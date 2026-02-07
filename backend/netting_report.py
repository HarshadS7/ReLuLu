import torch
import numpy as np
import pandas as pd
from save_model import get_systemic_data

# --- 1. CONFIGURATION & MARKET CAPS ---
# Estimated Market Caps (in Billions USD) for scaling
MARKET_CAPS = {
    'JPM': 580, 'BAC': 300, 'WFC': 210, 
    'C': 110, 'USB': 65, 'GS': 140, 'MS': 150
}

def calculate_systemic_netting(tickers, predictions, corr_matrix):
    print("--- TIER 3: CAPITAL NETTING & COMPRESSION REPORT ---")
    print(f"{'Institution':<12} | {'Gross Risk (bn)':<15} | {'Netted Risk (bn)':<15}")
    print("-" * 50)
    
    total_gross = 0
    total_netted = 0
    
    for i, ticker in enumerate(tickers):
        mcap = MARKET_CAPS.get(ticker, 100)
        
        # Gross Risk: Potential loss based on prediction without graph context
        gross_risk_val = abs(predictions[i]) * mcap
        
        # Netted Risk: Risk adjusted by network coupling (Compression)
        # We use the mean correlation with others as a compression factor
        compression_factor = 1 - np.mean(corr_matrix[i]) 
        netted_risk_val = gross_risk_val * compression_factor
        
        total_gross += gross_risk_val
        total_netted += netted_risk_val
        
        print(f"{ticker:<12} | ${gross_risk_val:>13.2f} | ${netted_risk_val:>14.2f}")
    
    compression_gain = total_gross - total_netted
    efficiency = (compression_gain / total_gross) * 100
    
    print("-" * 50)
    print(f"TOTAL SYSTEMIC EXPOSURE (GROSS): ${total_gross:.2f} Billion")
    print(f"TOTAL COMPRESSED PAYLOAD (NET):  ${total_netted:.2f} Billion")
    print(f"CAPITAL EFFICIENCY GAINED:       {efficiency:.2f}%")
    print(f"\n[Tier 3 Outcome]: Release ${compression_gain:.2f}bn to Mutualized Default Fund.")

if __name__ == "__main__":
    # 1. Load context
    bank_rets, _, tickers = get_systemic_data()
    corr = bank_rets.corr().values
    
    # 2. Simulate current state predictions (Using your latest Reward values)
    # Using approx values from your last run: ~0.007 avg
    mock_preds = np.random.uniform(0.006, 0.009, size=len(tickers))
    
    # 3. Generate Report
    calculate_systemic_netting(tickers, mock_preds, corr)