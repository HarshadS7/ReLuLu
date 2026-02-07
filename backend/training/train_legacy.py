"""
Legacy SuperNodeGNN trainer.

Originally save_model.py — trains the static GCN → LSTM → Linear model
on 2-year market data.

Usage:
    cd backend
    python -m training.train_legacy
"""

import os
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from data.loader import TimeSeriesLoader
from data.constants import BANK_TICKERS, CORRELATION_THRESHOLD
from models.super_node_gnn import SuperNodeGNN


def train(
    period: str = "2y",
    hidden_dim: int = 32,
    lr: float = 0.001,
    epochs: int = 150,
    save_path: str | None = None,
):
    if save_path is None:
        save_path = os.path.join(BACKEND_DIR, "super_node_v1.pth")

    # 1. Data ----------------------------------------------------------
    loader = TimeSeriesLoader(period=period).load()
    x_all, y_all = loader.get_windows()
    edge_index = loader.edge_index
    tickers = loader.bank_tickers

    split = int(len(x_all) * 0.8)
    train_x, train_y = x_all[:split], y_all[:split]
    num_samples = min(len(train_x), 200)

    # 2. Model ---------------------------------------------------------
    model = SuperNodeGNN(node_features=2, hidden_dim=hidden_dim)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    print(f"[Legacy Train] {num_samples} samples, {epochs} epochs …")

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()

        preds = torch.stack(
            [model(train_x[i], edge_index) for i in range(num_samples)]
        ).squeeze()

        loss = criterion(preds, train_y[:num_samples])
        loss.backward()
        optimizer.step()

        if epoch % 25 == 0 or epoch == 1:
            print(f"  Epoch {epoch:>4d} | loss={loss.item():.7f}")

    torch.save(model.state_dict(), save_path)
    print(f"[Legacy Train] Model saved → {save_path}")

    # Quick inference
    model.eval()
    with torch.no_grad():
        latest_pred = model(x_all[-1], edge_index).squeeze().numpy()

    print("\n  Latest predictions:")
    for i, t in enumerate(tickers):
        print(f"    {t}: {latest_pred[i]:.6f}")


if __name__ == "__main__":
    train()
