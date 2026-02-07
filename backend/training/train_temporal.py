"""
Temporal GNN trainer — multi-horizon prediction.

Usage:
    cd backend
    python -m training.train_temporal
    python -m training.train_temporal --epochs 300 --period 3y
"""

import os
import sys
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from data.loader import TimeSeriesLoader
from models.temporal_gnn import TemporalGNN


def build_multi_horizon_targets(
    y_all: torch.Tensor, num_horizons: int
) -> torch.Tensor:
    """
    From y_all [W, N] build targets [W - K + 1, K, N].
    y[i, k, :] = y_all[i + k] — the return k+1 steps ahead.
    """
    W, N = y_all.shape
    usable = W - num_horizons + 1
    targets = torch.zeros(usable, num_horizons, N)
    for k in range(num_horizons):
        targets[:, k, :] = y_all[k : k + usable]
    return targets


def train(
    period: str = "2y",
    epochs: int = 200,
    lr: float = 0.001,
    hidden_dim: int = 64,
    num_horizons: int = 5,
    save_path: str | None = None,
):
    if save_path is None:
        save_path = os.path.join(BACKEND_DIR, "temporal_gnn_v1.pth")

    # 1. Data ----------------------------------------------------------
    loader = TimeSeriesLoader(period=period).load()
    x_all, y_all = loader.get_windows()
    edge_index = loader.edge_index

    y_multi = build_multi_horizon_targets(y_all, num_horizons)
    usable = y_multi.shape[0]
    x_all = x_all[:usable]

    split = int(usable * 0.8)
    train_x, train_y = x_all[:split], y_multi[:split]
    val_x, val_y = x_all[split:], y_multi[split:]

    print(
        f"[Temporal Train] train={split}  val={usable - split}  "
        f"horizons={num_horizons}  features={x_all.shape}"
    )

    # 2. Model ---------------------------------------------------------
    model = TemporalGNN(
        node_features=2,
        hidden_dim=hidden_dim,
        num_horizons=num_horizons,
    )
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=15, verbose=True,
    )

    best_val = float("inf")
    patience_counter = 0
    num_train = min(len(train_x), 300)

    print(f"[Temporal Train] {num_train} samples/epoch for {epochs} epochs …\n")

    # 3. Training loop -------------------------------------------------
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()

        preds = torch.stack(
            [model.forecast_single(train_x[i], edge_index) for i in range(num_train)]
        )
        loss = criterion(preds, train_y[:num_train])
        loss.backward()
        optimizer.step()

        # Validation
        model.eval()
        with torch.no_grad():
            val_preds = torch.stack(
                [model.forecast_single(val_x[i], edge_index) for i in range(len(val_x))]
            )
            val_loss = criterion(val_preds, val_y).item()

        scheduler.step(val_loss)

        if val_loss < best_val:
            best_val = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), save_path)
        else:
            patience_counter += 1

        if epoch % 25 == 0 or epoch == 1:
            print(
                f"  Epoch {epoch:>4d} | train_loss={loss.item():.7f}  "
                f"val_loss={val_loss:.7f}  best={best_val:.7f}"
            )

        if patience_counter >= 30:
            print(f"\n  Early stopping at epoch {epoch}")
            break

    print(f"\n[Temporal Train] Best val loss: {best_val:.7f}")
    print(f"[Temporal Train] Model saved → {save_path}")

    # Quick forecast test
    model.load_state_dict(torch.load(save_path, weights_only=True))
    model.eval()
    with torch.no_grad():
        test_pred = model.forecast_single(x_all[-1], edge_index)
    tickers = loader.bank_tickers
    print(f"\n  Sample forecast (latest window):")
    for k in range(num_horizons):
        vals = ", ".join(f"{tickers[n]}={test_pred[k, n]:.5f}" for n in range(len(tickers)))
        print(f"    Horizon {k+1}: {vals}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the Temporal GNN")
    parser.add_argument("--period", default="2y", help="yfinance period (default 2y)")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--horizons", type=int, default=5)
    args = parser.parse_args()

    train(
        period=args.period,
        epochs=args.epochs,
        lr=args.lr,
        hidden_dim=args.hidden,
        num_horizons=args.horizons,
    )
