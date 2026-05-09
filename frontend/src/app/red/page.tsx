"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import * as d3 from "d3";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import type { NodoCoautoria, AristaCoautoria, Dependencia } from "@/types";

interface SimNode extends d3.SimulationNodeDatum {
  persona_id: string;
  nombre_completo: string;
  dependencia_id: string | null;
  grado: number;
  es_externo: boolean;
}

interface SimEdge extends d3.SimulationLinkDatum<SimNode> {
  n_papers_comunes: number;
}

const PALETTE = [
  "#0d6efd",
  "#02c27a",
  "#fd7e14",
  "#8b5cf6",
  "#0dcaf0",
  "#fc185a",
  "#ffc107",
  "#20c997",
];

function depColor(depId: string | null, depOrder: Map<string, number>): string {
  if (!depId) return "#94a3b8";
  const idx = depOrder.get(depId);
  if (idx !== undefined) return PALETTE[idx % PALETTE.length];
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
  depOrder: Map<string, number>;
  isFiltered: boolean;
  onNavigate: (id: string) => void;
}

function NetworkGraph({ nodos, aristas, depOrder, isFiltered, onNavigate }: GraphProps) {
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

    const svgEl = svgRef.current;
    const rect = svgEl.getBoundingClientRect();
    const W = rect.width > 0 ? rect.width : window.innerWidth - 280;
    const H = rect.height > 0 ? rect.height : window.innerHeight - 60;

    d3.select(svgEl).selectAll("*").remove();

    const rScale = d3
      .scaleLinear()
      .domain([d3.min(nodos, (d) => d.grado) ?? 1, d3.max(nodos, (d) => d.grado) ?? 10])
      .range([7, 22]);

    const wScale = d3
      .scaleLinear()
      .domain([1, d3.max(aristas, (d) => d.n_papers_comunes) ?? 10])
      .range([1, 4]);

    const svg = d3.select(svgEl).attr("width", W).attr("height", H);
    const g = svg.append("g");

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.15, 5])
      .on("zoom", (e) => g.attr("transform", String(e.transform)));
    svg.call(zoom);
    zoomRef.current = zoom;

    const simNodes: SimNode[] = nodos.map((d) => ({
      ...d,
      es_externo: d.es_externo ?? false,
    }));
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
          .distance(80)
      )
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(W / 2, H / 2))
      .force(
        "collision",
        d3.forceCollide<SimNode>((d) => rScale(d.grado) + 4)
      );

    // Edge color: lighter when connecting to an external node in filtered mode
    g.append("g")
      .selectAll("line")
      .data(simEdges)
      .join("line")
      .attr("stroke", (d) => {
        const src = d.source as SimNode;
        const tgt = d.target as SimNode;
        return src.es_externo || tgt.es_externo ? "#e2e8f0" : "#dde3ef";
      })
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
        onNavigate(d.persona_id);
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
      .attr("fill", (d) => {
        if (d.es_externo) return "#e2e8f0";
        const color = depColor(d.dependencia_id, depOrder);
        return isFiltered ? color : color + "33";
      })
      .attr("stroke", (d) => (d.es_externo ? "#94a3b8" : depColor(d.dependencia_id, depOrder)))
      .attr("stroke-width", (d) => (d.es_externo ? 1 : isFiltered ? 2 : 1.5));

    node
      .append("text")
      .text((d) => initials(d.nombre_completo))
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .attr("font-size", (d) => Math.max(6, rScale(d.grado) * 0.55))
      .attr("font-family", "var(--font-sans)")
      .attr("font-weight", "600")
      .attr("fill", (d) => (d.es_externo ? "#94a3b8" : depColor(d.dependencia_id, depOrder)))
      .attr("pointer-events", "none");

    node.append("title").text((d) => `${d.nombre_completo} — ${d.grado} papers`);

    const linkSel = g.selectAll<SVGLineElement, SimEdge>("line");

    sim.on("tick", () => {
      linkSel
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);
      node.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => {
      sim.stop();
    };
  }, [nodos, aristas, depOrder, isFiltered, onNavigate]);

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
  const router = useRouter();
  const [nodos, setNodos] = useState<NodoCoautoria[]>([]);
  const [aristas, setAristas] = useState<AristaCoautoria[]>([]);
  const [totalNodos, setTotalNodos] = useState(0);
  const [totalAristas, setTotalAristas] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dependencias, setDependencias] = useState<Dependencia[]>([]);
  const [filtroDepId, setFiltroDepId] = useState<string>("");

  // Fetch dependencias once for the filter dropdown
  useEffect(() => {
    api
      .dependencias({ limit: 50 })
      .then((data) => setDependencias(data.items))
      .catch(() => {});
  }, []);

  // Re-fetch graph whenever filter changes
  useEffect(() => {
    setLoading(true);
    setError(null);

    const params: Parameters<typeof api.redCoautoria>[0] = filtroDepId
      ? { dependencia_id: filtroDepId, limite_nodos: 200 }
      : { limite_nodos: 100 };

    api
      .redCoautoria(params)
      .then((data) => {
        setNodos(data.nodos);
        setAristas(data.aristas);
        setTotalNodos(data.total_nodos);
        setTotalAristas(data.total_aristas);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al cargar la red"))
      .finally(() => setLoading(false));
  }, [filtroDepId]);

  const depOrder = (() => {
    const freq = new Map<string, number>();
    nodos.forEach((n) => {
      if (n.dependencia_id) freq.set(n.dependencia_id, (freq.get(n.dependencia_id) ?? 0) + 1);
    });
    const sorted = Array.from(freq.entries()).sort((a, b) => b[1] - a[1]);
    const m = new Map<string, number>();
    sorted.forEach(([id], i) => m.set(id, i));
    return m;
  })();

  const depNameMap = new Map(dependencias.map((d) => [d.id, d.nombre_corto ?? d.nombre]));

  const primaryCount = nodos.filter((n) => !n.es_externo).length;
  const externalCount = nodos.filter((n) => n.es_externo).length;

  const uniqueDeps = Array.from(depOrder.entries())
    .sort((a, b) => a[1] - b[1])
    .slice(0, 8)
    .map(([id]) => id);

  const handleNavigate = useCallback(
    (id: string) => {
      router.push(`/perfil/${id}`);
    },
    [router]
  );

  const isFiltered = filtroDepId !== "";

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
          {!loading && !error && nodos.length > 0 && (
            <NetworkGraph
              nodos={nodos}
              aristas={aristas}
              depOrder={depOrder}
              isFiltered={isFiltered}
              onNavigate={handleNavigate}
            />
          )}
          {!loading && !error && nodos.length === 0 && (
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
              Sin coautorías registradas para esta dependencia.
            </div>
          )}
        </div>

        {/* Side panel */}
        <aside className="net-panel">
          {/* Stats */}
          <div className="panel-sec">
            <div className="panel-sec-title">{isFiltered ? "Dependencia" : "Red global"}</div>
            <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
              {isFiltered ? (
                <>
                  <div className="person-stat">
                    <div className="person-stat-val">{primaryCount}</div>
                    <div className="person-stat-lbl">primarios</div>
                  </div>
                  <div className="person-stat">
                    <div className="person-stat-val">{externalCount}</div>
                    <div className="person-stat-lbl">externos</div>
                  </div>
                  <div className="person-stat">
                    <div className="person-stat-val">{totalAristas.toLocaleString("es-MX")}</div>
                    <div className="person-stat-lbl">aristas</div>
                  </div>
                </>
              ) : (
                <>
                  <div className="person-stat">
                    <div className="person-stat-val">{totalNodos.toLocaleString("es-MX")}</div>
                    <div className="person-stat-lbl">nodos</div>
                  </div>
                  <div className="person-stat">
                    <div className="person-stat-val">{totalAristas.toLocaleString("es-MX")}</div>
                    <div className="person-stat-lbl">aristas</div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Filter */}
          <div className="panel-sec">
            <div className="panel-sec-title">Filtrar por dependencia</div>
            <select
              value={filtroDepId}
              onChange={(e) => setFiltroDepId(e.target.value)}
              style={{
                fontSize: 12,
                padding: "5px 8px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border-color)",
                background: "var(--bg-card)",
                color: "var(--text-secondary)",
                width: "100%",
              }}
            >
              <option value="">Todas (top 100 global)</option>
              {dependencias.map((dep) => (
                <option key={dep.id} value={dep.id}>
                  {dep.nombre_corto ?? dep.nombre}
                </option>
              ))}
            </select>
          </div>

          {/* Legend */}
          <div className="panel-sec">
            <div className="panel-sec-title">{isFiltered ? "Leyenda" : "Dependencias (top 8)"}</div>
            {isFiltered ? (
              <>
                <div className="legend-row">
                  <div
                    className="legend-dot"
                    style={{ background: PALETTE[0], width: 10, height: 10 }}
                  />
                  <div className="legend-lbl">
                    {depNameMap.get(filtroDepId) ?? "Dependencia seleccionada"}
                  </div>
                </div>
                <div className="legend-row">
                  <div
                    className="legend-dot"
                    style={{ background: "#94a3b8", width: 10, height: 10 }}
                  />
                  <div className="legend-lbl">Coautores externos</div>
                </div>
              </>
            ) : (
              uniqueDeps.map((depId) => (
                <div key={depId} className="legend-row">
                  <div className="legend-dot" style={{ background: depColor(depId, depOrder) }} />
                  <div className="legend-lbl">
                    {(() => {
                      const name = depNameMap.get(depId);
                      if (!name) return depId.slice(-8);
                      return name.length > 28 ? name.slice(0, 26) + "…" : name;
                    })()}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Instructions */}
          <div className="panel-sec" style={{ marginTop: "auto" }}>
            <div
              style={{
                fontSize: 12,
                color: "var(--text-muted)",
                lineHeight: 1.55,
                borderTop: "1px solid var(--border-color)",
                paddingTop: "var(--sp-4)",
              }}
            >
              <strong style={{ color: "var(--text-secondary)" }}>Clic en nodo</strong> → ver perfil
              <br />
              <strong style={{ color: "var(--text-secondary)" }}>Arrastra</strong> para reposicionar
              <br />
              <strong style={{ color: "var(--text-secondary)" }}>Scroll</strong> para zoom
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
