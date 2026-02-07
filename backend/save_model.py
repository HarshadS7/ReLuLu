import yfinance as yf
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
import seaborn as sns
from gnn_model import SuperNodeGNN

# --- 1. MODEL DEFINITION ---

# --- 2. DATA PIPELINE ---
def get_systemic_data():
    banks = ['JPM', 'BAC', 'WFC', 'C', 'USB', 'GS', 'MS']
    macro = ['^TNX'] # 10-Year Treasury Yield
    all_data = yf.download(banks + macro, period="2y")['Close']
    returns = np.log(all_data / all_data.shift(1)).dropna()
    return returns[banks], returns[macro], banks

def create_windows(bank_rets, macro_rets, window_size=10):
    x, y = [], []
    for i in range(len(bank_rets) - window_size):
        b_win = bank_rets.iloc[i : i + window_size].values.T
        m_win = macro_rets.iloc[i : i + window_size].values.T
        m_broadcast = np.tile(m_win, (b_win.shape[0], 1))
        x.append(np.stack([b_win, m_broadcast], axis=-1))
        y.append(bank_rets.iloc[i + window_size].values)
    return torch.tensor(np.array(x), dtype=torch.float), torch.tensor(np.array(y), dtype=torch.float)

# --- 3. STABILITY DASHBOARD (TIER 3) ---
def launch_dashboard(tickers, predictions, adj_matrix):
    plt.figure(figsize=(15, 6))
    
    # Heatmap: Inter-bank Exposure (Spatial Risk)
    plt.subplot(1, 2, 1)
    sns.heatmap(adj_matrix, xticklabels=tickers, yticklabels=tickers, cmap="YlOrRd", annot=True, cbar=False)
    plt.title("Tier 3: Inter-Bank Exposure (Correlation Network)")
    
    # Bar Chart: Strategic Conviction (Signal Magnitude)
    plt.subplot(1, 2, 2)
    colors = ['#ff4d4d' if x < 0 else '#2ecc71' for x in predictions]
    plt.bar(tickers, predictions, color=colors)
    plt.axhline(0, color='black', linewidth=1)
    plt.title("Strategic Signal Conviction (Predicted Returns)")
    
    # Global Status
    avg_risk = np.mean(predictions)
    status = "🔴 SYSTEMIC STRESS" if avg_risk < -0.001 else "🟢 STABLE"
    plt.suptitle(f"ORCHESTRATOR STATUS: {status} | Network Risk Index: {avg_risk:.6f}", fontsize=16)
    plt.tight_layout()
    plt.show()

# --- 4. MAIN EXECUTION ---
if __name__ == "__main__":
    HIDDEN, LR, EPOCHS, THRESHOLD = 32, 0.001, 150, 0.7
    bank_rets, macro_rets, tickers = get_systemic_data()
    
    # Graph Construction
    corr = bank_rets.corr()
    edge_index = torch.tensor(np.array(np.nonzero((corr > THRESHOLD).values & ~np.eye(len(tickers), dtype=bool))), dtype=torch.long)
    
    x_win, y_tgt = create_windows(bank_rets, macro_rets)
    split = int(len(x_win) * 0.8)
    train_x, train_y = x_win[:split], y_tgt[:split]

  # Training
    model = SuperNodeGNN(node_features=2, hidden_dim=HIDDEN)
    optimizer = optim.Adam(model.parameters(), lr=LR)
    criterion = nn.MSELoss()

    # Determine a safe number of samples to train on based on data size
    num_samples = min(len(train_x), 200) 

    print(f"Orchestrator is learning systemic patterns on {num_samples} samples...")
    for epoch in range(EPOCHS):
        model.train()
        optimizer.zero_grad()
        
        # Ensure predictions and targets have the EXACT same count
        preds = torch.stack([model(train_x[i], edge_index) for i in range(num_samples)]).squeeze()
        loss = criterion(preds, train_y[:num_samples]) 
        
        loss.backward()
        optimizer.step()
        
        if (epoch+1) % 25 == 0: 
            print(f"Epoch {epoch+1} | Loss: {loss.item():.7f}")

    # Inference & Decision Logic
    model.eval()
    with torch.no_grad():
        latest_pred = model(x_win[-1], edge_index).squeeze().numpy()

    print("\n--- TIER 2 STRATEGIC DECISIONS ---")
    for i, ticker in enumerate(tickers):
        score = latest_pred[i]
        # LOWERED THRESHOLD TO 0.001 (0.1%) TO TRIGGER SIGNALS
        if score < -0.001:
            decision = f"🔴 PENALTY | Increase Margin by {abs(score)*1000:.2f}%"
        elif score > 0.001:
            decision = f"🟢 REWARD  | Lower Collateral by {score*500:.2f}%"
        else:
            decision = f"⚪ NEUTRAL | No Policy Change"
        print(f"{ticker:<5}: {decision}")

    # Launch Dashboard
    launch_dashboard(tickers, latest_pred, corr.values)
    torch.save(model.state_dict(), 'super_node_v1.pth')