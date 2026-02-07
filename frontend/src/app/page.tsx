"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import localFont from "next/font/local";
import Link from "next/link";
import axios from "axios";
import {
  Activity,
  AlertTriangle,
  Calendar,
  CheckCircle,
  Clock,
  Database,
  Loader2,
  Play,
  TrendingDown,
  TrendingUp,
  Wifi,
  WifiOff,
  Zap,
} from "lucide-react";

import type {
  ForecastResponse,
  HorizonSnapshot,
  TickStatus,
} from "./types";
import {
  StatCard,
  HubBar,
  ObligationsMatrix,
  HorizonTimeline,
  TickerBar,
} from "./components";
import IntroLoader from "@/components/IntroLoader";

const rostex = localFont({
  src: "../fonts/ALTRONED Trial.otf",
  display: "swap",
});

const API = "http://localhost:8000";

// =====================================================================
// Main Page
// =====================================================================

export default function Home() {
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeHorizon, setActiveHorizon] = useState(0);

  // --- Live tick state ---
  const [tickStatus, setTickStatus] = useState<TickStatus | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [countdown, setCountdown] = useState(0);
  const pollInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastTickCount = useRef<number>(-1);

  const POLL_INTERVAL_S = 60; // match backend FORECAST_RECOMPUTE_INTERVAL

  // --- Fetch forecast (used by both manual click & auto-poll) ---
  const fetchForecast = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const [forecastRes, tickRes] = await Promise.all([
        axios.get<ForecastResponse>(`${API}/api/forecast`),
        axios.get<TickStatus>(`${API}/api/tick`),
      ]);
      setData(forecastRes.data);
      setTickStatus(tickRes.data);
      if (forecastRes.data.horizons.length > 0 && activeHorizon >= forecastRes.data.horizons.length) {
        setActiveHorizon(0);
      }
      lastTickCount.current = tickRes.data.tick_count;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      if (!silent) setError(`Failed to reach backend: ${msg}`);
    } finally {
      if (!silent) setLoading(false);
    }
  }, [activeHorizon]);

  // --- Manual run ---
  const runForecast = async () => {
    setLoading(true);
    await Promise.all([
      fetchForecast(true),
      new Promise((r) => setTimeout(r, 1000)),
    ]);
    setLoading(false);
    setCountdown(POLL_INTERVAL_S);
  };

  // --- Auto-poll effect ---
  useEffect(() => {
    // Auto-run forecast on initial load
    runForecast();
    setCountdown(POLL_INTERVAL_S);

    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
      if (countdownInterval.current) clearInterval(countdownInterval.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (pollInterval.current) clearInterval(pollInterval.current);
    if (countdownInterval.current) clearInterval(countdownInterval.current);

    if (autoRefresh) {
      pollInterval.current = setInterval(() => {
        fetchForecast(true);
        setCountdown(POLL_INTERVAL_S);
      }, POLL_INTERVAL_S * 1000);

      countdownInterval.current = setInterval(() => {
        setCountdown((c) => Math.max(c - 1, 0));
      }, 1000);
    }

    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
      if (countdownInterval.current) clearInterval(countdownInterval.current);
    };
  }, [autoRefresh, fetchForecast]);

  const snap: HorizonSnapshot | undefined = data?.horizons[activeHorizon];

  return (
    <div className="min-h-screen bg-[#0d0417] text-zinc-100">
      <IntroLoader />
      {/* Header */}
      <header className="border-b border-white/10 bg-[#0d0417] px-8 py-6">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-4">
            <video
              src="/34004-399415222_tiny.webm"
              autoPlay
              loop
              muted
              playsInline
              className="h-20 w-20 rounded-xl object-cover mix-blend-screen brightness-[0.6] contrast-[2]"
            />
            <h1 className="tracking-tight">
              <span className={`${rostex.className} text-3xl`}>SPECTRA</span>{" "}
              <span className="text-base font-normal text-zinc-500">
                Temporal Forecast Engine
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/risk"
              className="flex items-center gap-1.5 rounded-lg bg-red-600/15 px-3 py-2 text-xs font-medium text-red-400 ring-1 ring-red-500/25 transition hover:bg-red-600/25"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Risk Analysis
            </Link>
            {/* Auto-refresh toggle */}
            <button
              onClick={() => setAutoRefresh((v) => !v)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
                autoRefresh
                  ? "bg-green-600/20 text-green-400 ring-1 ring-green-500/30"
                  : "bg-zinc-800 text-zinc-500 ring-1 ring-zinc-700"
              }`}
              title={autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}
            >
              {autoRefresh ? (
                <Wifi className="h-3.5 w-3.5" />
              ) : (
                <WifiOff className="h-3.5 w-3.5" />
              )}
              {autoRefresh ? "LIVE" : "PAUSED"}
            </button>

            <button
              onClick={runForecast}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {loading ? "Forecasting…" : "Run Forecast"}
            </button>
          </div>
        </div>
      </header>

      {/* Ticker status bar */}
      <TickerBar
        tickStatus={tickStatus}
        autoRefresh={autoRefresh}
        countdown={countdown}
      />

      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* Error */}
        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        )}

        {/* Empty state */}
        {!data && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-32 text-center">
            <Activity className="mb-4 h-12 w-12 text-zinc-700" />
            <h2 className="text-xl font-semibold text-zinc-400">
              No data yet
            </h2>
            <p className="mt-2 text-sm text-zinc-600">
              Click <strong>Run Forecast</strong> to load live market data and
              generate multi-horizon risk projections
            </p>
          </div>
        )}

        {/* Dashboard */}
        {data && snap && (
          <div className="space-y-8">
            {/* Data source badge */}
            <div className="flex flex-wrap items-center gap-4 text-xs text-zinc-500">
              <span className="flex items-center gap-1">
                <Database className="h-3 w-3" />
                {data.metadata.model_type}
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {data.metadata.date_range[0]} → {data.metadata.date_range[1]}
              </span>
              <span>{data.metadata.total_days} trading days</span>
              <span>{data.horizons.length} forecast horizons</span>
            </div>

            {/* Horizon timeline */}
            <HorizonTimeline
              horizons={data.horizons}
              selected={activeHorizon}
              onSelect={setActiveHorizon}
            />

            {/* Top stats for selected horizon */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <StatCard
                label="Horizon"
                value={`T+${snap.horizon}`}
                sub="Forecast step"
                icon={Clock}
                accent="purple"
              />
              <StatCard
                label="Payload Reduction"
                value={`${snap.payload_reduction.toFixed(1)}%`}
                sub={`$${snap.raw_load.toFixed(1)}M → $${snap.net_load.toFixed(1)}M`}
                icon={TrendingDown}
                accent="green"
              />
              <StatCard
                label="Stability Index"
                value={snap.stability.toFixed(4)}
                sub={snap.is_stable ? "System stable" : "Cascading risk"}
                icon={snap.is_stable ? CheckCircle : AlertTriangle}
                accent={snap.is_stable ? "blue" : "red"}
              />
              <StatCard
                label="Edges Before"
                value={`${snap.edges_before.length}`}
                sub="Gross obligation links"
                icon={Activity}
                accent="amber"
              />
              <StatCard
                label="Edges After"
                value={`${snap.edges_after.length}`}
                sub="Post-netting residual"
                icon={TrendingUp}
                accent="green"
              />
            </div>

            {/* Status Banner */}
            <div
              className={`flex items-center gap-3 rounded-xl border px-5 py-4 ${
                snap.is_stable
                  ? "border-green-500/30 bg-green-500/10"
                  : "border-red-500/30 bg-red-500/10"
              }`}
            >
              {snap.is_stable ? (
                <CheckCircle className="h-5 w-5 text-green-400" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-red-400" />
              )}
              <span
                className={`text-sm font-semibold ${snap.is_stable ? "text-green-400" : "text-red-400"}`}
              >
                {snap.is_stable
                  ? `🟢 T+${snap.horizon} STABLE — Shocks dissipate naturally`
                  : `🔴 T+${snap.horizon} UNSTABLE — Cascading failure risk. Increasing margins.`}
              </span>
            </div>

            {/* Two-column: Hubs + Predictions */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5 flex flex-col">
                <h2 className="mb-4 text-sm font-semibold text-zinc-300">
                  Systemic Hub Rankings — T+{snap.horizon}
                </h2>
                <div className="flex-1 flex flex-col justify-between">
                  {[...snap.banks]
                    .sort((a, b) => b.hub_score - a.hub_score)
                    .map((b) => (
                      <HubBar
                        key={b.name}
                        name={b.name}
                        score={b.hub_score}
                      />
                    ))}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <h2 className="mb-4 text-sm font-semibold text-zinc-300">
                  Forecast Signals — T+{snap.horizon}
                </h2>
                <div className="space-y-2">
                  {snap.banks.map((b) => (
                    <div
                      key={b.name}
                      className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-zinc-800/50"
                    >
                      <span className="text-sm font-mono text-zinc-300">
                        {b.name}
                      </span>
                      <span
                        className={`text-sm font-mono font-medium ${
                          b.predicted_score < 0
                            ? "text-red-400"
                            : "text-green-400"
                        }`}
                      >
                        {b.predicted_score > 0 ? "+" : ""}
                        {(b.predicted_score * 100).toFixed(3)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Obligations Matrices */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <ObligationsMatrix
                  matrix={snap.obligations_before}
                  banks={snap.banks.map((b) => b.name)}
                  title={`Obligations BEFORE Netting — T+${snap.horizon}`}
                />
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <ObligationsMatrix
                  matrix={snap.obligations_after}
                  banks={snap.banks.map((b) => b.name)}
                  title={`Obligations AFTER Netting — T+${snap.horizon}`}
                />
              </div>
            </div>

            {/* Edge Details */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
              <h2 className="mb-4 text-sm font-semibold text-zinc-300">
                Top Residual Obligations — T+{snap.horizon}
              </h2>
              {snap.edges_after.length === 0 ? (
                <p className="text-sm text-zinc-500">
                  All obligations fully netted — zero residual.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 text-left text-xs text-zinc-500">
                        <th className="pb-2 pr-4">From</th>
                        <th className="pb-2 pr-4">To</th>
                        <th className="pb-2 pr-4 text-right">Before</th>
                        <th className="pb-2 pr-4 text-right">After</th>
                        <th className="pb-2 text-right">Reduced</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...snap.edges_after]
                        .sort((a, b) => b.weight_after - a.weight_after)
                        .slice(0, 15)
                        .map((e, i) => {
                          const reduction =
                            e.weight_before > 0
                              ? (
                                  ((e.weight_before - e.weight_after) /
                                    e.weight_before) *
                                  100
                                ).toFixed(1)
                              : "0.0";
                          return (
                            <tr
                              key={i}
                              className="border-b border-zinc-800/50 text-zinc-300"
                            >
                              <td className="py-2 pr-4 font-mono">
                                {e.source}
                              </td>
                              <td className="py-2 pr-4 font-mono">
                                {e.target}
                              </td>
                              <td className="py-2 pr-4 text-right font-mono text-zinc-500">
                                {e.weight_before.toFixed(2)}
                              </td>
                              <td className="py-2 pr-4 text-right font-mono text-amber-400">
                                {e.weight_after.toFixed(2)}
                              </td>
                              <td className="py-2 text-right font-mono text-green-400">
                                {reduction}%
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
