"""
Capital netting & compression report.

Usage:
    cd backend
    python -m scripts.netting_report
"""

import os
import sys
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from data.loader import TimeSeriesLoader
from data.constants import BANK_TICKERS, MARKET_CAPS


def calculate_systemic_netting(tickers, predictions, corr_matrix):
    print("--- TIER 3: CAPITAL NETTING & COMPRESSION REPORT ---")
    print(f"{'Institution':<12} | {'Gross Risk (bn)':<15} | {'Netted Risk (bn)':<15}")
    print("-" * 50)

    total_gross = 0
    total_netted = 0

    for i, ticker in enumerate(tickers):
        mcap = MARKET_CAPS.get(ticker, 100)
        gross = abs(predictions[i]) * mcap
        compression = 1 - np.mean(corr_matrix[i])
        netted = gross * compression

        total_gross += gross
        total_netted += netted
        print(f"{ticker:<12} | ${gross:>13.2f} | ${netted:>14.2f}")

    efficiency = ((total_gross - total_netted) / total_gross) * 100

    print("-" * 50)
    print(f"GROSS EXPOSURE:     ${total_gross:.2f} bn")
    print(f"COMPRESSED (NET):   ${total_netted:.2f} bn")
    print(f"CAPITAL SAVED:      {efficiency:.2f}%")
    print(f"Release ${total_gross - total_netted:.2f} bn to Mutualized Default Fund.")


if __name__ == "__main__":
    loader = TimeSeriesLoader(period="2y").load()
    corr = loader.bank_returns.corr().values
    mock_preds = np.random.uniform(0.006, 0.009, size=len(BANK_TICKERS))
    calculate_systemic_netting(BANK_TICKERS, mock_preds, corr)
