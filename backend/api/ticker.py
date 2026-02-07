"""
Background ticker — refreshes market data and recomputes forecasts
on a configurable interval using asyncio tasks.
"""

import asyncio
from datetime import datetime, timezone

from data.constants import DATA_REFRESH_INTERVAL, FORECAST_RECOMPUTE_INTERVAL, MAX_TICK_ERRORS

# --- Tick state (module-level singletons) ---
tick_count: int = 0
last_data_refresh: str = "—"
last_forecast_time: str = "—"
tick_running: bool = False
tick_errors: int = 0
cached_forecast: dict | None = None

# These are set by app.py at startup
_engine_ref = None
_loader_ref = None
_refresh_fn = None   # callable: () -> None
_recompute_fn = None  # callable: () -> None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def configure(refresh_fn, recompute_fn):
    """Called once by app.py to inject the blocking sync functions."""
    global _refresh_fn, _recompute_fn
    _refresh_fn = refresh_fn
    _recompute_fn = recompute_fn


def refresh_data_sync():
    """Re-download market data and rebuild the forecast engine (blocking)."""
    global last_data_refresh
    if _refresh_fn:
        _refresh_fn()
    last_data_refresh = _now_iso()


def recompute_forecast_sync():
    """Run the forecast pipeline and cache the result (blocking)."""
    global cached_forecast, last_forecast_time
    if _recompute_fn:
        cached_forecast = _recompute_fn()
    last_forecast_time = _now_iso()


async def ticker_task():
    """Async background task: refreshes data and recomputes forecasts on a tick."""
    global tick_count, tick_running, tick_errors
    tick_running = True
    print(
        f"[TICK] Background ticker started — data every {DATA_REFRESH_INTERVAL}s, "
        f"forecast every {FORECAST_RECOMPUTE_INTERVAL}s"
    )

    data_countdown = DATA_REFRESH_INTERVAL   # first data refresh after full interval
    forecast_countdown = 0                    # first forecast immediately

    while tick_running:
        try:
            await asyncio.sleep(1)  # heartbeat every 1 second
            data_countdown -= 1
            forecast_countdown -= 1

            # --- Data refresh tick ---
            if data_countdown <= 0:
                print(f"[TICK #{tick_count}] Refreshing market data …")
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, refresh_data_sync)
                data_countdown = DATA_REFRESH_INTERVAL
                forecast_countdown = 0  # force forecast after data refresh
                tick_count += 1
                print(f"[TICK #{tick_count}] Data refresh complete")

            # --- Forecast recompute tick ---
            if forecast_countdown <= 0:
                print(f"[TICK #{tick_count}] Recomputing forecast …")
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, recompute_forecast_sync)
                forecast_countdown = FORECAST_RECOMPUTE_INTERVAL
                print(f"[TICK #{tick_count}] Forecast cached")

            tick_errors = 0

        except asyncio.CancelledError:
            print("[TICK] Ticker cancelled")
            break
        except Exception as exc:
            import traceback
            tick_errors += 1
            print(f"[TICK] Error ({tick_errors}/{MAX_TICK_ERRORS}): {exc}")
            traceback.print_exc()
            if tick_errors >= MAX_TICK_ERRORS:
                print("[TICK] Too many errors — pausing ticker for 5 min")
                await asyncio.sleep(300)
                tick_errors = 0
            else:
                await asyncio.sleep(10)

    tick_running = False
