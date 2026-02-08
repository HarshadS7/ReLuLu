"""
Quick terminal test — runs the full forecast pipeline and prints:
  1. Per-bank risk factors
  2. Payload / netting summary (raw → netted → risk-adjusted → worst-case)
  3. Anomaly flags for any bank with unusual recent returns
"""

import os, sys

# ── Fix import root so `data.loader` etc. resolve ───────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from data.loader import TimeSeriesLoader
from core.forecast_engine import ForecastEngine

SEP = "=" * 62


def main():
    # ── 1. Load market data ──────────────────────────────────────────
    print(SEP)
    print("  ReLuLu / Spectra  —  Forecast + Risk Test")
    print(SEP)

    loader = TimeSeriesLoader(period="2y").load()

    # ── 2. Load model (temporal if available, else legacy) ───────────
    temporal_path = os.path.join(BACKEND_DIR, "temporal_gnn_v1.pth")
    legacy_path = os.path.join(BACKEND_DIR, "super_node_v1.pth")

    if os.path.exists(temporal_path):
        model = ForecastEngine.load_temporal(temporal_path)
        model_name = "TemporalGNN"
    else:
        model = ForecastEngine.load_legacy(legacy_path)
        model_name = "SuperNodeGNN (legacy)"

    engine = ForecastEngine(model, loader)
    print(f"\n[MODEL] {model_name}")

    # ── 3. Run forecast ──────────────────────────────────────────────
    result = engine.run_forecast()
    tickers = result["metadata"]["tickers"]

    for snap in result["horizons"]:
        h = snap["horizon"]
        print(f"\n{SEP}")
        print(f"  HORIZON {h}")
        print(SEP)

        # ── Per-bank table ───────────────────────────────────────────
        print(f"\n{'Bank':<6} {'Pred Score':>11} {'Risk Factor':>12} {'Hub Score':>10}")
        print("-" * 42)
        for i, t in enumerate(tickers):
            ps = snap["node_scores"][i]
            rf = snap["risk_factor"][i]
            hs = snap["systemic_hubs"][i]
            print(f"{t:<6} {ps:>+11.6f} {rf:>12.4f} {hs:>10.4f}")

        # ── Payload summary ──────────────────────────────────────────
        print(f"\n{'Metric':<35} {'Value':>14}")
        print("-" * 50)
        print(f"{'Gross Obligations (raw_load)':<35} {snap['raw_load']:>14.2f}")
        print(f"{'After Netting (net_load)':<35} {snap['net_load']:>14.2f}")
        print(f"{'Payload Reduction':<35} {snap['payload_reduction']:>13.2f}%")
        print()
        print(f"{'Risk Buffer (Σ riskᵢ × outflowᵢ)':<35} {snap['risk_buffer']:>14.2f}")
        print(f"{'Risk-Adj Required Money':<35} {snap['risk_adjusted_net_load']:>14.2f}")
        print(f"{'Risk-Adj Payload Reduction':<35} {snap['risk_adjusted_payload_reduction']:>13.2f}%")
        print()
        print(f"{'Worst-Case Buffer (top-risk banks)':<35} {snap['worst_case_buffer']:>14.2f}")
        print(f"{'Worst-Case Required Money':<35} {snap['worst_case_net_load']:>14.2f}")
        print(f"{'Worst-Case Payload Reduction':<35} {snap['worst_case_payload_reduction']:>13.2f}%")

    # ── 4. Anomaly detection ─────────────────────────────────────────
    print(f"\n{SEP}")
    print("  ANOMALY FLAGS  (z-score > threshold on recent returns)")
    print(SEP)

    anomalies = loader.detect_anomalies()

    if not anomalies:
        print("\n  ✅  No anomalies detected — all banks within normal range.\n")
    else:
        print(f"\n  ⚠️  {len(anomalies)} anomaly/anomalies detected!\n")
        print(f"{'Bank':<6} {'Date':<12} {'Return':>9} {'Z-score':>9} {'Flag':<12}")
        print("-" * 50)
        for a in anomalies:
            print(
                f"{a['bank']:<6} {a['date']:<12} {a['return']:>+9.5f} "
                f"{a['z_score']:>+9.3f} {a['direction']:<12}"
            )
        print()

    print(SEP)
    print("  Done.")
    print(SEP)


if __name__ == "__main__":
    main()
