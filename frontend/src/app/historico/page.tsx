"use client";

import { useState, useEffect, useCallback } from "react";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import type { CosechaRead, Paginated } from "@/types";

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-MX", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function fmtMs(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

const ESTADO_COLOR: Record<string, string> = {
  completada: "var(--green)",
  en_curso: "var(--blue)",
  error: "var(--red)",
  cancelada: "var(--text-muted)",
  programada: "var(--orange)",
};
const ESTADO_BG: Record<string, string> = {
  completada: "var(--green-light)",
  en_curso: "var(--blue-light)",
  error: "var(--red-light)",
  cancelada: "var(--bg-muted)",
  programada: "var(--orange-light)",
};

const FUENTES = ["Todas", "openalex", "vufind_uat", "riuat", "snii_api", "sniiuat"];
const ESTADOS = ["Todos", "completada", "error", "en_curso", "cancelada"];

export default function HistoricoPage() {
  const [data, setData] = useState<Paginated<CosechaRead> | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterFuente, setFilterFuente] = useState("Todas");
  const [filterEstado, setFilterEstado] = useState("Todos");

  const load = useCallback(() => {
    setLoading(true);
    api
      .cosechas({ limit: 50 })
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const items = data?.items ?? [];

  const filtered = items.filter((c) => {
    if (filterFuente !== "Todas" && c.fuente !== filterFuente) return false;
    if (filterEstado !== "Todos" && c.estado !== filterEstado) return false;
    return true;
  });

  const totalRegistros = filtered.reduce((s, c) => s + c.registros_procesados, 0);
  const totalNuevos = filtered.reduce((s, c) => s + c.registros_nuevos, 0);

  const fuentesPresentes = Array.from(new Set(items.map((c) => c.fuente)));

  return (
    <div
      style={{
        background: "var(--bg-body)",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Header />

      {/* Page sub-header */}
      <div
        style={{
          marginTop: 60,
          padding: "var(--sp-4) var(--sp-6)",
          background: "var(--bg-card)",
          borderBottom: "1px solid var(--border-color)",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)" }}>
          Histórico de cosechas
        </span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-muted)" }}>
          {filtered.length} registros
        </span>
        <div style={{ marginLeft: "auto" }}>
          <button className="btn btn-ghost btn-sm" onClick={load}>
            ↻ Actualizar
          </button>
        </div>
      </div>

      <div className="hist-layout" style={{ flex: 1 }}>
        {/* Filter sidebar */}
        <aside className="hist-sidebar">
          <div style={{ fontWeight: 600, fontSize: 14, color: "var(--text-primary)" }}>Filtros</div>

          <div>
            <div className="filter-title">Fuente</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {["Todas", ...fuentesPresentes].map((f) => (
                <button
                  key={f}
                  className={`fchip${filterFuente === f ? "active" : ""}`}
                  style={{ textAlign: "left" }}
                  onClick={() => setFilterFuente(f)}
                >
                  {f}
                </button>
              ))}
              {fuentesPresentes.length === 0 &&
                FUENTES.slice(1).map((f) => (
                  <button
                    key={f}
                    className={`fchip${filterFuente === f ? "active" : ""}`}
                    style={{ textAlign: "left" }}
                    onClick={() => setFilterFuente(f)}
                  >
                    {f}
                  </button>
                ))}
            </div>
          </div>

          <div>
            <div className="filter-title">Estado</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {ESTADOS.map((s) => (
                <button
                  key={s}
                  className={`fchip${filterEstado === s ? "active" : ""}`}
                  style={{ textAlign: "left" }}
                  onClick={() => setFilterEstado(s)}
                >
                  {s === "Todos" ? "Todos" : s}
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Main content */}
        <div className="hist-main">
          <div className="hist-table-wrap">
            {loading ? (
              <div
                style={{
                  padding: "var(--sp-8)",
                  textAlign: "center",
                  color: "var(--text-muted)",
                  fontSize: 14,
                }}
              >
                Cargando…
              </div>
            ) : filtered.length === 0 ? (
              <div
                style={{
                  padding: "var(--sp-8)",
                  textAlign: "center",
                  color: "var(--text-muted)",
                  fontSize: 14,
                }}
              >
                Sin cosechas registradas
              </div>
            ) : (
              <div className="card" style={{ overflow: "hidden" }}>
                <table className="table">
                  <thead>
                    <tr>
                      {[
                        "Fuente",
                        "Estado",
                        "Inicio",
                        "Duración",
                        "Procesados",
                        "Nuevos",
                        "Errores",
                        "Manual",
                      ].map((h) => (
                        <th key={h} className="table-th">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((c) => (
                      <tr key={c.id} className="table-tr">
                        <td className="table-td strong">{c.fuente}</td>
                        <td className="table-td">
                          <span
                            className="badge"
                            style={{
                              color: ESTADO_COLOR[c.estado] ?? "var(--text-muted)",
                              background: ESTADO_BG[c.estado] ?? "var(--bg-muted)",
                            }}
                          >
                            {c.estado}
                          </span>
                        </td>
                        <td className="table-td mono" style={{ fontSize: 11 }}>
                          {fmtDate(c.iniciada_at)}
                        </td>
                        <td className="table-td mono" style={{ fontSize: 11 }}>
                          {fmtMs(c.duracion_ms)}
                        </td>
                        <td className="table-td mono">
                          {c.registros_procesados.toLocaleString("es-MX")}
                        </td>
                        <td className="table-td mono" style={{ color: "var(--green)" }}>
                          +{c.registros_nuevos.toLocaleString("es-MX")}
                        </td>
                        <td
                          className="table-td mono"
                          style={{
                            color: c.errores_count > 0 ? "var(--red)" : "var(--text-muted)",
                          }}
                        >
                          {c.errores_count}
                        </td>
                        <td
                          className="table-td"
                          style={{ fontSize: 12, color: "var(--text-muted)" }}
                        >
                          {c.disparada_manual ? "Sí" : "Auto"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Summary bar */}
          <div className="hist-summary">
            <div className="summary-stat">
              <div className="summary-val">{filtered.length}</div>
              <div className="summary-lbl">cosechas</div>
            </div>
            <div style={{ width: 1, height: 36, background: "var(--border-color)" }} />
            <div className="summary-stat">
              <div className="summary-val">{totalRegistros.toLocaleString("es-MX")}</div>
              <div className="summary-lbl">registros procesados</div>
            </div>
            <div style={{ width: 1, height: 36, background: "var(--border-color)" }} />
            <div className="summary-stat">
              <div className="summary-val" style={{ color: "var(--green)" }}>
                +{totalNuevos.toLocaleString("es-MX")}
              </div>
              <div className="summary-lbl">registros nuevos</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
