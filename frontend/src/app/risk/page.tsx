"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import localFont from "next/font/local";
import axios from "axios";
import {
  ArrowLeft,
  AlertTriangle,
  Loader2,
  Network,
  RefreshCw,
  Shield,
} from "lucide-react";

import type { ForecastResponse, HorizonSnapshot } from "../types";
import { RiskGraph } from "./components/RiskGraph";
import { RiskMetrics } from "./components/RiskMetrics";

const rostex = localFont({
  src: "../../fonts/ALTRONED Trial.otf",
  display: "swap",
});

const API = "http://localhost:8000";

export default function RiskPage() {
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeHorizon, setActiveHorizon] = useState(0);
  const [graphMode, setGraphMode] = useState<"before" | "after">("after");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get<ForecastResponse>(`${API}/api/forecast`);
      setData(res.data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(`Failed to reach backend: ${msg}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const snap: HorizonSnapshot | undefined = data?.horizons[activeHorizon];

  return (
    <div className="min-h-screen bg-[#0d0417] text-zinc-100">
      {/* Header */}
      <header className="border-b border-white/10 bg-[#0d0417] px-8 py-5">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-2 rounded-lg bg-zinc-800/60 px-3 py-2 text-xs text-zinc-400 transition hover:bg-zinc-700/60 hover:text-zinc-200"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Dashboard
            </Link>
            <div className="flex items-center gap-3">
              <Shield className="h-5 w-5 text-red-400" />
              <h1 className="tracking-tight">
                <span className={`${rostex.className} text-2xl`}>SPECTRA</span>{" "}
                <span className="text-sm font-normal text-zinc-500">
                  Risk Analysis
                </span>
              </h1>
            </div>
          </div>

          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-red-600/80 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-500 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Refresh
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] px-8 py-8">
        {/* Error */}
        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && !data && (
          <div className="flex flex-col items-center justify-center py-32">
            <Loader2 className="h-10 w-10 animate-spin text-zinc-600 mb-4" />
            <p className="text-sm text-zinc-500">Loading risk data…</p>
          </div>
        )}

        {/* Content */}
        {data && snap && (
          <div className="space-y-6">
            {/* Horizon selector + graph mode toggle */}
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span className="text-xs text-zinc-500 mr-1">Horizon:</span>
                {data.horizons.map((h, idx) => (
                  <button
                    key={idx}
                    onClick={() => setActiveHorizon(idx)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-mono transition ${
                      idx === activeHorizon
                        ? "bg-purple-500/20 text-purple-300 ring-1 ring-purple-500/40"
                        : "text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
                    }`}
                  >
                    T+{h.horizon}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-1 rounded-lg bg-zinc-900 p-1 ring-1 ring-zinc-800">
                <button
                  onClick={() => setGraphMode("before")}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                    graphMode === "before"
                      ? "bg-zinc-700 text-zinc-100"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  Before Netting
                </button>
                <button
                  onClick={() => setGraphMode("after")}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                    graphMode === "after"
                      ? "bg-zinc-700 text-zinc-100"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  After Netting
                </button>
              </div>
            </div>

            {/* Stability banner */}
            <div
              className={`flex items-center gap-3 rounded-xl border px-5 py-3 ${
                snap.is_stable
                  ? "border-green-500/30 bg-green-500/10"
                  : "border-red-500/30 bg-red-500/10"
              }`}
            >
              {snap.is_stable ? (
                <Shield className="h-5 w-5 text-green-400" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-red-400" />
              )}
              <span
                className={`text-sm font-semibold ${snap.is_stable ? "text-green-400" : "text-red-400"}`}
              >
                {snap.is_stable
                  ? `Stability Index: ${snap.stability.toFixed(4)} — System within safe bounds`
                  : `Stability Index: ${snap.stability.toFixed(4)} — Cascading risk detected`}
              </span>
              <span className="ml-auto text-xs text-zinc-500">
                Payload Reduction: {snap.payload_reduction.toFixed(1)}%
              </span>
            </div>

            {/* Main layout: Graph + Metrics */}
            <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
              {/* Graph (2/3 width) */}
              <div className="xl:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Network className="h-4 w-4 text-purple-400" />
                  <h2 className="text-sm font-semibold text-zinc-300">
                    Obligation Network — T+{snap.horizon}{" "}
                    <span className="text-zinc-500 font-normal">
                      ({graphMode === "before" ? "Pre-Netting" : "Post-Netting"})
                    </span>
                  </h2>
                </div>
                <RiskGraph
                  banks={snap.banks}
                  edges={graphMode === "before" ? snap.edges_before : snap.edges_after}
                  mode={graphMode}
                />
                <div className="mt-3 flex flex-wrap gap-4 text-[10px] text-zinc-500">
                  <span className="flex items-center gap-1">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-500" />
                    Low risk
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-500" />
                    Medium risk
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
                    High risk
                  </span>
                  <span className="ml-auto">node size = hub score · edge width = obligation weight</span>
                </div>
              </div>

              {/* Risk metrics (1/3 width) */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 overflow-y-auto max-h-[800px]">
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle className="h-4 w-4 text-red-400" />
                  <h2 className="text-sm font-semibold text-zinc-300">
                    Risk Metrics — T+{snap.horizon}
                  </h2>
                </div>
                <RiskMetrics snap={snap} />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
