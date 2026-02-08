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
    <div className="border-b theme-border theme-bg-secondary px-6 py-2 transition-colors duration-300">
      <div className="mx-auto flex max-w-7xl items-center gap-6 text-[11px] font-mono">
        {/* Pulse dot */}
        <span className="flex items-center gap-1.5">
          <span
            className={`inline-block h-2 w-2 rounded-full ${autoRefresh && tickStatus?.ticker_active
                ? "bg-green-500 animate-pulse"
                : "bg-zinc-400 dark:bg-zinc-600"
              }`}
          />
          <span className="theme-text-secondary">
            {autoRefresh ? "LIVE" : "PAUSED"}
          </span>
        </span>

        {tickStatus && (
          <>
            <span className="theme-text-muted">
              Tick{" "}
              <span className="theme-text-primary">#{tickStatus.tick_count}</span>
            </span>

            <span className="theme-text-muted">
              Data refreshed{" "}
              <span className="theme-text-primary">
                {tickStatus.last_data_refresh}
              </span>
            </span>

            <span className="theme-text-muted">
              Forecast computed{" "}
              <span className="theme-text-primary">
                {tickStatus.last_forecast_time}
              </span>
            </span>

            <span className="theme-text-muted">
              Interval{" "}
              <span className="theme-text-primary">
                {tickStatus.data_refresh_interval_s}s
              </span>
            </span>

            {tickStatus.consecutive_errors > 0 && (
              <span className="text-red-500 dark:text-red-400">
                ⚠ {tickStatus.consecutive_errors} errors
              </span>
            )}
          </>
        )}

        {autoRefresh && (
          <span className="ml-auto flex items-center gap-1.5 theme-text-muted">
            <RefreshCw
              className={`h-3 w-3 ${countdown <= 5 ? "text-blue-500 animate-spin" : ""
                }`}
            />
            next refresh in{" "}
            <span className="theme-text-primary">{countdown}s</span>
          </span>
        )}
      </div>
    </div>
  );
}
