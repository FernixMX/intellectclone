"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import type { NodoCoautoria, AristaCoautoria } from "@/types";

// D3 simulation node shape
interface SimNode extends d3.SimulationNodeDatum {
  persona_id: string;
  nombre_completo: string;
  dependencia_id: string | null;
  grado: number;
}

interface SimEdge extends d3.SimulationLinkDatum<SimNode> {
  n_papers_comunes: number;
}

const PALETTE = [
  "#0d6efd",
  "#02c27a",
  "#fd7e14",
  "#6c757d",
  "#8b5cf6",
  "#0dcaf0",
  "#fc185a",
  "#ffc107",
];

function depColor(depId: string | null): string {
  if (!depId) return "#94a3b8";
  let h = 0;
  for (let i = 0; i < depId.length; i++) h = (h * 31 + depId.charCodeAt(i)) & 0xffff;
  return PALETTE[h % PALETTE.length];
}

function initials(name: string): string {
  return name
    .split(" ")
    .filter((w) => /^[A-ZÁÉÍÓÚÑ]/u.test(w))
    .slice(0, 2)
    .map((w) => w[0])
    .join("");
}

interface GraphProps {
  nodos: NodoCoautoria[];
  aristas: AristaCoautoria[];
  selected: string | null;
  onSelect: (id: string | null) => void;
}

function NetworkGraph({ nodos, aristas, selected, onSelect }: GraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);

  const zoomIn = useCallback(() => {
    if (svgRef.current && zoomRef.current)
      d3.select(svgRef.current).transition().call(zoomRef.current.scaleBy, 1.4);
  }, []);

  const zoomOut = useCallback(() => {
    if (svgRef.current && zoomRef.current)
      d3.select(svgRef.current).transition().call(zoomRef.current.scaleBy, 0.7);
  }, []);

  const zoomReset = useCallback(() => {
    if (svgRef.current && zoomRef.current)
      d3.select(svgRef.current).transition().call(zoomRef.current.transform, d3.zoomIdentity);
  }, []);

  useEffect(() => {
    if (!svgRef.current || !nodos.length) return;
    const container = svgRef.current.parentElement!;
    const W = container.clientWidth;
    const H = container.clientHeight;

    d3.select(svgRef.current).selectAll("*").remove();

    const rScale = d3
      .scaleLinear()
      .domain([d3.min(nodos, (d) => d.grado) ?? 1, d3.max(nodos, (d) => d.grado) ?? 10])
      .range([8, 22]);

    const wScale = d3
      .scaleLinear()
      .domain([1, d3.max(aristas, (d) => d.n_papers_comunes) ?? 10])
      .range([1, 4]);

    const svg = d3.select(svgRef.current).attr("width", W).attr("height", H);
    const g = svg.append("g");

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on("zoom", (e) => g.attr("transform", String(e.transform)));
    svg.call(zoom);
    zoomRef.current = zoom;

    const simNodes: SimNode[] = nodos.map((d) => ({ ...d }));
    const nodeById = Object.fromEntries(simNodes.map((d) => [d.persona_id, d]));

    const simEdges: SimEdge[] = aristas
      .filter((a) => nodeById[a.persona_a_id] && nodeById[a.persona_b_id])
      .map((a) => ({
        source: nodeById[a.persona_a_id],
        target: nodeById[a.persona_b_id],
        n_papers_comunes: a.n_papers_comunes,
      }));

    const sim = d3
      .forceSimulation(simNodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimEdge>(simEdges)
          .id((d) => d.persona_id)
          .distance(90)
      )
      .force("charge", d3.forceManyBody().strength(-220))
      .force("center", d3.forceCenter(W / 2, H / 2))
      .force(
        "collision",
        d3.forceCollide<SimNode>((d) => rScale(d.grado) + 5)
      );

    const link = g
      .append("g")
      .selectAll("line")
      .data(simEdges)
      .join("line")
      .attr("stroke", "#dde3ef")
      .attr("stroke-opacity", 0.8)
      .attr("stroke-width", (d) => wScale(d.n_papers_comunes));

    const node = g
      .append("g")
      .selectAll<SVGGElement, SimNode>("g")
      .data(simNodes)
      .join("g")
      .attr("cursor", "pointer")
      .on("click", (e, d) => {
        e.stopPropagation();
        onSelect(d.persona_id === selected ? null : d.persona_id);
      })
      .call(
        d3
          .drag<SVGGElement, SimNode>()
          .on("start", (e, d) => {
            if (!e.active) sim.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (e, d) => {
            d.fx = e.x;
            d.fy = e.y;
          })
          .on("end", (e, d) => {
            if (!e.active) sim.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    node
      .append("circle")
      .attr("r", (d) => rScale(d.grado))
      .attr("fill", (d) =>
        d.persona_id === selected ? "var(--blue-light)" : depColor(d.dependencia_id) + "22"
      )
      .attr("stroke", (d) =>
        d.persona_id === selected ? "var(--blue)" : depColor(d.dependencia_id)
      )
      .attr("stroke-width", (d) => (d.persona_id === selected ? 2.5 : 1.5));

    node
      .append("text")
      .text((d) => initials(d.nombre_completo))
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .attr("font-size", (d) => Math.max(7, rScale(d.grado) * 0.55))
      .attr("font-family", "var(--font-sans)")
      .attr("font-weight", "600")
      .attr("fill", (d) => (d.persona_id === selected ? "var(--blue)" : depColor(d.dependencia_id)))
      .attr("pointer-events", "none");

    svg.on("click", () => onSelect(null));

    sim.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);
      node.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => {
      sim.stop();
    };
  }, [nodos, aristas, selected, onSelect]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <svg ref={svgRef} className="net-svg" />
      <div className="net-controls">
        <button className="ctrl-btn" onClick={zoomIn} title="Acercar">
          +
        </button>
        <button className="ctrl-btn" onClick={zoomOut} title="Alejar">
          −
        </button>
        <button className="ctrl-btn" onClick={zoomReset} title="Restablecer">
          ⊡
        </button>
      </div>
    </div>
  );
}

export default function RedPage() {
  const [nodos, setNodos] = useState<NodoCoautoria[]>([]);
  const [aristas, setAristas] = useState<AristaCoautoria[]>([]);
  const [totalNodos, setTotalNodos] = useState(0);
  const [totalAristas, setTotalAristas] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .redCoautoria({ limite_nodos: 100 })
      .then((data) => {
        setNodos(data.nodos);
        setAristas(data.aristas);
        setTotalNodos(data.total_nodos);
        setTotalAristas(data.total_aristas);
        if (data.nodos.length > 0) setSelected(data.nodos[0].persona_id);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al cargar la red"))
      .finally(() => setLoading(false));
  }, []);

  const selNode = nodos.find((n) => n.persona_id === selected) ?? null;
  const selEdges = aristas.filter(
    (a) => a.persona_a_id === selected || a.persona_b_id === selected
  );

  // Unique dependencias for legend
  const uniqueDeps = Array.from(new Set(nodos.map((n) => n.dependencia_id))).slice(0, 8);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <Header />
      <div className="net-body">
        {/* Canvas */}
        <div className="net-canvas">
          {loading && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "#f8fafc",
                fontSize: 14,
                color: "var(--text-muted)",
              }}
            >
              Cargando red de coautoría…
            </div>
          )}
          {error && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "#f8fafc",
                fontSize: 14,
                color: "var(--red)",
              }}
            >
              {error}
            </div>
          )}
          {!loading && !error && (
            <NetworkGraph
              nodos={nodos}
              aristas={aristas}
              selected={selected}
              onSelect={setSelected}
            />
          )}
        </div>

        {/* Side panel */}
        <aside className="net-panel">
          {/* Stats */}
          <div className="panel-sec">
            <div className="panel-sec-title">Red global</div>
            <div style={{ display: "flex", gap: 20 }}>
              <div className="person-stat">
                <div className="person-stat-val">{totalNodos.toLocaleString("es-MX")}</div>
                <div className="person-stat-lbl">nodos</div>
              </div>
              <div className="person-stat">
                <div className="person-stat-val">{totalAristas.toLocaleString("es-MX")}</div>
                <div className="person-stat-lbl">aristas</div>
              </div>
            </div>
          </div>

          {/* Dep legend */}
          <div className="panel-sec">
            <div className="panel-sec-title">Dependencias</div>
            {uniqueDeps.map((depId, i) => (
              <div key={depId ?? `null-${i}`} className="legend-row">
                <div className="legend-dot" style={{ background: depColor(depId) }} />
                <div className="legend-lbl">{depId ? depId.slice(-8) : "Sin dependencia"}</div>
              </div>
            ))}
          </div>

          {/* Selected node */}
          <div className="panel-sec" style={{ flex: 1 }}>
            <div className="panel-sec-title">
              {selNode ? "Seleccionado" : "Haz clic en un nodo"}
            </div>
            {selNode && (
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: "50%",
                      background: depColor(selNode.dependencia_id) + "22",
                      border: `2px solid ${depColor(selNode.dependencia_id)}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 14,
                      fontWeight: 700,
                      color: depColor(selNode.dependencia_id),
                      flexShrink: 0,
                    }}
                  >
                    {initials(selNode.nombre_completo)}
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                      {selNode.nombre_completo}
                    </div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {selNode.dependencia_id
                        ? `Dep. ${selNode.dependencia_id.slice(-8)}`
                        : "Sin dependencia"}
                    </div>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div className="person-stat">
                    <div className="person-stat-val">{selNode.grado}</div>
                    <div className="person-stat-lbl">conexiones</div>
                  </div>
                  <div className="person-stat">
                    <div className="person-stat-val">{selEdges.length}</div>
                    <div className="person-stat-lbl">coautorías</div>
                  </div>
                </div>

                {selEdges.length > 0 && (
                  <div>
                    <div
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        textTransform: "uppercase",
                        letterSpacing: "0.08em",
                        color: "var(--text-muted)",
                        marginBottom: 8,
                      }}
                    >
                      Colabora con
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {selEdges.slice(0, 8).map((e) => {
                        const otherId =
                          e.persona_a_id === selected ? e.persona_b_id : e.persona_a_id;
                        const other = nodos.find((n) => n.persona_id === otherId);
                        return (
                          <div
                            key={otherId}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 8,
                              cursor: "pointer",
                            }}
                            onClick={() => setSelected(otherId)}
                          >
                            <div
                              style={{
                                width: 24,
                                height: 24,
                                borderRadius: "50%",
                                background: depColor(other?.dependencia_id ?? null) + "22",
                                border: `1.5px solid ${depColor(other?.dependencia_id ?? null)}`,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontSize: 9,
                                fontWeight: 700,
                                color: depColor(other?.dependencia_id ?? null),
                                flexShrink: 0,
                              }}
                            >
                              {initials(other?.nombre_completo ?? "")}
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div
                                style={{
                                  fontSize: 12,
                                  color: "var(--text-primary)",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                }}
                              >
                                {other?.nombre_completo ?? otherId.slice(-8)}
                              </div>
                            </div>
                            <span
                              style={{
                                fontFamily: "var(--font-mono)",
                                fontSize: 11,
                                color: "var(--text-muted)",
                                flexShrink: 0,
                              }}
                            >
                              ×{e.n_papers_comunes}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
