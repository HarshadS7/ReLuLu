export function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  accent = "blue",
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  accent?: string;
}) {
  /* 
    Adjusting for light/dark mode:
    Dark mode: text-*-400, bg-*-500/10
    Light mode: text-*-600, bg-*-500/10 (background can stay similar, text needs to be darker)
   */
  const colors: Record<string, string> = {
    blue: "from-blue-500/10 to-blue-600/5 border-blue-500/20 text-blue-600 dark:text-blue-400",
    green:
      "from-green-500/10 to-green-600/5 border-green-500/20 text-green-600 dark:text-green-400",
    red: "from-red-500/10 to-red-600/5 border-red-500/20 text-red-600 dark:text-red-400",
    amber:
      "from-amber-500/10 to-amber-600/5 border-amber-500/20 text-amber-600 dark:text-amber-400",
    purple:
      "from-purple-500/10 to-purple-600/5 border-purple-500/20 text-purple-600 dark:text-purple-400",
  };
  return (
    <div
      className={`rounded-xl border bg-gradient-to-br p-5 ${colors[accent]}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium theme-text-secondary">{label}</span>
        <Icon className="h-4 w-4 opacity-60" />
      </div>
      <p className="mt-2 text-2xl font-bold theme-text-primary">{value}</p>
      {sub && <p className="mt-1 text-xs theme-text-muted">{sub}</p>}
    </div>
  );
}
