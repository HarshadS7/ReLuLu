"""
FastAPI route handlers.
"""

from fastapi import APIRouter

from api.schemas import (
    BankResult,
    EdgeResult,
    HorizonSnapshot,
    DataMeta,
    ForecastResponse,
    PipelineResponse,
)
from api import ticker
from data.constants import DATA_REFRESH_INTERVAL, FORECAST_RECOMPUTE_INTERVAL

router = APIRouter(prefix="/api")

# Reference to the ForecastEngine — set by app.py
_engine = None


def set_engine(engine):
    global _engine
    _engine = engine


# =====================================================================
# Helpers
# =====================================================================
def _format_snapshot(snap: dict, tickers: list[str]) -> HorizonSnapshot:
    """Convert a raw engine snapshot dict into the API schema."""
    n = len(tickers)
    banks = []
    for i, name in enumerate(tickers):
        banks.append(BankResult(
            name=name,
            predicted_score=round(float(snap["node_scores"][i]), 6),
            hub_score=round(float(snap["systemic_hubs"][i]), 4),
        ))

    ob_before = snap["obligations_before"]
    ob_after = snap["obligations_after"]

    edges_before, edges_after = [], []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            wb = float(ob_before[i][j])
            wa = float(ob_after[i][j])
            if wb > 0.01:
                edges_before.append(EdgeResult(
                    source=tickers[i], target=tickers[j],
                    weight_before=round(wb, 4), weight_after=round(wa, 4),
                ))
            if wa > 0.01:
                edges_after.append(EdgeResult(
                    source=tickers[i], target=tickers[j],
                    weight_before=round(wb, 4), weight_after=round(wa, 4),
                ))

    return HorizonSnapshot(
        horizon=snap["horizon"],
        banks=banks,
        edges_before=edges_before,
        edges_after=edges_after,
        stability=round(snap["stability"], 6),
        is_stable=snap["stability"] < 1.0,
        payload_reduction=round(snap["payload_reduction"], 2),
        raw_load=round(snap["raw_load"], 2),
        net_load=round(snap["net_load"], 2),
        obligations_before=[[round(float(v), 4) for v in row] for row in ob_before],
        obligations_after=[[round(float(v), 4) for v in row] for row in ob_after],
    )


# =====================================================================
# Routes
# =====================================================================
@router.get("/forecast", response_model=ForecastResponse)
def run_forecast():
    """Multi-horizon temporal forecast — returns the latest cached result."""
    result = ticker.cached_forecast

    if result is None:
        result = _engine.run_forecast()

    meta = result["metadata"]
    tickers = meta["tickers"]
    snapshots = [_format_snapshot(s, tickers) for s in result["horizons"]]
    model_type = "TemporalGNN" if _engine.is_temporal else "SuperNodeGNN (legacy)"

    return ForecastResponse(
        horizons=snapshots,
        metadata=DataMeta(
            tickers=tickers,
            num_banks=meta["num_banks"],
            total_days=meta["total_days"],
            date_range=list(meta["date_range"]),
            last_updated=meta["last_updated"],
            model_type=model_type,
        ),
    )


@router.get("/tick")
def tick_status():
    """Live tick status — used by the frontend to show freshness."""
    return {
        "tick_count": ticker.tick_count,
        "last_data_refresh": ticker.last_data_refresh,
        "last_forecast_time": ticker.last_forecast_time,
        "ticker_active": ticker.tick_running,
        "consecutive_errors": ticker.tick_errors,
        "data_refresh_interval_s": DATA_REFRESH_INTERVAL,
        "forecast_recompute_interval_s": FORECAST_RECOMPUTE_INTERVAL,
    }


@router.get("/config")
def config():
    """Returns tick intervals so the frontend can synchronize its polling."""
    return {
        "data_refresh_interval_s": DATA_REFRESH_INTERVAL,
        "forecast_recompute_interval_s": FORECAST_RECOMPUTE_INTERVAL,
        "frontend_poll_interval_s": FORECAST_RECOMPUTE_INTERVAL,
    }


@router.get("/run", response_model=PipelineResponse)
def run_pipeline():
    """Backward-compatible single-snapshot endpoint (horizon 1 only)."""
    result = _engine.run_forecast()
    tickers = result["metadata"]["tickers"]
    snap = _format_snapshot(result["horizons"][0], tickers)
    return PipelineResponse(
        banks=snap.banks,
        edges_before=snap.edges_before,
        edges_after=snap.edges_after,
        stability=snap.stability,
        is_stable=snap.is_stable,
        payload_reduction=snap.payload_reduction,
        raw_load=snap.raw_load,
        net_load=snap.net_load,
        obligations_before=snap.obligations_before,
        obligations_after=snap.obligations_after,
    )


@router.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": _engine is not None,
        "model_type": "TemporalGNN" if (_engine and _engine.is_temporal) else "legacy",
        "data_loaded": ticker.cached_forecast is not None,
    }
