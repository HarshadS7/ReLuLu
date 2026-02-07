"""
Test script to verify the FinancialOptimizationEngine integration.
"""
import torch
import numpy as np
from engine import FinancialOptimizationEngine

# --- Configuration ---
NUM_BANKS = 7  # Same as save_model.py (JPM, BAC, WFC, C, USB, GS, MS)
SEQ_LEN = 10   # Window size used in training
NODE_FEATURES = 2
HIDDEN_DIM = 32
MODEL_PATH = "super_node_v1.pth"

def main():
    print("=" * 50)
    print("FINANCIAL OPTIMIZATION ENGINE TEST")
    print("=" * 50)

    # 1. Load the trained GNN model
    print("\n[1] Loading trained GNN model...")
    try:
        model = FinancialOptimizationEngine.load_gnn_model(
            MODEL_PATH, 
            node_features=NODE_FEATURES, 
            hidden_dim=HIDDEN_DIM
        )
        print(f"    ✓ Model loaded from {MODEL_PATH}")
    except FileNotFoundError:
        print(f"    ✗ Model file not found: {MODEL_PATH}")
        print("    Run save_model.py first to train and save the model.")
        return

    # 2. Initialize the engine
    print("\n[2] Initializing FinancialOptimizationEngine...")
    engine = FinancialOptimizationEngine(model)
    print("    ✓ Engine initialized")

    # 3. Create synthetic test data (simulating GNN input)
    print("\n[3] Creating test data...")
    
    # x_window: [num_nodes, seq_len, node_features]
    # Simulates bank returns + macro features over a time window
    x_window = torch.randn(NUM_BANKS, SEQ_LEN, NODE_FEATURES)
    
    # edge_index: [2, num_edges] - connectivity based on correlation threshold
    # Creating a sample connected graph (ring + some cross connections)
    edges = []
    for i in range(NUM_BANKS):
        edges.append([i, (i + 1) % NUM_BANKS])
        edges.append([(i + 1) % NUM_BANKS, i])
        if i < NUM_BANKS - 2:
            edges.append([i, i + 2])
            edges.append([i + 2, i])
    edge_index = torch.tensor(edges, dtype=torch.long).T
    
    # liquidity_tensor: Cash on hand for each bank
    liquidity_tensor = torch.abs(torch.randn(NUM_BANKS)) * 100 + 50
    
    # base_obligations: Optional starting obligations matrix
    base_obligations = torch.abs(torch.randn(NUM_BANKS, NUM_BANKS)) * 10
    base_obligations.fill_diagonal_(0)
    
    print(f"    ✓ x_window shape: {x_window.shape}")
    print(f"    ✓ edge_index shape: {edge_index.shape}")
    print(f"    ✓ liquidity_tensor shape: {liquidity_tensor.shape}")
    print(f"    ✓ base_obligations shape: {base_obligations.shape}")

    # 4. Run the optimization pipeline
    print("\n[4] Running optimization pipeline...")
    print("-" * 50)
    
    results = engine.run_pipeline(
        x_window=x_window,
        edge_index=edge_index,
        liquidity_tensor=liquidity_tensor,
        base_obligations=base_obligations
    )
    
    print("-" * 50)

    # 5. Display results
    print("\n[5] Results Summary:")
    print(f"    • Obligations to CCP shape: {results['obligations_to_ccp'].shape}")
    print(f"    • Systemic Hub Scores: {np.round(results['systemic_hubs'], 4)}")
    print(f"    • Stability Index: {results['stability']:.4f}")
    print(f"    • Predicted Node Scores: {np.round(results['predicted_node_scores'], 6)}")
    
    # 6. Interpret stability
    print("\n[6] System Status:")
    if results['stability'] < 1.0:
        print("    🟢 STABLE - Shocks will dissipate naturally")
    else:
        print("    🔴 UNSTABLE - Cascading failure risk detected")
    
    # 7. Show top systemic hubs
    hub_ranking = np.argsort(results['systemic_hubs'])[::-1]
    bank_names = ['JPM', 'BAC', 'WFC', 'C', 'USB', 'GS', 'MS']
    print("\n[7] Systemic Hub Ranking (highest risk first):")
    for rank, idx in enumerate(hub_ranking, 1):
        print(f"    {rank}. {bank_names[idx]}: {results['systemic_hubs'][idx]:.4f}")

    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
