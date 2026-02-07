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

from data.constants import BANK_TICKERS, MACRO_TICKERS, CORRELATION_THRESHOLD


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


# --------------- quick test ---------------
if __name__ == "__main__":
    loader = TimeSeriesLoader(period="1y").load()
    x, y = loader.get_windows()
    print(f"x_windows : {x.shape}")
    print(f"y_targets : {y.shape}")
    print(f"edge_index: {loader.edge_index.shape}")
    print(f"metadata  : {loader.get_metadata()}")
