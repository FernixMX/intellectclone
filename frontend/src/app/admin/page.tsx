"use client";

import { useState, useEffect, useCallback } from "react";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import type {
  CosechaDispararResponse,
  CosechaRead,
  EstadisticasGlobales,
  Paginated,
  SniiApiResultado,
} from "@/types";

// ─── helpers ────────────────────────────────────────────────────────────────

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
  completada_con_errores: "var(--orange)",
  en_curso: "var(--blue)",
  fallida: "var(--red)",
  cancelada: "var(--text-muted)",
  programada: "var(--orange)",
};

const ESTADO_BG: Record<string, string> = {
  completada: "var(--green-light)",
  completada_con_errores: "var(--orange-light)",
  en_curso: "var(--blue-light)",
  fallida: "var(--red-light)",
  cancelada: "var(--bg-muted)",
  programada: "var(--orange-light)",
};

// ─── sub-components ─────────────────────────────────────────────────────────

function StatCard({
  icon,
  label,
  value,
  color,
  bg,
}: {
  icon: string;
  label: string;
  value: string | number;
  color: string;
  bg: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: bg, color }}>
        <span style={{ fontSize: 22 }}>{icon}</span>
      </div>
      <div className="stat-info">
        <div className="stat-value">
          {typeof value === "number" ? value.toLocaleString("es-MX") : value}
        </div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

interface ActionBtnProps {
  label: string;
  loadingLabel: string;
  onClick: () => Promise<void>;
  variant?: "primary" | "outline";
}

function ActionBtn({ label, loadingLabel, onClick, variant = "outline" }: ActionBtnProps) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handle = async () => {
    setBusy(true);
    setResult(null);
    try {
      await onClick();
      setResult("✓ Listo");
    } catch (e: unknown) {
      setResult(e instanceof Error ? `✗ ${e.message}` : "✗ Error");
    } finally {
      setBusy(false);
      setTimeout(() => setResult(null), 4000);
    }
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <button className={`btn btn-${variant} btn-sm`} disabled={busy} onClick={() => void handle()}>
        {busy ? loadingLabel : label}
      </button>
      {result && (
        <span
          style={{
            fontSize: 12,
            color: result.startsWith("✓") ? "var(--green)" : "var(--red)",
          }}
        >
          {result}
        </span>
      )}
    </div>
  );
}

// ─── Tabs ────────────────────────────────────────────────────────────────────

function CosechasTab() {
  const [cosechas, setCosechas] = useState<Paginated<CosechaRead> | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    setLoading(true);
    api
      .cosechas({ limit: 20 })
      .then(setCosechas)
      .catch(() => setCosechas(null))
      .finally(() => setLoading(false));
  }, []);

  // Actualización silenciosa sin spinner para polling y post-acción
  const silentRefresh = useCallback(() => {
    api
      .cosechas({ limit: 20 })
      .then(setCosechas)
      .catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const items = cosechas?.items ?? [];

  // Auto-refresh cada 10 segundos mientras haya una cosecha en_curso
  const hayCosechaEnCurso = items.some((c) => c.estado === "en_curso" || c.estado === "programada");
  useEffect(() => {
    if (!hayCosechaEnCurso) return;
    const id = setInterval(() => {
      void silentRefresh();
    }, 10_000);
    return () => clearInterval(id);
  }, [hayCosechaEnCurso, silentRefresh]);

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "var(--sp-5)",
        }}
      >
        <div>
          <div
            style={{
              fontSize: 16,
              fontWeight: 600,
              color: "var(--text-primary)",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            Historial de cosechas
            {hayCosechaEnCurso && (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 500,
                  color: "var(--blue)",
                  background: "var(--blue-light)",
                  borderRadius: "var(--radius-full)",
                  padding: "2px 8px",
                }}
              >
                ● auto-refresh 10s
              </span>
            )}
          </div>
          <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 2 }}>
            Últimas 20 cosechas registradas
          </div>
        </div>
        <button className="btn btn-outline btn-sm" onClick={silentRefresh}>
          ↻ Actualizar
        </button>
      </div>

      {/* Actions */}
      <div
        className="card"
        style={{
          padding: "var(--sp-4)",
          marginBottom: "var(--sp-4)",
          display: "flex",
          flexWrap: "wrap",
          gap: "var(--sp-4)",
        }}
      >
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>
            Métricas bibliométricas
          </div>
          <ActionBtn
            label="Recalcular métricas"
            loadingLabel="Calculando…"
            onClick={async () => {
              await api.recalcularMetricas();
            }}
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>
            Investigadores SNII
          </div>
          <ActionBtn
            label="Cosecha SNII API"
            loadingLabel="Cosechando…"
            onClick={async () => {
              const r: SniiApiResultado = await api.cosechaSniiApi();
              void r;
            }}
            variant="primary"
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>
            OpenAlex UAT — cosecha completa (~30 min)
          </div>
          <ActionBtn
            label="Cosecha OpenAlex completa"
            loadingLabel="Encolando…"
            onClick={async () => {
              const r: CosechaDispararResponse = await api.cosechaOpenAlexCompleta();
              void r;
              silentRefresh();
            }}
            variant="primary"
          />
        </div>
      </div>

      {/* Table */}
      <div className="card">
        {loading ? (
          <div
            style={{
              padding: "var(--sp-6)",
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: 14,
            }}
          >
            Cargando…
          </div>
        ) : items.length === 0 ? (
          <div
            style={{
              padding: "var(--sp-6)",
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: 14,
            }}
          >
            Sin cosechas registradas
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                {["Fuente", "Estado", "Inicio", "Duración", "Registros", "Nuevos", "Errores"].map(
                  (h) => (
                    <th key={h} className="table-th">
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {items.map((c) => (
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
                    style={{ color: c.errores_count > 0 ? "var(--red)" : "var(--text-muted)" }}
                  >
                    {c.errores_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function GemelosTab() {
  return (
    <div>
      <div style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
        Gemelos digitales
      </div>
      <div
        className="card"
        style={{
          padding: "var(--sp-8)",
          textAlign: "center",
          color: "var(--text-muted)",
          fontSize: 14,
        }}
      >
        <div style={{ fontSize: 36, marginBottom: 12 }}>🤖</div>
        <div style={{ fontWeight: 600, marginBottom: 4, color: "var(--text-secondary)" }}>
          Fase D — pendiente
        </div>
        <div style={{ fontSize: 13 }}>
          La generación de gemelos digitales con LLM se implementa en la Fase D.
        </div>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

const TABS = ["Cosechas", "Gemelos digitales"] as const;
type Tab = (typeof TABS)[number];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("Cosechas");
  const [stats, setStats] = useState<EstadisticasGlobales | null>(null);

  useEffect(() => {
    api
      .estadisticasGlobales()
      .then(setStats)
      .catch(() => setStats(null));
  }, []);

  return (
    <div style={{ background: "var(--bg-body)", minHeight: "100vh" }}>
      <Header />
      <div
        style={{
          maxWidth: 1100,
          margin: "0 auto",
          padding: "calc(60px + var(--sp-7)) var(--sp-7) var(--sp-8)",
        }}
      >
        {/* Page title */}
        <div style={{ marginBottom: "var(--sp-6)" }}>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: "var(--text-primary)",
              margin: 0,
              marginBottom: 4,
            }}
          >
            Panel de administración
          </h1>
          <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
            Estado del sistema y operaciones de mantenimiento
          </p>
        </div>

        {/* Stats strip */}
        {stats && (
          <div className="grid-4" style={{ marginBottom: "var(--sp-6)" }}>
            <StatCard
              icon="👥"
              label="Personas"
              value={stats.total_personas}
              color="var(--blue)"
              bg="var(--blue-light)"
            />
            <StatCard
              icon="📄"
              label="Papers"
              value={stats.total_papers}
              color="var(--green)"
              bg="var(--green-light)"
            />
            <StatCard
              icon="🔗"
              label="Coautorías"
              value={stats.total_coautorias}
              color="var(--orange)"
              bg="var(--orange-light)"
            />
            <StatCard
              icon="🏛️"
              label="Dependencias"
              value={stats.total_dependencias}
              color="var(--purple)"
              bg="var(--purple-light)"
            />
          </div>
        )}

        {/* Tabs */}
        <div
          style={{
            display: "flex",
            gap: 4,
            borderBottom: "1px solid var(--border-color)",
            marginBottom: "var(--sp-5)",
          }}
        >
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                padding: "8px 16px",
                fontSize: 13,
                fontWeight: tab === t ? 600 : 400,
                color: tab === t ? "var(--blue)" : "var(--text-muted)",
                background: "none",
                border: "none",
                borderBottom: tab === t ? "2px solid var(--blue)" : "2px solid transparent",
                cursor: "pointer",
                marginBottom: -1,
                transition: "color 120ms",
              }}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {tab === "Cosechas" && <CosechasTab />}
        {tab === "Gemelos digitales" && <GemelosTab />}
      </div>
    </div>
  );
}
