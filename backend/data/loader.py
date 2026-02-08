"""
Time-Series Data Loader
========================
Fetches live market data via yfinance and produces rolling-window tensors
that the Temporal GNN consumes for multi-horizon forecasting.

Outputs:
  x_windows : [num_windows, num_nodes, seq_len, num_features]
  y_targets  : [num_windows, num_nodes]
  edge_index : [2, num_edges]  (correlation-based graph)
  metadata   : dict with timestamps, tickers, correlation matrix
"""

import torch
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

from data.constants import (
    BANK_TICKERS,
    MACRO_TICKERS,
    CORRELATION_THRESHOLD,
    RISK_FACTOR_WINDOW_DAYS,
    RISK_EWMA_LAMBDA,
    RISK_DOWNSIDE_WEIGHT,
    ANOMALY_Z_THRESHOLD,
    ANOMALY_LOOKBACK_DAYS,
    ANOMALY_RECENT_DAYS,
)


class TimeSeriesLoader:
    """Loads real market data and yields rolling-window graph snapshots."""

    def __init__(
        self,
        bank_tickers: list[str] = BANK_TICKERS,
        macro_tickers: list[str] = MACRO_TICKERS,
        period: str = "2y",
        window_size: int = 10,
        correlation_threshold: float = CORRELATION_THRESHOLD,
    ):
        self.bank_tickers = bank_tickers
        self.macro_tickers = macro_tickers
        self.period = period
        self.window_size = window_size
        self.corr_threshold = correlation_threshold

        # Populated by .load()
        self.bank_returns: pd.DataFrame | None = None
        self.macro_returns: pd.DataFrame | None = None
        self.timestamps: list[str] = []
        self.corr_matrix: np.ndarray | None = None
        self.edge_index: torch.Tensor | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load(self) -> "TimeSeriesLoader":
        """Download data and build the correlation graph.  Returns self."""
        print(f"[DataLoader] Downloading {self.period} of market data …")
        all_tickers = self.bank_tickers + self.macro_tickers
        raw = yf.download(all_tickers, period=self.period)["Close"]
        raw = raw.dropna()

        # Log returns
        log_ret = np.log(raw / raw.shift(1)).dropna()
        self.bank_returns = log_ret[self.bank_tickers]
        self.macro_returns = log_ret[self.macro_tickers]
        self.timestamps = [str(d.date()) for d in self.bank_returns.index]

        # Correlation-based graph
        corr = self.bank_returns.corr()
        self.corr_matrix = corr.values
        mask = (corr.values > self.corr_threshold) & (
            ~np.eye(len(self.bank_tickers), dtype=bool)
        )
        self.edge_index = torch.tensor(np.array(np.nonzero(mask)), dtype=torch.long)
        print(
            f"[DataLoader] {len(self.bank_returns)} trading days, "
            f"{self.edge_index.shape[1]} edges (threshold={self.corr_threshold})"
        )
        return self

    def get_windows(self) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Build rolling windows from the loaded data.

        Returns
        -------
        x_windows : Tensor [num_windows, num_nodes, seq_len, 2]
            Feature 0 = bank log-return, Feature 1 = macro (^TNX) log-return.
        y_targets : Tensor [num_windows, num_nodes]
            Next-day bank log-returns (prediction target).
        """
        assert self.bank_returns is not None, "Call .load() first"
        bank_vals = self.bank_returns.values  # [T, N]
        macro_vals = self.macro_returns.values  # [T, 1]

        xs, ys = [], []
        for i in range(len(bank_vals) - self.window_size):
            b_win = bank_vals[i : i + self.window_size].T  # [N, W]
            m_win = macro_vals[i : i + self.window_size].T  # [1, W]
            m_broad = np.tile(m_win, (b_win.shape[0], 1))  # [N, W]
            xs.append(np.stack([b_win, m_broad], axis=-1))  # [N, W, 2]
            ys.append(bank_vals[i + self.window_size])  # [N]

        x_windows = torch.tensor(np.array(xs), dtype=torch.float32)
        y_targets = torch.tensor(np.array(ys), dtype=torch.float32)
        return x_windows, y_targets

    def get_latest_window(self) -> torch.Tensor:
        """Return the most-recent window for live inference.  Shape [N, W, 2]."""
        x_all, _ = self.get_windows()
        return x_all[-1]  # [N, W, 2]

    def get_recent_windows(self, n: int = 5) -> torch.Tensor:
        """Return the last *n* windows for multi-horizon forecasting.
        Shape [n, N, W, 2]."""
        x_all, _ = self.get_windows()
        return x_all[-n:]

    def get_metadata(self) -> dict:
        return {
            "tickers": self.bank_tickers,
            "num_banks": len(self.bank_tickers),
            "window_size": self.window_size,
            "correlation_matrix": self.corr_matrix.tolist() if self.corr_matrix is not None else [],
            "total_days": len(self.timestamps),
            "date_range": (self.timestamps[0], self.timestamps[-1]) if self.timestamps else ("", ""),
            "last_updated": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Convenience: build base obligations from recent returns
    # ------------------------------------------------------------------
    def build_base_obligations(self, scale: float = 10.0) -> torch.Tensor:
        """Derive an *asymmetric* obligations matrix.

        Real interbank obligations are directional — A may owe B far more
        than B owes A.  We model this by combining correlation strength
        (how linked the banks are) with a directional component derived
        from recent return volatility (higher-vol banks tend to be net
        payers of margin).  The result is a non-symmetric matrix that
        prevents netting from collapsing to ~100%.
        """
        n = len(self.bank_tickers)
        if self.corr_matrix is None or self.bank_returns is None:
            obl = torch.abs(torch.randn(n, n)) * scale
            obl.fill_diagonal_(0)
            return obl

        # Correlation gives magnitude of bilateral exposure
        corr_abs = np.abs(self.corr_matrix)

        # Directional component: recent 20-day mean return & volatility
        recent = self.bank_returns.iloc[-20:]
        vol = recent.std().values          # [N]
        mu  = recent.mean().values         # [N]

        # Payer weight: banks with negative mean or high vol pay more
        payer_w  = np.abs(mu) + vol        # [N]
        payer_w  = payer_w / (payer_w.sum() + 1e-8)

        # obl[i,j] = corr_strength * payer_weight_i * receiver_weight_j
        # receiver_weight is just 1/N + noise to keep it asymmetric
        rng = np.random.RandomState(42)
        recv_w = np.ones(n) / n + rng.uniform(0, 0.05, size=n)

        obl = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                obl[i, j] = corr_abs[i, j] * payer_w[i] * recv_w[j] * scale * n

        # Add small random jitter to guarantee asymmetry
        obl += rng.uniform(0.1, 0.5, size=(n, n))
        np.fill_diagonal(obl, 0)

        return torch.tensor(obl, dtype=torch.float32)

    def build_liquidity(self) -> torch.Tensor:
        """Heuristic liquidity from recent volatility (lower vol → more cash)."""
        if self.bank_returns is None:
            return torch.abs(torch.randn(len(self.bank_tickers))) * 100 + 50
        vol = self.bank_returns.iloc[-20:].std().values  # 20-day vol
        # Invert: low-vol banks → higher liquidity
        liq = 1.0 / (vol + 1e-8)
        liq = liq / liq.max() * 100 + 50  # normalise into ~[50, 150]
        return torch.tensor(liq, dtype=torch.float32)

    def build_time_series_risk_factor(
        self,
        window_days: int = RISK_FACTOR_WINDOW_DAYS,
        ewma_lambda: float = RISK_EWMA_LAMBDA,
        downside_weight: float = RISK_DOWNSIDE_WEIGHT,
    ) -> torch.Tensor:
        """Per-bank risk factor in [0,1] derived purely from time-series returns.

        Definition (default): mixture of EWMA volatility and downside magnitude.
        - EWMA volatility captures "how unstable is it lately"
        - Downside captures "how negative are recent returns"

        Returns
        -------
        Tensor [N] with values in [0, 1]. Higher = riskier.
        """
        n = len(self.bank_tickers)
        if self.bank_returns is None or len(self.bank_returns) == 0:
            rf = torch.rand(n)
            return torch.clamp(rf, 0.0, 1.0)

        r = self.bank_returns.iloc[-window_days:].values  # [T, N]
        if r.shape[0] < 2:
            return torch.zeros(n, dtype=torch.float32)

        # EWMA volatility (RiskMetrics-style)
        lam = float(np.clip(ewma_lambda, 0.0, 0.9999))
        w = (1.0 - lam) * (lam ** np.arange(r.shape[0] - 1, -1, -1))  # [T]
        w = w / (w.sum() + 1e-12)
        ewma_var = (w[:, None] * (r ** 2)).sum(axis=0)  # [N]
        ewma_vol = np.sqrt(np.maximum(ewma_var, 0.0))

        # Downside magnitude (average negative return size)
        downside = np.maximum(-r, 0.0).mean(axis=0)  # [N]

        def _norm01(x: np.ndarray) -> np.ndarray:
            x = np.asarray(x, dtype=float)
            denom = np.max(x)
            if not np.isfinite(denom) or denom <= 1e-12:
                return np.zeros_like(x)
            return np.clip(x / denom, 0.0, 1.0)

        vol_n = _norm01(ewma_vol)
        down_n = _norm01(downside)

        a = float(np.clip(downside_weight, 0.0, 1.0))
        risk = (1.0 - a) * vol_n + a * down_n
        return torch.tensor(risk, dtype=torch.float32)

    # ------------------------------------------------------------------
    # Anomaly detection on time-series returns
    # ------------------------------------------------------------------
    def detect_anomalies(
        self,
        lookback_days: int = ANOMALY_LOOKBACK_DAYS,
        recent_days: int = ANOMALY_RECENT_DAYS,
        z_threshold: float = ANOMALY_Z_THRESHOLD,
    ) -> list[dict]:
        """Flag banks whose recent returns spike beyond z_threshold σ.

        Returns a list of dicts, one per anomaly detected:
          { "bank", "date", "return", "z_score", "direction" }
        Empty list if no anomalies.
        """
        if self.bank_returns is None or len(self.bank_returns) < lookback_days:
            return []

        window = self.bank_returns.iloc[-lookback_days:]
        mu = window.mean()                # [N]
        sigma = window.std()              # [N]

        recent = self.bank_returns.iloc[-recent_days:]
        anomalies = []
        for ticker in self.bank_tickers:
            s = sigma[ticker]
            m = mu[ticker]
            if s < 1e-12:
                continue
            for date_idx, ret_val in recent[ticker].items():
                z = (ret_val - m) / s
                if abs(z) >= z_threshold:
                    anomalies.append({
                        "bank": ticker,
                        "date": str(date_idx.date()) if hasattr(date_idx, "date") else str(date_idx),
                        "return": float(ret_val),
                        "z_score": round(float(z), 3),
                        "direction": "SPIKE UP" if z > 0 else "SPIKE DOWN",
                    })
        return anomalies


# --------------- quick test ---------------
if __name__ == "__main__":
    loader = TimeSeriesLoader(period="1y").load()
    x, y = loader.get_windows()
    print(f"x_windows : {x.shape}")
    print(f"y_targets : {y.shape}")
    print(f"edge_index: {loader.edge_index.shape}")
    print(f"metadata  : {loader.get_metadata()}")
