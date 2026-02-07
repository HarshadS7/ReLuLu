"""
Standalone engine integration test (uses synthetic data).

Usage:
    cd backend
    python -m scripts.test_engine
"""

import os
import sys
import torch
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from data.constants import BANK_TICKERS
from models.super_node_gnn import SuperNodeGNN
from core.optimize import OptimizationNode

NUM_BANKS = 7
SEQ_LEN = 10
MODEL_PATH = os.path.join(BACKEND_DIR, "super_node_v1.pth")


def main():
    print("=" * 50)
    print("FINANCIAL OPTIMIZATION ENGINE TEST")
    print("=" * 50)

    # 1. Load model
    print("\n[1] Loading trained GNN …")
    model = SuperNodeGNN(node_features=2, hidden_dim=32)
    try:
        model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
        model.eval()
        print(f"    ✓ Loaded {MODEL_PATH}")
    except FileNotFoundError:
        print(f"    ✗ {MODEL_PATH} not found — run training first.")
        return

    # 2. Synthetic data
    print("\n[2] Creating synthetic test data …")
    x_window = torch.randn(NUM_BANKS, SEQ_LEN, 2)
    edges = []
    for i in range(NUM_BANKS):
        edges.append([i, (i + 1) % NUM_BANKS])
        edges.append([(i + 1) % NUM_BANKS, i])
    edge_index = torch.tensor(edges, dtype=torch.long).T

    # 3. GNN inference
    print("\n[3] Running GNN inference …")
    with torch.no_grad():
        scores = model(x_window, edge_index).squeeze().numpy()
    print(f"    Scores: {np.round(scores, 6)}")

    # 4. Optimization
    print("\n[4] Running optimization …")
    obligations = torch.abs(torch.randn(NUM_BANKS, NUM_BANKS)) * 10
    obligations.fill_diagonal_(0)

    node = OptimizationNode(np.eye(NUM_BANKS))  # dummy risk matrix
    hub_scores, stability = node.get_systemic_hubs()
    opt_matrix, raw, net, _ = node.minimize_payload(obligations)
    reduction = ((raw - net) / raw) * 100 if raw > 0 else 0

    print(f"    Stability: {stability:.4f}")
    print(f"    Payload:   ${raw:.2f}M → ${net:.2f}M ({reduction:.1f}% reduction)")
    print(f"    Hub ranking: {np.round(hub_scores, 4)}")

    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    main()
