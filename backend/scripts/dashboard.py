"""
Matplotlib stability dashboard (legacy visualization).

Usage:
    cd backend
    python -m scripts.dashboard
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def launch_stability_dashboard(tickers, predictions, adj_matrix):
    plt.figure(figsize=(14, 6))

    plt.subplot(1, 2, 1)
    sns.heatmap(adj_matrix, xticklabels=tickers, yticklabels=tickers, cmap="YlOrRd")
    plt.title("Tier 3: Inter-Bank Exposure Map")

    plt.subplot(1, 2, 2)
    colors = ["red" if x < 0 else "green" for x in predictions]
    plt.bar(tickers, predictions, color=colors)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("Strategic Signal Conviction")

    score = np.mean(predictions)
    status = "STABLE" if score > -0.002 else "WARNING: SYSTEMIC STRESS"
    plt.suptitle(f"SYSTEM STATUS: {status} | Risk Index: {score:.5f}")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    from data.constants import BANK_TICKERS  # noqa: E402
    mock = np.random.uniform(-0.005, 0.01, size=len(BANK_TICKERS))
    corr = np.random.rand(len(BANK_TICKERS), len(BANK_TICKERS))
    launch_stability_dashboard(BANK_TICKERS, mock, corr)
