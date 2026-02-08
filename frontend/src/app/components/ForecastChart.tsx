"use client";

import { useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";
import type { HorizonSnapshot } from "../types";

interface Props {
  horizons: HorizonSnapshot[];
  selected: number;
  onSelect: (idx: number) => void;
}

export function ForecastChart({ horizons, selected, onSelect }: Props) {
  const chartData = useMemo(
    () =>
      horizons.map((h, idx) => ({
        name: `T+${h.horizon}`,
        idx,
        stability: +h.stability.toFixed(4),
        payloadReduction: +h.payload_reduction.toFixed(2),
        riskAdjReduction: +h.risk_adjusted_payload_reduction.toFixed(2),
        worstCaseReduction: +h.worst_case_payload_reduction.toFixed(2),
        rawLoad: +h.raw_load.toFixed(2),
        netLoad: +h.net_load.toFixed(2),
        riskAdjLoad: +h.risk_adjusted_net_load.toFixed(2),
        worstCaseLoad: +h.worst_case_net_load.toFixed(2),
        riskBuffer: +h.risk_buffer.toFixed(2),
        worstCaseBuffer: +h.worst_case_buffer.toFixed(2),
        isStable: h.is_stable,
      })),
    [horizons],
  );

  const handleClick = (data: Record<string, unknown> | null) => {
    if (data && typeof data.idx === "number") onSelect(data.idx);
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <h2 className="mb-1 text-sm font-semibold text-zinc-300">
        Forecast Timeline — Settlement Sizing Across Horizons
      </h2>
      <p className="mb-4 text-[11px] text-zinc-500">
        Click any bar to inspect that horizon. Lines show how much money is
        actually needed after netting + risk buffers.
      </p>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 5, right: 20, bottom: 5, left: 10 }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            onClick={(e: any) => e?.activePayload && handleClick(e.activePayload[0]?.payload)}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis
              dataKey="name"
              tick={{ fill: "#a1a1aa", fontSize: 12 }}
              axisLine={{ stroke: "#3f3f46" }}
              tickLine={false}
            />
            <YAxis
              yAxisId="money"
              tick={{ fill: "#a1a1aa", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              label={{
                value: "Settlement ($)",
                angle: -90,
                position: "insideLeft",
                style: { fill: "#71717a", fontSize: 11 },
              }}
            />
            <YAxis
              yAxisId="pct"
              orientation="right"
              domain={[0, 100]}
              tick={{ fill: "#a1a1aa", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              label={{
                value: "Reduction %",
                angle: 90,
                position: "insideRight",
                style: { fill: "#71717a", fontSize: 11 },
              }}
            />

            <Tooltip
              contentStyle={{
                backgroundColor: "#18181b",
                border: "1px solid #3f3f46",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: "#e4e4e7", fontWeight: 600 }}
              itemStyle={{ padding: "2px 0" }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any, name: any) => {
                const labels: Record<string, string> = {
                  rawLoad: "Gross Obligations",
                  netLoad: "After Netting",
                  riskAdjLoad: "Risk-Adjusted Req",
                  worstCaseLoad: "Worst-Case Req",
                  payloadReduction: "Netting Reduction",
                  riskAdjReduction: "Risk-Adj Reduction",
                  worstCaseReduction: "Worst-Case Reduction",
                };
                const unit = name.includes("Reduction") ? "%" : "";
                return [`${value}${unit}`, labels[name] || name];
              }}
            />

            <Legend
              wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
              formatter={(value: string) => {
                const labels: Record<string, string> = {
                  rawLoad: "Gross Obligations",
                  netLoad: "After Netting",
                  riskAdjLoad: "Risk-Adjusted Req",
                  worstCaseLoad: "Worst-Case Req",
                  payloadReduction: "Netting %",
                  riskAdjReduction: "Risk-Adj %",
                  worstCaseReduction: "Worst-Case %",
                };
                return labels[value] || value;
              }}
            />

            {/* Bars: settlement money */}
            <Bar
              yAxisId="money"
              dataKey="rawLoad"
              fill="#52525b"
              radius={[4, 4, 0, 0]}
              barSize={28}
              opacity={0.5}
            />
            <Bar
              yAxisId="money"
              dataKey="netLoad"
              fill="#22c55e"
              radius={[4, 4, 0, 0]}
              barSize={28}
            />
            <Bar
              yAxisId="money"
              dataKey="riskAdjLoad"
              fill="#f59e0b"
              radius={[4, 4, 0, 0]}
              barSize={28}
            />
            <Bar
              yAxisId="money"
              dataKey="worstCaseLoad"
              fill="#ef4444"
              radius={[4, 4, 0, 0]}
              barSize={28}
            />

            {/* Lines: reduction percentages */}
            <Line
              yAxisId="pct"
              type="monotone"
              dataKey="payloadReduction"
              stroke="#4ade80"
              strokeWidth={2}
              dot={{ r: 5, fill: "#4ade80", strokeWidth: 0 }}
              activeDot={{ r: 7 }}
            />
            <Line
              yAxisId="pct"
              type="monotone"
              dataKey="riskAdjReduction"
              stroke="#fbbf24"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={{ r: 4, fill: "#fbbf24", strokeWidth: 0 }}
            />
            <Line
              yAxisId="pct"
              type="monotone"
              dataKey="worstCaseReduction"
              stroke="#f87171"
              strokeWidth={2}
              strokeDasharray="3 3"
              dot={{ r: 4, fill: "#f87171", strokeWidth: 0 }}
            />

            {/* Selected horizon indicator */}
            {chartData[selected] && (
              <ReferenceLine
                yAxisId="money"
                x={chartData[selected].name}
                stroke="#a78bfa"
                strokeWidth={2}
                strokeDasharray="4 2"
                label={{
                  value: "▼ selected",
                  position: "top",
                  fill: "#a78bfa",
                  fontSize: 10,
                }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Mini legend for context */}
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-[10px] text-zinc-500">
        <span>
          <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-zinc-500" />
          Gross = total obligations before netting
        </span>
        <span>
          <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-green-500" />
          Netted = money needed after cycle-cancellation
        </span>
        <span>
          <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-amber-500" />
          Risk-Adj = netted + risk buffer (riskᵢ × outflowᵢ)
        </span>
        <span>
          <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-red-500" />
          Worst-Case = netted + full outflow of top-risk banks
        </span>
      </div>
    </div>
  );
}
