import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def launch_stability_dashboard(tickers, predictions, adj_matrix):
    plt.figure(figsize=(14, 6))
    
    # 1. Systemic Risk Heatmap (Spatial)
    plt.subplot(1, 2, 1)
    sns.heatmap(adj_matrix, xticklabels=tickers, yticklabels=tickers, cmap="YlOrRd")
    plt.title("Tier 3: Inter-Bank Exposure Map")
    
    # 2. Predicted Strategic Signal Distribution
    plt.subplot(1, 2, 2)
    colors = ['red' if x < 0 else 'green' for x in predictions]
    plt.bar(tickers, predictions, color=colors)
    plt.axhline(0, color='black', linewidth=0.8)
    plt.title("Strategic Signal Conviction")
    
    # Calculate Total Systemic Risk Score
    systemic_score = np.mean(predictions)
    status = "STABLE" if systemic_score > -0.002 else "WARNING: SYSTEMIC STRESS"
    
    plt.suptitle(f"SYSTEM STATUS: {status} | Global Risk Index: {systemic_score:.5f}")
    plt.tight_layout()
    plt.show()

# Run this inside your main block after predictions
# launch_stability_dashboard(tickers, prediction.numpy(), corr.values)