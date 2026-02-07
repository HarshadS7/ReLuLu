"""
Shared constants for the ReLuLu / Spectra financial engine.
"""

# --- Bank universe ---
BANK_TICKERS = ["JPM", "BAC", "WFC", "C", "USB", "GS", "MS"]
MACRO_TICKERS = ["^TNX"]  # 10-Year Treasury Yield

# --- Graph construction ---
CORRELATION_THRESHOLD = 0.7

# --- Real-time tick intervals (seconds) ---
DATA_REFRESH_INTERVAL = 60        # re-fetch market data
FORECAST_RECOMPUTE_INTERVAL = 60  # re-run the GNN + netting pipeline
MAX_TICK_ERRORS = 5               # pause ticking after N consecutive failures

# --- Model paths (relative to backend/) ---
TEMPORAL_MODEL_PATH = "temporal_gnn_v1.pth"
LEGACY_MODEL_PATH = "super_node_v1.pth"

# --- Market caps for netting reports (billions USD) ---
MARKET_CAPS = {
    "JPM": 580, "BAC": 300, "WFC": 210,
    "C": 110, "USB": 65, "GS": 140, "MS": 150,
}
