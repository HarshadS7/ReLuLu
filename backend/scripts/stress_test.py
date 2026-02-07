"""
Stress test — simulates a bank-specific crash and measures contagion.

Usage:
    cd backend
    python -m scripts.stress_test
    python -m scripts.stress_test --bank GS --magnitude -0.10
"""

import os
import sys
import argparse
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from data.loader import TimeSeriesLoader
from data.constants import BANK_TICKERS, CORRELATION_THRESHOLD
from models.super_node_gnn import SuperNodeGNN


MODEL_PATH = os.path.join(BACKEND_DIR, "super_node_v1.pth")


def load_model(hidden_dim: int = 32) -> SuperNodeGNN:
    model = SuperNodeGNN(node_features=2, hidden_dim=hidden_dim)
    model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    model.eval()
    print(f"✅ Model loaded from {MODEL_PATH}")
    return model


def run_stress(
    model: SuperNodeGNN,
    loader: TimeSeriesLoader,
    target_bank: str = "JPM",
    crash_magnitude: float = -0.08,
):
    """Inject a crash into one bank's recent returns and re-run inference."""
    print(f"\n⚠️  SIMULATING CRASH on {target_bank} ({crash_magnitude*100:.0f}% move) …")

    x_all, _ = loader.get_windows()
    latest = x_all[-1].clone()  # [N, T, F]
    edge_index = loader.edge_index

    idx = BANK_TICKERS.index(target_bank)
    latest[idx, -5:, 0] = crash_magnitude

    with torch.no_grad():
        preds = model(latest, edge_index).squeeze().numpy()

    corr_vals = loader.bank_returns.corr().values
    return preds, corr_vals


def plot_contagion(tickers, preds, corr_matrix):
    plt.figure(figsize=(15, 6))

    plt.subplot(1, 2, 1)
    sns.heatmap(corr_matrix, xticklabels=tickers, yticklabels=tickers,
                cmap="Reds", annot=True)
    plt.title("Contagion Path (Inter-bank Exposure)")

    plt.subplot(1, 2, 2)
    colors = ["#d32f2f" if x < 0 else "#388e3c" for x in preds]
    plt.bar(tickers, preds, color=colors)
    plt.axhline(0, color="black", linewidth=1)
    plt.title("Systemic Response to Simulated Stress")

    avg = np.mean(preds)
    status = "CRITICAL" if avg < -0.0005 else "RESILIENT"
    plt.suptitle(f"STRESS TEST: {status} | Index: {avg:.6f}",
                 fontsize=16, color="darkred")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a bank stress test")
    parser.add_argument("--bank", default="JPM", choices=BANK_TICKERS)
    parser.add_argument("--magnitude", type=float, default=-0.08)
    args = parser.parse_args()

    loader = TimeSeriesLoader(period="2y").load()
    model = load_model()
    preds, corr = run_stress(model, loader, args.bank, args.magnitude)
    plot_contagion(BANK_TICKERS, preds, corr)
