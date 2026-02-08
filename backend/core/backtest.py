"""
Backtesting Engine
==================
Compares historical forecasts with actual outcomes to measure model accuracy.
"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import os

# Simple file-based storage for backtest results
BACKTEST_STORAGE_PATH = os.path.join(os.path.dirname(__file__), "..", "backtest_history.json")


class BacktestEngine:
    """Engine for backtesting model predictions against actual outcomes."""

    def __init__(self, loader):
        """
        Initialize the backtest engine.
        
        Args:
            loader: TimeSeriesLoader instance with historical data
        """
        self.loader = loader
        self.history: List[Dict] = self._load_history()

    def _load_history(self) -> List[Dict]:
        """Load backtest history from file."""
        if os.path.exists(BACKTEST_STORAGE_PATH):
            try:
                with open(BACKTEST_STORAGE_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        """Save backtest history to file."""
        try:
            with open(BACKTEST_STORAGE_PATH, "w") as f:
                json.dump(self.history[-100:], f, indent=2)  # Keep last 100 results
        except Exception as e:
            print(f"[Backtest] Failed to save history: {e}")

    def store_prediction(self, horizon: int, predictions: Dict[str, float], timestamp: Optional[str] = None):
        """
        Store a prediction for later comparison.
        
        Args:
            horizon: Forecast horizon (T+1, T+2, etc.)
            predictions: Dict mapping ticker -> predicted score
            timestamp: ISO timestamp of prediction (default: now)
        """
        entry = {
            "timestamp": timestamp or datetime.now().isoformat(),
            "horizon": horizon,
            "predictions": predictions,
            "actual": None,  # To be filled when outcome is known
            "metrics": None,
        }
        self.history.append(entry)
        self._save_history()

    def update_actuals(self, target_date: str, actuals: Dict[str, float]):
        """
        Update stored predictions with actual outcomes.
        
        Args:
            target_date: Date (ISO format) for which to update actuals
            actuals: Dict mapping ticker -> actual return
        """
        for entry in self.history:
            if entry["actual"] is None:
                entry["actual"] = actuals
                entry["metrics"] = self._compute_metrics(entry["predictions"], actuals)
                self._save_history()
                break

    def _compute_metrics(self, predictions: Dict[str, float], actuals: Dict[str, float]) -> Dict[str, float]:
        """
        Compute accuracy metrics comparing predictions to actuals.
        
        Returns:
            Dict with MAE, directional accuracy, and correlation
        """
        common_tickers = set(predictions.keys()) & set(actuals.keys())
        if not common_tickers:
            return {"mae": None, "directional_accuracy": None, "correlation": None}

        pred_vals = np.array([predictions[t] for t in common_tickers])
        actual_vals = np.array([actuals[t] for t in common_tickers])

        # Mean Absolute Error
        mae = float(np.mean(np.abs(pred_vals - actual_vals)))

        # Directional Accuracy (did we predict the sign correctly?)
        pred_signs = np.sign(pred_vals)
        actual_signs = np.sign(actual_vals)
        directional_acc = float(np.mean(pred_signs == actual_signs))

        # Correlation
        if np.std(pred_vals) > 0 and np.std(actual_vals) > 0:
            correlation = float(np.corrcoef(pred_vals, actual_vals)[0, 1])
        else:
            correlation = 0.0

        return {
            "mae": round(mae, 6),
            "directional_accuracy": round(directional_acc, 4),
            "correlation": round(correlation, 4),
        }

    def run_backtest(self, lookback_days: int = 30) -> Dict[str, Any]:
        """
        Run a backtest using historical data.
        
        Uses the loader's window data to simulate past predictions
        and compare against actual outcomes.
        
        Args:
            lookback_days: Number of days to backtest
        
        Returns:
            Dict with overall metrics and per-day results
        """
        if self.loader.bank_returns is None:
            return {"error": "No data loaded", "results": []}

        returns = self.loader.bank_returns
        tickers = self.loader.bank_tickers
        n_days = min(lookback_days, len(returns) - 1)

        results = []
        all_mae = []
        all_dir_acc = []

        for i in range(n_days, 0, -1):
            # Use returns from day -i-1 as "prediction" proxy (lag correlation)
            if i + 1 >= len(returns):
                continue

            pred_day = returns.iloc[-(i + 1)]
            actual_day = returns.iloc[-i]

            predictions = {t: float(pred_day[t]) for t in tickers}
            actuals = {t: float(actual_day[t]) for t in tickers}

            metrics = self._compute_metrics(predictions, actuals)
            
            results.append({
                "date": str(returns.index[-i].date()) if hasattr(returns.index[-i], "date") else str(returns.index[-i]),
                "predictions": predictions,
                "actuals": actuals,
                "metrics": metrics,
            })

            if metrics["mae"] is not None:
                all_mae.append(metrics["mae"])
            if metrics["directional_accuracy"] is not None:
                all_dir_acc.append(metrics["directional_accuracy"])

        # Aggregate metrics
        aggregate = {
            "total_days": len(results),
            "avg_mae": round(float(np.mean(all_mae)), 6) if all_mae else None,
            "avg_directional_accuracy": round(float(np.mean(all_dir_acc)), 4) if all_dir_acc else None,
            "best_day": max(results, key=lambda x: x["metrics"]["directional_accuracy"] or 0)["date"] if results else None,
            "worst_day": min(results, key=lambda x: x["metrics"]["directional_accuracy"] or 1)["date"] if results else None,
        }

        return {
            "aggregate": aggregate,
            "results": results[:10],  # Return only last 10 days for brevity
            "timestamp": datetime.now().isoformat(),
        }

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent backtest history entries."""
        return self.history[-limit:]
