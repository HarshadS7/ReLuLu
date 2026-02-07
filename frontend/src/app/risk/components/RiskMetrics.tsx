"use client";

import { AlertTriangle, Shield, TrendingDown, Activity } from "lucide-react";
import type { BankResult, EdgeResult, HorizonSnapshot } from "../../types";

function RiskBadge({ level }: { level: "low" | "medium" | "high" | "critical" }) {
  const styles = {
    low: "bg-green-500/15 text-green-400 ring-green-500/30",
    medium: "bg-amber-500/15 text-amber-400 ring-amber-500/30",
    high: "bg-orange-500/15 text-orange-400 ring-orange-500/30",
    critical: "bg-red-500/15 text-red-400 ring-red-500/30",
  };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase ring-1 ${styles[level]}`}>
      {level}
    </span>
  );
}

function getRiskLevel(hubScore: number): "low" | "medium" | "high" | "critical" {
  if (hubScore > 0.7) return "critical";
  if (hubScore > 0.5) return "high";
  if (hubScore > 0.3) return "medium";
  return "low";
}

export function RiskMetrics({ snap }: { snap: HorizonSnapshot }) {
  const sortedBanks = [...snap.banks].sort((a, b) => b.hub_score - a.hub_score);
  const totalExposure = snap.raw_load;
  const netExposure = snap.net_load;
  const avgHub = snap.banks.reduce((s, b) => s + b.hub_score, 0) / snap.banks.length;
  const maxHub = Math.max(...snap.banks.map((b) => b.hub_score));
  const concentration = maxHub / (avgHub || 1);

  // Count high-risk edges (after netting)
  const highRiskEdges = snap.edges_after.filter((e) => e.weight_after > 0.5).length;
  const totalEdges = snap.edges_after.length;

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex items-center gap-2 text-xs text-zinc-500 mb-1">
            <Shield className="h-3.5 w-3.5" />
            Gross Exposure
          </div>
          <p className="text-xl font-mono font-bold text-zinc-100">${totalExposure.toFixed(1)}M</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex items-center gap-2 text-xs text-zinc-500 mb-1">
            <TrendingDown className="h-3.5 w-3.5" />
            Net Exposure
          </div>
          <p className="text-xl font-mono font-bold text-green-400">${netExposure.toFixed(1)}M</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex items-center gap-2 text-xs text-zinc-500 mb-1">
            <Activity className="h-3.5 w-3.5" />
            Concentration
          </div>
          <p className="text-xl font-mono font-bold text-amber-400">{concentration.toFixed(2)}x</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex items-center gap-2 text-xs text-zinc-500 mb-1">
            <AlertTriangle className="h-3.5 w-3.5" />
            High-Risk Links
          </div>
          <p className="text-xl font-mono font-bold text-red-400">
            {highRiskEdges}<span className="text-sm text-zinc-500">/{totalEdges}</span>
          </p>
        </div>
      </div>

      {/* Per-bank risk breakdown */}
      <div>
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Bank Risk Breakdown
        </h3>
        <div className="space-y-2">
          {sortedBanks.map((bank) => {
            const riskLevel = getRiskLevel(bank.hub_score);
            const hubPct = Math.min(bank.hub_score * 100, 100);
            return (
              <div
                key={bank.name}
                className="rounded-lg border border-zinc-800/60 bg-zinc-900/30 px-4 py-3"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono font-medium text-zinc-200">
                      {bank.name}
                    </span>
                    <RiskBadge level={riskLevel} />
                  </div>
                  <span
                    className={`text-xs font-mono font-medium ${
                      bank.predicted_score < 0 ? "text-red-400" : "text-green-400"
                    }`}
                  >
                    {bank.predicted_score > 0 ? "+" : ""}
                    {(bank.predicted_score * 100).toFixed(3)}%
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 rounded-full bg-zinc-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        hubPct > 70
                          ? "bg-red-500"
                          : hubPct > 40
                            ? "bg-amber-500"
                            : "bg-green-500"
                      }`}
                      style={{ width: `${hubPct}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500 w-12 text-right">
                    {bank.hub_score.toFixed(4)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top exposures */}
      <div>
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Top Bilateral Exposures
        </h3>
        <div className="space-y-1">
          {[...snap.edges_after]
            .sort((a, b) => b.weight_after - a.weight_after)
            .slice(0, 8)
            .map((e, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-zinc-800/40 transition"
              >
                <span className="text-xs font-mono text-zinc-400">
                  {e.source} → {e.target}
                </span>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono text-zinc-600 line-through">
                    {e.weight_before.toFixed(2)}
                  </span>
                  <span className="text-xs font-mono font-medium text-amber-400">
                    {e.weight_after.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
