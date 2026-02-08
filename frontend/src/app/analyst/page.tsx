"use client";

import React, { useState, useEffect } from "react";
import axios from "axios";
import Link from "next/link";
import { ArrowLeft, RefreshCw, AlertTriangle, CheckCircle, Activity } from "lucide-react";
import {
    ResponsiveContainer,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    Legend,
    Tooltip,
} from "recharts";
import { useTheme } from "@/context/ThemeContext";

interface AnalystResponse {
    risk_assessment: string;
    status: string;
}

interface ForecastResponse {
    horizons: Array<{
        horizon: number;
        banks: Array<{
            name: string;
            predicted_score: number;
            hub_score: number;
            risk_factor: number;
        }>;
        stability: number;
        is_stable: boolean;
        payload_reduction: number;
    }>;
}

export default function AnalystPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [data, setData] = useState<AnalystResponse | null>(null);
    const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [analystRes, forecastRes] = await Promise.all([
                axios.get<AnalystResponse>(`http://localhost:8000/api/analyst/risk?horizon=1`),
                axios.get<ForecastResponse>(`http://localhost:8000/api/forecast`),
            ]);
            setData(analystRes.data);
            setForecastData(forecastRes.data);
        } catch (err: any) {
            console.error("Failed to fetch analyst data", err);
            setError(
                err.response?.data?.detail || "Failed to connect to the AI Analyst service."
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    // Prepare radar chart data from forecast
    const radarData = forecastData?.horizons[0]?.banks.map((bank) => ({
        name: bank.name,
        hubScore: +(bank.hub_score * 100).toFixed(1),
        riskFactor: +(bank.risk_factor * 100).toFixed(1),
        signal: +Math.abs(bank.predicted_score * 100).toFixed(2),
    })) || [];

    // Chart colors
    const polarGridStroke = isDark ? "#3f3f46" : "#e4e4e7";
    const tickFill = isDark ? "#a1a1aa" : "#71717a";
    const tooltipBg = isDark ? "#18181b" : "#ffffff";
    const tooltipBorder = isDark ? "#3f3f46" : "#e4e4e7";

    return (
        <div className="min-h-screen theme-bg-primary theme-text-primary p-8 font-sans transition-colors duration-300">
            <div className="max-w-5xl mx-auto">
                <header className="mb-8 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/"
                            className="p-2 rounded-full hover:theme-bg-tertiary transition-colors"
                        >
                            <ArrowLeft className="w-6 h-6 theme-text-muted" />
                        </Link>
                        <div>
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                                Systemic Risk Analyst
                            </h1>
                            <p className="theme-text-muted text-sm mt-1">
                                AI-powered assessment of interbank network stability (T+1)
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={fetchData}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 theme-bg-tertiary hover:opacity-80 rounded-lg transition-all disabled:opacity-50 theme-text-primary"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                        {loading ? "Analyzing..." : "Refresh Analysis"}
                    </button>
                </header>

                {/* Main Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Left: Risk Assessment Text */}
                    <div className="theme-card border theme-border rounded-xl p-6 shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />

                        {error ? (
                            <div className="flex flex-col items-center justify-center py-12 text-red-400">
                                <AlertTriangle className="w-12 h-12 mb-4 opacity-80" />
                                <p className="text-lg font-medium">Analysis Unavailable</p>
                                <p className="text-sm opacity-70 mt-2 text-center max-w-md">
                                    {error}
                                </p>
                                <button
                                    onClick={fetchData}
                                    className="mt-6 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                                >
                                    Try Again
                                </button>
                            </div>
                        ) : loading ? (
                            <div className="flex flex-col items-center justify-center py-20">
                                <div className="relative w-16 h-16">
                                    <div className="absolute inset-0 border-t-2 border-blue-500 rounded-full animate-spin"></div>
                                    <div className="absolute inset-2 border-t-2 border-purple-500 rounded-full animate-spin animation-delay-150"></div>
                                </div>
                                <p className="mt-6 theme-text-muted animate-pulse">
                                    Generating risk assessment...
                                </p>
                            </div>
                        ) : (
                            <div className="prose prose-sm max-w-none theme-text-secondary">
                                <div className="flex items-start gap-4 mb-6">
                                    <div className="p-3 bg-green-500/10 rounded-lg">
                                        <CheckCircle className="w-6 h-6 text-green-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-semibold theme-text-primary m-0">
                                            Assessment Complete
                                        </h3>
                                        <p className="theme-text-muted text-sm m-0 mt-1">
                                            Based on latest forecast data for T+1
                                        </p>
                                    </div>
                                </div>

                                <div className="theme-bg-secondary rounded-lg p-6 border theme-border leading-relaxed theme-text-secondary max-h-[400px] overflow-y-auto whitespace-pre-wrap">
                                    {data?.risk_assessment}
                                </div>

                                {data?.status === "error" && (
                                    <div className="mt-4 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-yellow-600 dark:text-yellow-200 text-sm flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 shrink-0" />
                                        <p>The AI service reported an issue with the generation process.</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Right: Radar Chart */}
                    <div className="theme-card border theme-border rounded-xl p-6 shadow-2xl">
                        <div className="flex items-center gap-2 mb-4">
                            <Activity className="w-5 h-5 text-purple-400" />
                            <h2 className="text-lg font-semibold theme-text-primary">
                                Bank Risk Profile — T+1
                            </h2>
                        </div>

                        {radarData.length > 0 ? (
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadarChart data={radarData}>
                                        <PolarGrid stroke={polarGridStroke} />
                                        <PolarAngleAxis
                                            dataKey="name"
                                            tick={{ fill: tickFill, fontSize: 11 }}
                                        />
                                        <PolarRadiusAxis
                                            angle={30}
                                            domain={[0, 100]}
                                            tick={{ fill: tickFill, fontSize: 10 }}
                                        />
                                        <Radar
                                            name="Hub Score"
                                            dataKey="hubScore"
                                            stroke="#8b5cf6"
                                            fill="#8b5cf6"
                                            fillOpacity={0.3}
                                        />
                                        <Radar
                                            name="Risk Factor"
                                            dataKey="riskFactor"
                                            stroke="#ef4444"
                                            fill="#ef4444"
                                            fillOpacity={0.2}
                                        />
                                        <Legend
                                            wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
                                        />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: tooltipBg,
                                                border: `1px solid ${tooltipBorder}`,
                                                borderRadius: 8,
                                                fontSize: 12,
                                                color: isDark ? "#fff" : "#000"
                                            }}
                                        />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-80 theme-text-muted">
                                <p>Loading chart data...</p>
                            </div>
                        )}

                        {/* Quick stats */}
                        {forecastData?.horizons[0] && (
                            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                                <div className="theme-bg-secondary rounded-lg p-3 border theme-border">
                                    <p className="theme-text-muted text-xs">Stability Index</p>
                                    <p className={`text-lg font-mono font-semibold ${forecastData.horizons[0].is_stable ? "text-green-500" : "text-red-500"}`}>
                                        {forecastData.horizons[0].stability.toFixed(4)}
                                    </p>
                                </div>
                                <div className="theme-bg-secondary rounded-lg p-3 border theme-border">
                                    <p className="theme-text-muted text-xs">Payload Reduction</p>
                                    <p className="text-lg font-mono font-semibold text-blue-400">
                                        {forecastData.horizons[0].payload_reduction.toFixed(1)}%
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
