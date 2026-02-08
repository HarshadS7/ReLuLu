export function HubBar({ name, score }: { name: string; score: number }) {
  const pct = Math.min(score * 100, 100);
  const color =
    pct > 70 ? "bg-red-500" : pct > 30 ? "bg-amber-500" : "bg-green-500";
  return (
    <div className="flex items-center gap-4 py-2">
      <span className="w-14 text-sm font-mono font-medium theme-text-primary">{name}</span>
      <div className="flex-1 h-5 rounded-full theme-bg-tertiary overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-16 text-right text-sm font-mono theme-text-muted">
        {score.toFixed(4)}
      </span>
    </div>
  );
}
