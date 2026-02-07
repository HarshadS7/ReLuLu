"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import type { BankResult, EdgeResult } from "../../types";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

interface GraphNode {
  id: string;
  hubScore: number;
  predictedScore: number;
  val: number;
}

interface GraphLink {
  source: string;
  target: string;
  weightBefore: number;
  weightAfter: number;
}

export function RiskGraph({
  banks,
  edges,
  mode,
}: {
  banks: BankResult[];
  edges: EdgeResult[];
  mode: "before" | "after";
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 500 });

  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: Math.max(containerRef.current.clientHeight, 500),
        });
      }
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  const maxHub = Math.max(...banks.map((b) => b.hub_score), 0.01);

  const nodes: GraphNode[] = banks.map((b) => ({
    id: b.name,
    hubScore: b.hub_score,
    predictedScore: b.predicted_score,
    val: (b.hub_score / maxHub) * 30 + 8,
  }));

  const links: GraphLink[] = edges.map((e) => ({
    source: e.source,
    target: e.target,
    weightBefore: e.weight_before,
    weightAfter: e.weight_after,
  }));

  const maxWeight = Math.max(
    ...edges.map((e) => (mode === "before" ? e.weight_before : e.weight_after)),
    0.01
  );

  const nodeColor = useCallback(
    (node: GraphNode) => {
      const ratio = node.hubScore / maxHub;
      if (ratio > 0.7) return "#ef4444";
      if (ratio > 0.4) return "#f59e0b";
      return "#22c55e";
    },
    [maxHub]
  );

  const linkWidth = useCallback(
    (link: GraphLink) => {
      const w = mode === "before" ? link.weightBefore : link.weightAfter;
      return Math.max((w / maxWeight) * 6, 0.5);
    },
    [mode, maxWeight]
  );

  const linkColor = useCallback(
    (link: GraphLink) => {
      const w = mode === "before" ? link.weightBefore : link.weightAfter;
      const ratio = w / maxWeight;
      if (ratio > 0.6) return "rgba(239, 68, 68, 0.6)";
      if (ratio > 0.3) return "rgba(245, 158, 11, 0.4)";
      return "rgba(161, 161, 170, 0.2)";
    },
    [mode, maxWeight]
  );

  const nodeLabel = useCallback(
    (node: GraphNode) =>
      `${node.id}\nHub: ${node.hubScore.toFixed(4)}\nSignal: ${(node.predictedScore * 100).toFixed(3)}%`,
    []
  );

  const nodeCanvasObject = useCallback(
    (node: GraphNode & { x?: number; y?: number }, ctx: CanvasRenderingContext2D) => {
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      const r = node.val;
      const color = nodeColor(node);

      // Glow
      ctx.beginPath();
      ctx.arc(x, y, r + 4, 0, 2 * Math.PI);
      ctx.fillStyle =
        color === "#ef4444"
          ? "rgba(239, 68, 68, 0.15)"
          : color === "#f59e0b"
            ? "rgba(245, 158, 11, 0.1)"
            : "rgba(34, 197, 94, 0.08)";
      ctx.fill();

      // Node
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,0.2)";
      ctx.lineWidth = 1;
      ctx.stroke();

      // Label
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#fff";
      ctx.font = `bold ${Math.max(r * 0.7, 8)}px monospace`;
      ctx.fillText(node.id, x, y);
    },
    [nodeColor]
  );

  return (
    <div ref={containerRef} className="w-full h-full min-h-[500px]">
      <ForceGraph2D
        width={dimensions.width}
        height={dimensions.height}
        graphData={{ nodes, links }}
        nodeCanvasObject={nodeCanvasObject as never}
        nodePointerAreaPaint={((node: GraphNode & { x?: number; y?: number }, color: string, ctx: CanvasRenderingContext2D) => {
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, node.val, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }) as never}
        linkWidth={linkWidth as never}
        linkColor={linkColor as never}
        nodeLabel={nodeLabel as never}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={0.9}
        backgroundColor="transparent"
        cooldownTicks={80}
        linkCurvature={0.15}
      />
    </div>
  );
}
