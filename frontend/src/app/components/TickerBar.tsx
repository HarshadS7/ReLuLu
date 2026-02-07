import { RefreshCw, Wifi, WifiOff } from "lucide-react";
import type { TickStatus } from "../types";

export function TickerBar({
  tickStatus,
  autoRefresh,
  countdown,
}: {
  tickStatus: TickStatus | null;
  autoRefresh: boolean;
  countdown: number;
}) {
  return (
    <div className="border-b border-zinc-800/50 bg-zinc-900/50 px-6 py-2">
      <div className="mx-auto flex max-w-7xl items-center gap-6 text-[11px] font-mono">
        {/* Pulse dot */}
        <span className="flex items-center gap-1.5">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              autoRefresh && tickStatus?.ticker_active
                ? "bg-green-500 animate-pulse"
                : "bg-zinc-600"
            }`}
          />
          <span className="text-zinc-400">
            {autoRefresh ? "LIVE" : "PAUSED"}
          </span>
        </span>

        {tickStatus && (
          <>
            <span className="text-zinc-500">
              Tick{" "}
              <span className="text-zinc-300">#{tickStatus.tick_count}</span>
            </span>

            <span className="text-zinc-500">
              Data refreshed{" "}
              <span className="text-zinc-300">
                {tickStatus.last_data_refresh}
              </span>
            </span>

            <span className="text-zinc-500">
              Forecast computed{" "}
              <span className="text-zinc-300">
                {tickStatus.last_forecast_time}
              </span>
            </span>

            <span className="text-zinc-500">
              Interval{" "}
              <span className="text-zinc-300">
                {tickStatus.data_refresh_interval_s}s
              </span>
            </span>

            {tickStatus.consecutive_errors > 0 && (
              <span className="text-red-400">
                ⚠ {tickStatus.consecutive_errors} errors
              </span>
            )}
          </>
        )}

        {autoRefresh && (
          <span className="ml-auto flex items-center gap-1.5 text-zinc-500">
            <RefreshCw
              className={`h-3 w-3 ${
                countdown <= 5 ? "text-blue-400 animate-spin" : ""
              }`}
            />
            next refresh in{" "}
            <span className="text-zinc-300">{countdown}s</span>
          </span>
        )}
      </div>
    </div>
  );
}
