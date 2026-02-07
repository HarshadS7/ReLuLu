"""
Forecast Engine
================
Wraps TemporalGNN / SuperNodeGNN behind a unified interface.

Pipeline per horizon:
  1. GNN inference → node scores
  2. Build obligations from scores
  3. Risk Jacobian → hub detection
  4. Circular netting → payload reduction
"""

import os
import torch
import numpy as np

from data.loader import TimeSeriesLoader
from models import TemporalGNN, SuperNodeGNN
from core.optimize import OptimizationNode


class ForecastEngine:
    """High-level driver consumed by the API layer."""

    HORIZONS = 5  # must match TemporalGNN.num_horizons

    def __init__(
        self,
        model: TemporalGNN | SuperNodeGNN,
        loader: TimeSeriesLoader,
        device: str | None = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.model.eval()
        self.loader = loader
        self.optimizer = OptimizationNode()
        self.is_temporal = isinstance(model, TemporalGNN)

    # ------------------------------------------------------------------
    # Model loading helpers
    # ------------------------------------------------------------------
    @staticmethod
    def load_temporal(
        path: str,
        node_features: int = 2,
        hidden_dim: int = 64,
        num_horizons: int = 5,
        device: str | None = None,
    ) -> TemporalGNN:
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        m = TemporalGNN(
            node_features=node_features,
            hidden_dim=hidden_dim,
            num_horizons=num_horizons,
        ).to(device)
        m.load_state_dict(torch.load(path, map_location=device))
        m.eval()
        return m

    @staticmethod
    def load_legacy(
        path: str,
        node_features: int = 2,
        hidden_dim: int = 32,
        device: str | None = None,
    ) -> SuperNodeGNN:
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        m = SuperNodeGNN(
            node_features=node_features, hidden_dim=hidden_dim
        ).to(device)
        m.load_state_dict(torch.load(path, map_location=device))
        m.eval()
        return m

    # ------------------------------------------------------------------
    # Per-horizon risk analysis
    # ------------------------------------------------------------------
    def _analyse_horizon(
        self,
        node_scores: torch.Tensor,
        liquidity: torch.Tensor,
        base_obligations: torch.Tensor,
    ) -> dict:
        """Run the full Jacobian → hubs → netting pipeline for one horizon."""
        pred_O = self._build_obligations(node_scores, base_obligations)

        risk_adj = self._risk_jacobian(pred_O, liquidity)
        hubs, stability = self.optimizer.get_systemic_hubs(risk_adj)

        netted, raw_load, net_load = self.optimizer.minimize_payload(pred_O, hubs)
        pct = ((raw_load - net_load) / raw_load * 100) if raw_load > 0 else 0.0

        return {
            "node_scores": node_scores.detach().cpu().numpy(),
            "obligations_before": pred_O.detach().cpu().numpy(),
            "obligations_after": netted,
            "systemic_hubs": hubs,
            "stability": float(stability),
            "payload_reduction": float(pct),
            "raw_load": float(raw_load),
            "net_load": float(net_load),
        }

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def run_forecast(self) -> dict:
        """
        Returns
        -------
        {
          "horizons": [ { …snapshot… }, … ],
          "metadata": { tickers, date_range, … },
        }
        """
        edge_index = self.loader.edge_index.to(self.device)
        liquidity = self.loader.build_liquidity().to(self.device)
        base_obl = self.loader.build_base_obligations().to(self.device)
        latest = self.loader.get_latest_window().to(self.device)  # [N, W, F]

        if self.is_temporal:
            with torch.no_grad():
                all_forecasts = self.model.forecast_single(latest, edge_index)

            horizons = []
            for k in range(all_forecasts.shape[0]):
                snap = self._analyse_horizon(all_forecasts[k], liquidity, base_obl)
                snap["horizon"] = k + 1
                horizons.append(snap)
        else:
            with torch.no_grad():
                scores = self.model(latest, edge_index).squeeze(-1)
            snap = self._analyse_horizon(scores, liquidity, base_obl)
            snap["horizon"] = 1
            horizons = [snap]

        return {
            "horizons": horizons,
            "metadata": self.loader.get_metadata(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_obligations(
        node_scores: torch.Tensor,
        base_obligations: torch.Tensor,
    ) -> torch.Tensor:
        """Scale obligations by predicted node stress (amplified 100×)."""
        base_obligations = base_obligations.to(node_scores.device)
        amplified = torch.clamp(node_scores * 100, min=-0.9, max=2.0)
        scale = 1 + amplified  # range [0.1 … 3.0]
        obligations = base_obligations * scale.unsqueeze(-1)
        obligations = torch.clamp(obligations, min=0)
        obligations.fill_diagonal_(0)
        return obligations

    @staticmethod
    def _risk_jacobian(
        pred_O: torch.Tensor, liquidity: torch.Tensor
    ) -> torch.Tensor:
        pred_O = pred_O.clone().detach().requires_grad_(True)
        liquidity = liquidity.clone().detach()

        def flow_score(O_input):
            inflow = torch.sum(O_input.T, dim=1)
            outflow = torch.sum(O_input, dim=1)
            net = (liquidity + inflow) - outflow
            scale = outflow.clamp(min=1.0)
            return torch.sigmoid(-net / scale)

        J = torch.autograd.functional.jacobian(flow_score, pred_O)
        return J.sum(dim=2)
