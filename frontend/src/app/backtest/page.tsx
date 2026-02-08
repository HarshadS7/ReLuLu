"use client";

import React, { useState, useEffect } from "react";
import axios from "axios";
import Link from "next/link";
import {
    ArrowLeft,
    RefreshCw,
    TrendingUp,
    TrendingDown,
    BarChart3,
    Calendar,
} from "lucide-react";
import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
} from "recharts";

interface BacktestResult {
    date: string;
    predictions: Record<string, number>;
    actuals: Record<string, number>;
    metrics: {
        mae: number | null;
        directional_accuracy: number | null;
        correlation: number | null;
    };
}

interface BacktestResponse {
    aggregate: {
        total_days: number;
        avg_mae: number | null;
        avg_directional_accuracy: number | null;
        best_day: string | null;
        worst_day: string | null;
    };
    results: BacktestResult[];
    timestamp: string;
}

export default function BacktestPage() {
    const [data, setData] = useState<BacktestResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [days, setDays] = useState(30);

    const fetchBacktest = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await axios.get<BacktestResponse>(
                `http://localhost:8000/api/backtest?days=${days}`
            );
            setData(res.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to run backtest");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBacktest();
    }, [days]);

    const chartData = data?.results.map((r) => ({
        date: r.date,
        accuracy: r.metrics.directional_accuracy
            ? +(r.metrics.directional_accuracy * 100).toFixed(1)
            : 0,
        mae: r.metrics.mae ? +r.metrics.mae.toFixed(4) : 0,
    })) || [];

    return (
        <div className="min-h-screen theme-bg-primary theme-text-primary p-8 font-sans transition-colors duration-300">
            <div className="max-w-6xl mx-auto">
                <header className="mb-8 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/"
                            className="p-2 rounded-full hover:theme-bg-tertiary transition-colors"
                        >
                            <ArrowLeft className="w-6 h-6 theme-text-muted" />
                        </Link>
                        <div>
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-500 bg-clip-text text-transparent">
                                Backtesting
                            </h1>
                            <p className="theme-text-muted text-sm mt-1">
                                Compare model predictions vs actual outcomes
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <select
                            value={days}
                            onChange={(e) => setDays(Number(e.target.value))}
                            className="theme-bg-secondary theme-text-primary theme-border border rounded-lg px-3 py-2 text-sm"
                        >
                            <option value={7}>Last 7 days</option>
                            <option value={14}>Last 14 days</option>
                            <option value={30}>Last 30 days</option>
                            <option value={60}>Last 60 days</option>
                        </select>
                        <button
                            onClick={fetchBacktest}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg transition-all disabled:opacity-50 text-white"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                            Run Backtest
                        </button>
                    </div>
                </header>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
                        {error}
                    </div>
                )}

                {/* Aggregate Stats */}
                {data?.aggregate && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                        <div className="theme-card theme-border border rounded-xl p-4">
                            <div className="flex items-center gap-2 theme-text-muted text-xs mb-2">
                                <Calendar className="w-4 h-4" />
                                Days Tested
                            </div>
                            <p className="text-2xl font-mono font-bold theme-text-primary">
                                {data.aggregate.total_days}
                            </p>
                        </div>
                        <div className="theme-card theme-border border rounded-xl p-4">
                            <div className="flex items-center gap-2 theme-text-muted text-xs mb-2">
                                <TrendingUp className="w-4 h-4" />
                                Directional Accuracy
                            </div>
                            <p className="text-2xl font-mono font-bold text-emerald-400">
                                {data.aggregate.avg_directional_accuracy
                                    ? `${(data.aggregate.avg_directional_accuracy * 100).toFixed(1)}%`
                                    : "N/A"}
                            </p>
                        </div>
                        <div className="theme-card theme-border border rounded-xl p-4">
                            <div className="flex items-center gap-2 theme-text-muted text-xs mb-2">
                                <BarChart3 className="w-4 h-4" />
                                Avg MAE
                            </div>
                            <p className="text-2xl font-mono font-bold text-blue-400">
                                {data.aggregate.avg_mae?.toFixed(4) || "N/A"}
                            </p>
                        </div>
                        <div className="theme-card theme-border border rounded-xl p-4">
                            <div className="flex items-center gap-2 theme-text-muted text-xs mb-2">
                                <TrendingDown className="w-4 h-4" />
                                Best Day
                            </div>
                            <p className="text-lg font-mono font-bold text-purple-400">
                                {data.aggregate.best_day || "N/A"}
                            </p>
                        </div>
                    </div>
                )}

                {/* Chart */}
                {chartData.length > 0 && (
                    <div className="theme-card theme-border border rounded-xl p-6 mb-8">
                        <h2 className="text-lg font-semibold mb-4">
                            Accuracy Over Time
                        </h2>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                                    <XAxis
                                        dataKey="date"
                                        tick={{ fill: "#a1a1aa", fontSize: 11 }}
                                    />
                                    <YAxis
                                        yAxisId="pct"
                                        domain={[0, 100]}
                                        tick={{ fill: "#a1a1aa", fontSize: 11 }}
                                        label={{
                                            value: "Accuracy %",
                                            angle: -90,
                                            position: "insideLeft",
                                            style: { fill: "#71717a", fontSize: 11 },
                                        }}
                                    />
                                    <YAxis
                                        yAxisId="mae"
                                        orientation="right"
                                        tick={{ fill: "#a1a1aa", fontSize: 11 }}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: "#18181b",
                                            border: "1px solid #3f3f46",
                                            borderRadius: 8,
                                        }}
                                    />
                                    <Legend />
                                    <Line
                                        yAxisId="pct"
                                        type="monotone"
                                        dataKey="accuracy"
                                        name="Directional Accuracy %"
                                        stroke="#10b981"
                                        strokeWidth={2}
                                        dot={{ r: 4 }}
                                    />
                                    <Line
                                        yAxisId="mae"
                                        type="monotone"
                                        dataKey="mae"
                                        name="MAE"
                                        stroke="#3b82f6"
                                        strokeWidth={2}
                                        strokeDasharray="5 5"
                                        dot={{ r: 3 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}

                {/* Results Table */}
                {data?.results && data.results.length > 0 && (
                    <div className="theme-card theme-border border rounded-xl p-6">
                        <h2 className="text-lg font-semibold mb-4">Daily Results</h2>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="theme-text-muted">
                                        <th className="text-left p-2">Date</th>
                                        <th className="text-right p-2">Dir. Accuracy</th>
                                        <th className="text-right p-2">MAE</th>
                                        <th className="text-right p-2">Correlation</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.results.map((r, i) => (
                                        <tr key={i} className="border-t theme-border">
                                            <td className="p-2 font-mono">{r.date}</td>
                                            <td
                                                className={`p-2 text-right font-mono ${(r.metrics.directional_accuracy || 0) > 0.5
                                                        ? "text-emerald-400"
                                                        : "text-red-400"
                                                    }`}
                                            >
                                                {r.metrics.directional_accuracy
                                                    ? `${(r.metrics.directional_accuracy * 100).toFixed(0)}%`
                                                    : "-"}
                                            </td>
                                            <td className="p-2 text-right font-mono">
                                                {r.metrics.mae?.toFixed(4) || "-"}
                                            </td>
                                            <td className="p-2 text-right font-mono">
                                                {r.metrics.correlation?.toFixed(3) || "-"}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {loading && (
                    <div className="flex items-center justify-center py-20">
                        <div className="animate-spin w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full" />
                    </div>
                )}
            </div>
        </div>
    );
}
