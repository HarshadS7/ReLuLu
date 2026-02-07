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

      <div className="flex items-end gap-2">
        {horizons.map((h, idx) => {
          const barH = Math.max((h.stability / maxStab) * 100, 8);
          const isActive = idx === selected;
          return (
            <button
              key={idx}
              onClick={() => onSelect(idx)}
              className={`flex flex-col items-center flex-1 rounded-lg p-2 transition ${
                isActive
                  ? "bg-purple-500/20 ring-1 ring-purple-500/50"
                  : "hover:bg-zinc-800"
              }`}
            >
              <div className="w-full flex justify-center mb-2">
                <div
                  className={`w-6 rounded-t transition-all duration-500 ${
                    h.is_stable ? "bg-green-500" : "bg-red-500"
                  }`}
                  style={{ height: `${barH}px` }}
                />
              </div>
              <span className="text-[10px] font-mono text-zinc-500">
                T+{h.horizon}
              </span>
              <span className="text-[10px] font-mono text-zinc-400">
                {h.stability.toFixed(2)}
              </span>
              <span className="text-[10px] font-mono text-green-400">
                {h.payload_reduction.toFixed(0)}%
              </span>
            </button>
          );
        })}
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
        <span className="ml-auto">bar height = stability index</span>
      </div>
    </div>
  );
}
