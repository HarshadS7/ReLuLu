import { Clock } from "lucide-react";
import type { HorizonSnapshot } from "../types";

export function HorizonTimeline({
  horizons,
  selected,
  onSelect,
}: {
  horizons: HorizonSnapshot[];
  selected: number;
  onSelect: (idx: number) => void;
}) {
  const maxStab = Math.max(...horizons.map((h) => h.stability), 1);
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-zinc-300">
        <Clock className="h-4 w-4 text-purple-400" />
        Forecast Timeline — click a horizon to inspect
      </h2>

      <div className="overflow-x-auto pb-2">
        <div className="flex items-center gap-3 w-full">
          {horizons.map((h, idx) => {
            const barW = Math.max((h.stability / maxStab) * 48, 6);
            const isActive = idx === selected;
            return (
              <button
                key={idx}
                onClick={() => onSelect(idx)}
                className={`grid grid-cols-3 flex-1 items-center rounded-lg px-4 py-3 transition ${
                  isActive
                    ? "bg-purple-500/20 ring-1 ring-purple-500/50"
                    : "hover:bg-zinc-800"
                }`}
              >
                <span className="text-xs font-mono font-semibold text-zinc-300 text-center whitespace-nowrap">
                  T+{h.horizon}
                </span>
                <span className="text-xs font-mono text-zinc-500 text-center">
                  {h.stability.toFixed(2)}
                </span>
                <span className="flex items-center justify-center gap-1.5">
                  <span className="text-xs font-mono font-medium text-green-400">
                    {h.payload_reduction.toFixed(0)}%
                  </span>
                  <div
                    className={`h-3.5 rounded transition-all duration-500 ${
                      h.is_stable ? "bg-green-500" : "bg-red-500"
                    }`}
                    style={{ width: `${barW}px` }}
                  />
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-3 flex gap-4 text-[10px] text-zinc-500">
        <span>
          <span className="inline-block h-2 w-2 rounded-full bg-green-500 mr-1" />
          Stable
        </span>
        <span>
          <span className="inline-block h-2 w-2 rounded-full bg-red-500 mr-1" />
          Unstable
        </span>
        <span className="ml-auto">bar = stability index</span>
      </div>
    </div>
  );
}
