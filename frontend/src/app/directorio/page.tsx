"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import type { Dependencia, Paginated, PersonaListItem } from "@/types";

const PER_PAGE = 12;

const SNII_OPTS: { label: string; value: string }[] = [
  { label: "Todos", value: "" },
  { label: "Candidato", value: "candidato" },
  { label: "Nivel 1", value: "nivel_1" },
  { label: "Nivel 2", value: "nivel_2" },
  { label: "Nivel 3", value: "nivel_3" },
  { label: "Emérito", value: "emerito" },
];
const SORT_OPTS = [
  { value: "relevancia", label: "Relevancia" },
  { value: "alfabetico", label: "Alfabético" },
  { value: "productividad", label: "Productividad" },
];

function initials(name: string): string {
  return name
    .split(" ")
    .filter((w) => /^[A-ZÁÉÍÓÚÑ]/u.test(w))
    .slice(0, 2)
    .map((w) => w[0])
    .join("");
}

const AVATAR_COLORS = ["blue", "green", "orange", "purple", "red", "teal"];
function avatarColor(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) & 0xffff;
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

export default function Directorio() {
  const [data, setData] = useState<Paginated<PersonaListItem> | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [snii, setSnii] = useState("");
  const [dependenciaId, setDependenciaId] = useState("");
  const [area, setArea] = useState("");
  const [sort, setSort] = useState("relevancia");
  const [page, setPage] = useState(1);
  const [soloUat, setSoloUat] = useState(true);

  const [dependencias, setDependencias] = useState<Dependencia[]>([]);
  const [conceptos, setConceptos] = useState<string[]>([]);

  useEffect(() => {
    void api.dependencias({ limit: 200 }).then((r) => setDependencias(r.items));
    void api.conceptosFrecuentes(30).then(setConceptos);
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.personas({
        limit: PER_PAGE,
        offset: (page - 1) * PER_PAGE,
        q: search || undefined,
        nivel_snii: snii || undefined,
        solo_uat: soloUat || undefined,
        dependencia_id: dependenciaId || undefined,
        area: area || undefined,
      });
      setData(result);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [page, search, snii, soloUat, dependenciaId, area]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  useEffect(() => {
    setPage(1);
  }, [search, sort, snii, soloUat, dependenciaId, area]);

  const items = data?.items ?? [];
  const sortedItems = [...items].sort((a, b) => {
    if (sort === "alfabetico") return a.nombre_completo.localeCompare(b.nombre_completo);
    if (sort === "productividad") return b.total_publicaciones - a.total_publicaciones;
    return 0;
  });

  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PER_PAGE);
  const hasFilters = snii !== "" || dependenciaId !== "" || area !== "";

  return (
    <div style={{ background: "var(--bg-body)", minHeight: "100vh" }}>
      <Header />

      <div className="dir-layout">
        {/* Sidebar */}
        <aside className="dir-sidebar">
          <div
            style={{
              fontWeight: 600,
              fontSize: 14,
              color: "var(--text-primary)",
              marginBottom: "var(--sp-5)",
            }}
          >
            Filtros
          </div>

          <div className="filter-section">
            <div className="filter-title">Nivel SNII</div>
            <div className="filter-chips">
              {SNII_OPTS.map((s) => (
                <button
                  key={s.value}
                  className={snii === s.value ? "chip active" : "chip"}
                  onClick={() => {
                    setSnii(s.value);
                    setPage(1);
                  }}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-section" style={{ marginTop: "var(--sp-5)" }}>
            <div className="filter-title">Dependencia / Facultad</div>
            <select
              className="form-control form-select"
              value={dependenciaId}
              onChange={(e) => {
                setDependenciaId(e.target.value);
                setPage(1);
              }}
              style={{ width: "100%", fontSize: 13, height: 34 }}
            >
              <option value="">Todas las dependencias</option>
              {dependencias.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nombre_corto ?? d.nombre}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-section" style={{ marginTop: "var(--sp-5)" }}>
            <div className="filter-title">Área de investigación</div>
            <select
              className="form-control form-select"
              value={area}
              onChange={(e) => {
                setArea(e.target.value);
                setPage(1);
              }}
              style={{ width: "100%", fontSize: 13, height: 34 }}
            >
              <option value="">Todas las áreas</option>
              {conceptos.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {hasFilters && (
            <button
              className="btn btn-ghost btn-sm"
              style={{ marginTop: "var(--sp-4)", color: "var(--red)" }}
              onClick={() => {
                setSnii("");
                setDependenciaId("");
                setArea("");
                setPage(1);
              }}
            >
              ✕ Limpiar filtros
            </button>
          )}
        </aside>

        {/* Main */}
        <div className="dir-main">
          <div className="dir-toolbar">
            {/* Toggle Solo UAT / Todos */}
            <div
              style={{
                display: "flex",
                background: "var(--bg-muted)",
                borderRadius: "var(--radius-sm)",
                padding: 2,
                gap: 2,
                flexShrink: 0,
              }}
            >
              <button
                className={soloUat ? "btn btn-primary btn-sm" : "btn btn-ghost btn-sm"}
                style={{ height: 30, fontSize: 12 }}
                onClick={() => {
                  setSoloUat(true);
                  setPage(1);
                }}
              >
                Solo UAT
              </button>
              <button
                className={!soloUat ? "btn btn-primary btn-sm" : "btn btn-ghost btn-sm"}
                style={{ height: 30, fontSize: 12 }}
                onClick={() => {
                  setSoloUat(false);
                  setPage(1);
                }}
              >
                Todos
              </button>
            </div>

            <div className="input-group" style={{ flex: 1, maxWidth: 400 }}>
              <span className="input-icon-left" style={{ fontSize: 15 }}>
                🔍
              </span>
              <input
                className="form-control has-icon-left"
                placeholder="Buscar investigador…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ height: 38, borderRadius: "var(--radius-full)" }}
              />
            </div>

            <div
              style={{ fontWeight: 500, fontSize: 14, color: "var(--text-primary)", marginLeft: 8 }}
            >
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                {loading ? "…" : total.toLocaleString("es-MX")}
              </span>
              <span style={{ color: "var(--text-muted)", fontWeight: 400 }}> investigadores</span>
            </div>

            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Ordenar</span>
              <div style={{ position: "relative" }}>
                <select
                  className="form-control form-select"
                  value={sort}
                  onChange={(e) => setSort(e.target.value)}
                  style={{ height: 36, fontSize: 13, width: 160 }}
                >
                  {SORT_OPTS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="results-grid">
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="rc">
                  <div
                    className="skeleton"
                    style={{ height: 40, borderRadius: "var(--radius-sm)" }}
                  />
                  <div
                    className="skeleton"
                    style={{ height: 20, width: "60%", borderRadius: "var(--radius-sm)" }}
                  />
                  <div
                    className="skeleton"
                    style={{ height: 16, width: "80%", borderRadius: "var(--radius-sm)" }}
                  />
                </div>
              ))
            ) : sortedItems.length === 0 ? (
              <div
                style={{
                  gridColumn: "1/-1",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  padding: "80px 0",
                  gap: 12,
                }}
              >
                <div style={{ fontSize: 40, color: "var(--text-light)" }}>🔍</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)" }}>
                  Sin resultados
                </div>
                <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                  Intenta con otros filtros.
                </div>
              </div>
            ) : (
              sortedItems.map((p) => (
                <Link key={p.id} href={`/perfil/${p.id}`} className="rc">
                  <div className="rc-head">
                    <div className={`avatar avatar-md avatar-${avatarColor(p.id)}`}>
                      {initials(p.nombre_completo)}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="rc-name">{p.nombre_completo}</div>
                      <div className="rc-dep">{p.cargo ?? p.tipo}</div>
                    </div>
                    {p.nivel_snii && <span className="badge badge-blue">{p.nivel_snii}</span>}
                  </div>
                  <div className="rc-metrics">
                    <div className="rc-metric">
                      <div className="rc-metric-val">{p.total_publicaciones}</div>
                      <div className="rc-metric-lbl">papers</div>
                    </div>
                    <div className="rc-metric">
                      <div className="rc-metric-val">{p.indice_h}</div>
                      <div className="rc-metric-lbl">índice h</div>
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <div className="pg-info">
                Página {page} de {totalPages} · {total} resultados
              </div>
              <div className="pg-btns">
                <button
                  className="pg-btn"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  ‹
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((p) => (
                  <button
                    key={p}
                    className={page === p ? "pg-btn active" : "pg-btn"}
                    onClick={() => setPage(p)}
                  >
                    {p}
                  </button>
                ))}
                <button
                  className="pg-btn"
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  ›
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
