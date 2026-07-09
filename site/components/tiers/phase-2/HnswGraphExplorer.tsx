"use client";

import { useState, useMemo, useCallback } from "react";
import fixtureRaw from "@/lib/tiers/hnsw-fixture.json";

type Metric = "SW₁" | "Cosine" | "L2";

interface Node {
  id: number;
  x: number;
  y: number;
  label: string;
  tags: string[];
}
interface Edge {
  source: number;
  target: number;
}

const fixture = fixtureRaw as { nodes: Node[]; edges: Edge[] };

const PASTEL_BLUE = "#7B9DB5";
const PASTEL_SAGE = "#8FB5A4";

function dist(a: Node, b: Node, metric: Metric): number {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  if (metric === "L2") return Math.sqrt(dx * dx + dy * dy);
  if (metric === "Cosine") {
    const dot = a.x * b.x + a.y * b.y;
    const ma = Math.sqrt(a.x * a.x + a.y * a.y) || 1;
    const mb = Math.sqrt(b.x * b.x + b.y * b.y) || 1;
    return 1 - dot / (ma * mb);
  }
  return Math.abs(dx) + Math.abs(dy);
}

const W = 600;
const H = 360;
function toCanvas(v: number, range = 1.2) {
  return ((v + range) / (2 * range));
}

export default function HnswGraphExplorer() {
  const [metric, setMetric] = useState<Metric>("SW₁");
  const [efSearch, setEfSearch] = useState(50);
  const [query, setQuery] = useState({ x: 0.05, y: 0.05 });
  const [dragging, setDragging] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [k] = useState(5);

  const nodes = fixture.nodes;
  const edges = fixture.edges;

  const sorted = useMemo(
    () =>
      nodes
        .map((n) => ({ n, d: dist(n, query as Node, metric) }))
        .sort((a, b) => a.d - b.d),
    [query, metric, nodes]
  );

  const topK = sorted.slice(0, k).map((s) => s.n.id);
  const candidateSet = sorted.slice(0, efSearch).map((s) => s.n.id);
  const nearestDist = sorted[0]?.d ?? 0;
  const groundTruth = [...sorted].sort((a, b) => a.d - b.d).slice(0, k).map((s) => s.n.id);
  const recall = topK.filter((id) => groundTruth.includes(id)).length / k;

  const handleSvgMove = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      if (!dragging) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width) * 2.4 - 1.2;
      const ny = ((e.clientY - rect.top) / rect.height) * 2.4 - 1.2;
      setQuery({ x: nx, y: ny });
    },
    [dragging]
  );

  return (
    <div className="flex flex-col gap-6">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex gap-1">
          {(["SW₁", "Cosine", "L2"] as Metric[]).map((m) => (
            <button
              key={m}
              onClick={() => setMetric(m)}
              className="font-mono text-[12px] uppercase tracking-[0.1em] px-3 py-1.5 border transition-opacity hover:opacity-70"
              style={{
                borderColor: metric === m ? PASTEL_BLUE : "var(--rule)",
                color: metric === m ? PASTEL_BLUE : "var(--ink-mute)",
              }}
            >
              {m}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <label className="font-mono text-[12px]" style={{ color: "var(--ink-mute)" }}>
            ef_search={efSearch}
          </label>
          <input
            type="range"
            min={10}
            max={Math.min(nodes.length, 200)}
            step={10}
            value={efSearch}
            onChange={(e) => setEfSearch(+e.target.value)}
            className="w-28"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Main canvas */}
        <div className="md:col-span-3">
          <svg
            viewBox={`0 0 ${W} ${H}`}
            className="w-full border"
            style={{
              borderColor: "var(--rule)",
              backgroundColor: "var(--bg-elev)",
              cursor: dragging ? "grabbing" : "grab",
            }}
            onMouseDown={() => setDragging(true)}
            onMouseUp={() => setDragging(false)}
            onMouseLeave={() => setDragging(false)}
            onMouseMove={handleSvgMove}
          >
            {/* Edges */}
            {edges.map((e, i) => {
              const s = nodes[e.source];
              const t = nodes[e.target];
              if (!s || !t) return null;
              const isCand =
                candidateSet.includes(e.source) && candidateSet.includes(e.target);
              return (
                <line
                  key={i}
                  x1={toCanvas(s.x) * W}
                  y1={toCanvas(s.y) * H}
                  x2={toCanvas(t.x) * W}
                  y2={toCanvas(t.y) * H}
                  stroke={isCand ? PASTEL_SAGE : "var(--rule)"}
                  strokeWidth={isCand ? 0.8 : 0.4}
                  opacity={isCand ? 0.5 : 0.2}
                />
              );
            })}

            {/* Nodes */}
            {nodes.map((n) => {
              const cx = toCanvas(n.x) * W;
              const cy = toCanvas(n.y) * H;
              const isTop = topK.includes(n.id);
              const isCand = candidateSet.includes(n.id) && !isTop;
              return (
                <circle
                  key={n.id}
                  cx={cx}
                  cy={cy}
                  r={isTop ? 6 : isCand ? 4 : 3}
                  fill={
                    isTop
                      ? PASTEL_BLUE
                      : isCand
                      ? PASTEL_SAGE
                      : "var(--bg)"
                  }
                  stroke={isTop ? PASTEL_BLUE : "var(--rule)"}
                  strokeWidth={isTop ? 0 : 0.8}
                  style={{ cursor: "pointer", opacity: isCand || isTop ? 1 : 0.5 }}
                  onClick={(e) => { e.stopPropagation(); setSelectedNode(n); }}
                />
              );
            })}

            {/* Query point */}
            <circle
              cx={toCanvas(query.x) * W}
              cy={toCanvas(query.y) * H}
              r={8}
              fill="var(--signal-warm)"
              stroke="var(--bg)"
              strokeWidth={2}
            />
            <text
              x={toCanvas(query.x) * W + 11}
              y={toCanvas(query.y) * H + 4}
              className="font-mono"
              fontSize={10}
              fill="var(--signal-warm)"
            >
              query
            </text>
          </svg>
        </div>

        {/* Side panel */}
        <div className="flex flex-col gap-3">
          {selectedNode ? (
            <div
              className="border p-4 flex flex-col gap-2 font-mono text-[12px]"
              style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)", color: "var(--ink)" }}
            >
              <p style={{ color: PASTEL_BLUE }}>Node #{selectedNode.id.toString(16).toUpperCase().padStart(5, "0")}</p>
              <p style={{ color: "var(--ink-mute)" }}>172-d point cloud</p>
              <p>label: <strong>{selectedNode.label}</strong></p>
              <p>tags: [{selectedNode.tags.join(", ")}]</p>
              <p style={{ color: "var(--ink-mute)" }}>
                {metric} dist to query:{" "}
                <span style={{ color: "var(--ink)" }}>
                  {dist(selectedNode, query as Node, metric).toFixed(4)}
                </span>
              </p>
              <button
                onClick={() => setSelectedNode(null)}
                className="mt-2 text-[11px] uppercase tracking-[0.1em]"
                style={{ color: "var(--ink-mute)" }}
              >
                close
              </button>
            </div>
          ) : (
            <div
              className="border p-4 font-mono text-[12px]"
              style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)", color: "var(--ink-mute)" }}
            >
              Click a node to inspect it.
            </div>
          )}
        </div>
      </div>

      {/* Bottom rail */}
      <div
        className="grid grid-cols-2 md:grid-cols-4 gap-4 border p-4 font-mono text-[12px]"
        style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}
      >
        <div>
          <p style={{ color: "var(--ink-mute)" }}>Metric</p>
          <p style={{ color: PASTEL_BLUE }}>{metric}</p>
        </div>
        <div>
          <p style={{ color: "var(--ink-mute)" }}>Candidates eval.</p>
          <p style={{ color: "var(--ink)" }}>{Math.min(efSearch, nodes.length)}</p>
        </div>
        <div>
          <p style={{ color: "var(--ink-mute)" }}>Nearest dist.</p>
          <p style={{ color: "var(--ink)" }}>{nearestDist.toFixed(4)}</p>
        </div>
        <div>
          <p style={{ color: "var(--ink-mute)" }}>Recall@{k}</p>
          <p style={{ color: recall === 1 ? PASTEL_BLUE : "var(--signal-warm)" }}>
            {(recall * 100).toFixed(0)}%
          </p>
        </div>
      </div>
    </div>
  );
}
