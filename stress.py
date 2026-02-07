import torch
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
# Ensure these imports match the filenames and class names in your directory
from ReLuLu.save_model import SuperNodeGNN, get_systemic_data, create_windows 

# --- 1. CONFIGURATION ---
MODEL_PATH = 'super_node_v1.pth'
TICKERS = ['JPM', 'BAC', 'WFC', 'C', 'USB', 'GS', 'MS']
HIDDEN_DIM = 32

def load_orchestrator():
    """Initializes the architecture and loads the saved weights."""
    model = SuperNodeGNN(node_features=2, hidden_dim=HIDDEN_DIM)
    try:
        model.load_state_dict(torch.load(MODEL_PATH))
        model.eval()
        print(f"✅ Successfully loaded weights from {MODEL_PATH}")
    except FileNotFoundError:
        print(f"❌ Error: {MODEL_PATH} not found. Please run your training script first.")
        return None
    return model

# --- 2. THE STRESS TEST ENGINE ---
def run_systemic_simulation(model, bank_rets, macro_rets, target_bank="JPM", crash_magnitude=-0.08):
    """Artificially modifies the input data to simulate a bank-specific crash."""
    print(f"\n⚠️  SIMULATING SYSTEMIC CRASH ON {target_bank} ({crash_magnitude*100}% move)...")
    
    # Prepare the graph data
    x_win, _ = create_windows(bank_rets, macro_rets)
    latest_state = x_win[-1].clone() # Shape: [Nodes, Window, Features]
    
    # Calculate edge_index (The Inter-bank coupling)
    corr = bank_rets.corr()
    edge_index = torch.tensor(np.array(np.nonzero((corr > 0.7).values & ~np.eye(len(TICKERS), dtype=bool))), dtype=torch.long)
    
    # Find index of target bank and inject the crash into its price returns (Feature 0)
    idx = TICKERS.index(target_bank)
    latest_state[idx, -5:, 0] = crash_magnitude # Simulate a multi-day selloff
    
    # Run Inference
    with torch.no_grad():
        impacted_preds = model(latest_state, edge_index).squeeze().numpy()
        
    return impacted_preds, corr.values

# --- 3. TIER 3 VISUALIZATION ---
def plot_contagion_report(tickers, preds, correlation_matrix):
    """Generates the Stability Dashboard for Tier 3 analysis."""
    plt.figure(figsize=(15, 6))
    
    # Heatmap: Contagion Path
    plt.subplot(1, 2, 1)
    sns.heatmap(correlation_matrix, xticklabels=tickers, yticklabels=tickers, cmap="Reds", annot=True)
    plt.title("Tier 3: Contagion Path (Inter-bank Exposure)")
    
    # Bar Chart: Systemic Response
    plt.subplot(1, 2, 2)
    colors = ['#d32f2f' if x < 0 else '#388e3c' for x in preds]
    plt.bar(tickers, preds, color=colors)
    plt.axhline(0, color='black', linewidth=1)
    plt.title("Strategic Signal Response to Simulated Stress")
    
    avg_risk = np.mean(preds)
    # Text-based status to avoid font/emoji issues on Mac
    status = "CRITICAL: SYSTEMIC STRESS" if avg_risk < -0.0005 else "RESILIENT"
    plt.suptitle(f"STRESS TEST RESULT: {status} | Systemic Index: {avg_risk:.6f}", fontsize=16, color='darkred')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # 1. Load Data and Model
    bank_rets, macro_rets, _ = get_systemic_data()
    orchestrator = load_orchestrator()
    
    if orchestrator:
        # 2. Run Simulation: Crash JPM to see if GS/MS (highly correlated) also drop
        impacted_results, corr_values = run_systemic_simulation(orchestrator, bank_rets, macro_rets, target_bank="JPM")
        
        # 3. Launch Stability Report
        plot_contagion_report(TICKERS, impacted_results, corr_values)