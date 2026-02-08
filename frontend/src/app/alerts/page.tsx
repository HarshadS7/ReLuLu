"use client";

import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import Link from "next/link";
import {
    ArrowLeft,
    Bell,
    BellRing,
    Plus,
    Trash2,
    CheckCircle,
    AlertTriangle,
    RefreshCw,
} from "lucide-react";

interface AlertConfig {
    id: string;
    type: string;
    name: string;
    description: string;
    threshold: number;
    enabled: boolean;
    created_at: string;
}

interface AlertTriggered {
    id: string;
    type: string;
    name: string;
    message: string;
    triggered_at: string;
    current_value: number | null;
}

export default function AlertsPage() {
    const [alerts, setAlerts] = useState<AlertConfig[]>([]);
    const [triggered, setTriggered] = useState<AlertTriggered[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);

    // New alert form
    const [newAlert, setNewAlert] = useState({
        type: "stability_threshold",
        name: "",
        threshold: 1.0,
        description: "",
    });

    const fetchAlerts = useCallback(async () => {
        try {
            const [alertsRes, triggeredRes] = await Promise.all([
                axios.get<AlertConfig[]>("http://localhost:8000/api/alerts"),
                axios.get<AlertTriggered[]>("http://localhost:8000/api/alerts/triggered"),
            ]);
            setAlerts(alertsRes.data);
            setTriggered(triggeredRes.data);
        } catch (err) {
            console.error("Failed to fetch alerts", err);
        } finally {
            setLoading(false);
        }
    }, []);

    const checkAlerts = async () => {
        try {
            await axios.post("http://localhost:8000/api/alerts/check");
            fetchAlerts();
        } catch (err) {
            console.error("Failed to check alerts", err);
        }
    };

    const createAlert = async () => {
        if (!newAlert.name) return;
        try {
            await axios.post("http://localhost:8000/api/alerts", {
                ...newAlert,
                enabled: true,
            });
            setShowCreate(false);
            setNewAlert({ type: "stability_threshold", name: "", threshold: 1.0, description: "" });
            fetchAlerts();
        } catch (err) {
            console.error("Failed to create alert", err);
        }
    };

    const deleteAlert = async (id: string) => {
        try {
            await axios.delete(`http://localhost:8000/api/alerts/${id}`);
            fetchAlerts();
        } catch (err) {
            console.error("Failed to delete alert", err);
        }
    };

    useEffect(() => {
        fetchAlerts();
    }, [fetchAlerts]);

    return (
        <div className="min-h-screen theme-bg-primary theme-text-primary p-8 font-sans transition-colors duration-300">
            <div className="max-w-4xl mx-auto">
                <header className="mb-8 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/"
                            className="p-2 rounded-full hover:theme-bg-tertiary transition-colors"
                        >
                            <ArrowLeft className="w-6 h-6 theme-text-muted" />
                        </Link>
                        <div>
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
                                Alert Configuration
                            </h1>
                            <p className="theme-text-muted text-sm mt-1">
                                Set up notifications for risk thresholds
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={checkAlerts}
                            className="flex items-center gap-2 px-4 py-2 theme-bg-tertiary hover:opacity-80 rounded-lg transition-all"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Check Now
                        </button>
                        <button
                            onClick={() => setShowCreate(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-lg transition-all text-white"
                        >
                            <Plus className="w-4 h-4" />
                            New Alert
                        </button>
                    </div>
                </header>

                {/* Triggered Alerts */}
                {triggered.length > 0 && (
                    <div className="mb-8">
                        <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
                            <BellRing className="w-5 h-5 text-red-400" />
                            Triggered Alerts ({triggered.length})
                        </h2>
                        <div className="space-y-3">
                            {triggered.map((t) => (
                                <div
                                    key={`${t.id}-${t.triggered_at}`}
                                    className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg"
                                >
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <p className="font-medium text-red-400">{t.name}</p>
                                            <p className="text-sm theme-text-muted mt-1">{t.message}</p>
                                        </div>
                                        <span className="text-xs theme-text-muted">
                                            {new Date(t.triggered_at).toLocaleString()}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Configured Alerts */}
                <div className="mb-8">
                    <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
                        <Bell className="w-5 h-5" />
                        Configured Alerts
                    </h2>
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full" />
                        </div>
                    ) : alerts.length === 0 ? (
                        <div className="text-center py-12 theme-text-muted">
                            <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
                            <p>No alerts configured</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {alerts.map((alert) => (
                                <div
                                    key={alert.id}
                                    className="theme-card theme-border border rounded-lg p-4 flex items-center justify-between"
                                >
                                    <div className="flex items-center gap-4">
                                        <div
                                            className={`p-2 rounded-lg ${alert.enabled ? "bg-green-500/10" : "bg-zinc-700/50"
                                                }`}
                                        >
                                            {alert.enabled ? (
                                                <CheckCircle className="w-5 h-5 text-green-400" />
                                            ) : (
                                                <AlertTriangle className="w-5 h-5 theme-text-muted" />
                                            )}
                                        </div>
                                        <div>
                                            <p className="font-medium">{alert.name}</p>
                                            <p className="text-sm theme-text-muted">
                                                {alert.type.replace("_", " ")} • Threshold: {alert.threshold}
                                            </p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => deleteAlert(alert.id)}
                                        className="p-2 hover:bg-red-500/10 rounded-lg transition-colors group"
                                    >
                                        <Trash2 className="w-4 h-4 theme-text-muted group-hover:text-red-400" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Create Alert Modal */}
                {showCreate && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <div className="theme-card theme-border border rounded-xl p-6 w-full max-w-md">
                            <h3 className="text-lg font-semibold mb-4">Create New Alert</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm theme-text-muted mb-1">Alert Type</label>
                                    <select
                                        value={newAlert.type}
                                        onChange={(e) => setNewAlert({ ...newAlert, type: e.target.value })}
                                        className="w-full theme-bg-secondary theme-text-primary theme-border border rounded-lg px-3 py-2"
                                    >
                                        <option value="stability_threshold">Stability Threshold</option>
                                        <option value="payload_change">Payload Change</option>
                                        <option value="hub_shift">Hub Shift</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm theme-text-muted mb-1">Name</label>
                                    <input
                                        type="text"
                                        value={newAlert.name}
                                        onChange={(e) => setNewAlert({ ...newAlert, name: e.target.value })}
                                        className="w-full theme-bg-secondary theme-text-primary theme-border border rounded-lg px-3 py-2"
                                        placeholder="My Alert"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm theme-text-muted mb-1">Threshold</label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={newAlert.threshold}
                                        onChange={(e) => setNewAlert({ ...newAlert, threshold: parseFloat(e.target.value) })}
                                        className="w-full theme-bg-secondary theme-text-primary theme-border border rounded-lg px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm theme-text-muted mb-1">Description (optional)</label>
                                    <input
                                        type="text"
                                        value={newAlert.description}
                                        onChange={(e) => setNewAlert({ ...newAlert, description: e.target.value })}
                                        className="w-full theme-bg-secondary theme-text-primary theme-border border rounded-lg px-3 py-2"
                                        placeholder="Triggers when..."
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    onClick={() => setShowCreate(false)}
                                    className="px-4 py-2 theme-bg-tertiary rounded-lg hover:opacity-80"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={createAlert}
                                    className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-500"
                                >
                                    Create Alert
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
