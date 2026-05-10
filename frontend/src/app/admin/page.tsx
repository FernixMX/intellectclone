"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import type {
  CosechaDispararResponse,
  CosechaRead,
  EstadisticasGlobales,
  PapersPorAnio,
  Paginated,
  SniiApiResultado,
  TopDependenciaItem,
  TopInvestigadorItem,
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
  subvalue,
  color,
  bg,
}: {
  icon: string;
  label: string;
  value: string | number;
  subvalue?: string;
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
        {subvalue && (
          <div style={{ fontSize: 11, color: "var(--text-light)", marginTop: 1, lineHeight: 1.3 }}>
            {subvalue}
          </div>
        )}
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

// ─── Login gate ──────────────────────────────────────────────────────────────

function LoginGate({ onSuccess }: { onSuccess: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const setToken = useAuthStore((s) => s.setToken);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      setError("Ingresa la contraseña");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await api.login(password.trim());
      setToken(res.access_token);
      onSuccess();
    } catch {
      setError("Contraseña incorrecta");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-body)",
      }}
    >
      <div className="card" style={{ padding: "var(--sp-8)", width: 340, textAlign: "center" }}>
        <div style={{ fontSize: 32, marginBottom: "var(--sp-4)" }}>🔒</div>
        <div
          style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}
        >
          Panel de administración
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: "var(--sp-5)" }}>
          Ingresa la contraseña de acceso
        </div>
        <form
          onSubmit={(e) => void handleSubmit(e)}
          style={{ display: "flex", flexDirection: "column", gap: 12 }}
        >
          <input
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setError(null);
            }}
            placeholder="Contraseña"
            autoFocus
            style={{
              padding: "9px 12px",
              fontSize: 14,
              border: `1px solid ${error ? "var(--red)" : "var(--border-color)"}`,
              borderRadius: "var(--radius-md)",
              background: "var(--bg-surface)",
              color: "var(--text-primary)",
              outline: "none",
            }}
          />
          {error && (
            <div style={{ fontSize: 12, color: "var(--red)", textAlign: "left" }}>{error}</div>
          )}
          <button type="submit" className="btn btn-primary btn-sm" disabled={busy}>
            {busy ? "Accediendo…" : "Acceder"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─── Name helpers ────────────────────────────────────────────────────────────

const _CITIES = new Set([
  "Victoria",
  "Tampico",
  "Reynosa",
  "Matamoros",
  "Aztlán",
  "Hermoso",
  "Laredo",
]);
const _SKIP = new Set(["y", "e", "de", "del", "la", "el", "los", "las", "para", "con", "por"]);

function shortDepName(nombre: string, nombreCorto: string | null): string {
  if (nombreCorto && nombreCorto.length <= 30) return nombreCorto;

  let s = nombre
    .replace(/\s*"Dr[a]?\..+"$/, "") // strip "Dr. Nombre" honorific suffix
    .replace(/^Facultad de\s+/i, "")
    .replace(/^Unidad Académica Multidisciplinaria\s+/i, "UAM ")
    .replace(/^Unidad Académica de\s+/i, "")
    .replace(/^Unidad Académica\s+/i, "")
    .replace(/^Instituto de\s+/i, "")
    .replace(/^Centro de\s+/i, "")
    .replace(/^Escuela de\s+/i, "")
    .replace(/^División de\s+/i, "")
    .trim();

  if (s.length <= 30) return s;

  const words = s.split(/\s+/);
  const lastWord = words[words.length - 1];
  const hasCity = _CITIES.has(lastWord);

  const content: string[] = [];
  for (const w of words) {
    if (!_SKIP.has(w.toLowerCase()) && !_CITIES.has(w)) {
      content.push(w);
      if (content.length === (hasCity ? 1 : 2)) break;
    }
  }

  if (hasCity) content.push(lastWord);
  return content.join(" ") || s.slice(0, 25) + "…";
}

// ─── Dashboard tab ───────────────────────────────────────────────────────────

const TOOLTIP_STYLE = {
  background: "var(--bg-card)",
  border: "1px solid var(--border-color)",
  borderRadius: 6,
  fontSize: 12,
} as const;

function DashboardTab() {
  const [papersData, setPapersData] = useState<PapersPorAnio[]>([]);
  const [depsData, setDepsData] = useState<TopDependenciaItem[]>([]);
  const [invData, setInvData] = useState<TopInvestigadorItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [soloUat, setSoloUat] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api
        .papersPorAnio()
        .then((r) => setPapersData(r.datos))
        .catch(() => {}),
      api
        .topDependencias({ limite: 8 })
        .then((r) => setDepsData(r.items))
        .catch(() => {}),
      api
        .topInvestigadores({ limite: 10, orden: "papers" })
        .then((r) => setInvData(r.items))
        .catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div
        style={{ padding: "60px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 14 }}
      >
        Cargando datos…
      </div>
    );
  }

  // Stacked chart: bottom = externos, top = UAT
  const papersChart = papersData.map((d) => ({
    ...d,
    papers_externos: d.total_papers - d.total_papers_uat,
  }));

  const depsChart = depsData.map((d) => ({
    name: shortDepName(d.nombre, d.nombre_corto),
    fullName: d.nombre,
    papers: d.total_papers,
    personas: d.total_personas,
  }));

  const invChart = invData.map((i) => ({
    name: i.nombre_completo.split(" ").slice(-2).join(" "),
    papers: i.n_papers_cosechados,
    h: i.indice_h,
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--sp-6)" }}>
      {/* Toggle Solo UAT / Todos */}
      <div style={{ display: "flex", alignItems: "center", gap: "var(--sp-4)", flexWrap: "wrap" }}>
        <div
          style={{
            display: "flex",
            background: "var(--bg-muted)",
            borderRadius: "var(--radius-sm)",
            padding: 2,
            gap: 2,
          }}
        >
          <button
            className={soloUat ? "btn btn-primary btn-sm" : "btn btn-ghost btn-sm"}
            style={{ height: 30, fontSize: 12 }}
            onClick={() => setSoloUat(true)}
          >
            Solo UAT
          </button>
          <button
            className={!soloUat ? "btn btn-primary btn-sm" : "btn btn-ghost btn-sm"}
            style={{ height: 30, fontSize: 12 }}
            onClick={() => setSoloUat(false)}
          >
            UAT + externos
          </button>
        </div>
        <div
          style={{
            fontSize: 12,
            color: "var(--text-muted)",
            background: "var(--bg-muted)",
            borderRadius: "var(--radius-sm)",
            padding: "6px 10px",
            lineHeight: 1.4,
            maxWidth: 560,
          }}
        >
          <strong style={{ color: "var(--text-secondary)" }}>UAT</strong> = publicaciones donde al
          menos un autor pertenece a una dependencia/facultad confirmada de la UAT. &nbsp;
          <strong style={{ color: "var(--text-secondary)" }}>Externos</strong> = publicaciones de
          coautores que colaboraron con investigadores UAT pero no están adscritos a ninguna
          dependencia UAT.
        </div>
      </div>

      {/* Papers por año */}
      <div className="card" style={{ padding: "var(--sp-5)" }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: "var(--text-primary)",
            marginBottom: "var(--sp-4)",
          }}
        >
          Publicaciones por año
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={papersChart} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis dataKey="año" tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
            <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} width={40} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            {!soloUat && (
              <Bar dataKey="papers_externos" name="Externos" fill="#e2e8f0" stackId="a" />
            )}
            <Bar
              dataKey="total_papers_uat"
              name="UAT"
              fill="var(--blue)"
              stackId="a"
              radius={[3, 3, 0, 0]}
            />
            <Legend
              iconSize={10}
              wrapperStyle={{ fontSize: 11, paddingTop: 8, color: "var(--text-muted)" }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Top dependencias + top investigadores */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--sp-5)" }}>
        <div className="card" style={{ padding: "var(--sp-5)" }}>
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: "var(--text-primary)",
              marginBottom: "var(--sp-4)",
            }}
          >
            Top dependencias (papers UAT)
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart
              data={depsChart}
              layout="vertical"
              margin={{ top: 0, right: 8, bottom: 0, left: 8 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border-color)"
                horizontal={false}
              />
              <XAxis type="number" tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
              <YAxis
                type="category"
                dataKey="name"
                width={130}
                tick={{ fontSize: 10, fill: "var(--text-muted)" }}
              />
              <Tooltip
                labelFormatter={(_, payload) =>
                  (payload?.[0]?.payload as { fullName?: string } | undefined)?.fullName ?? ""
                }
                contentStyle={TOOLTIP_STYLE}
              />
              <Bar dataKey="papers" name="Papers" fill="var(--green)" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ padding: "var(--sp-5)" }}>
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: "var(--text-primary)",
              marginBottom: "var(--sp-4)",
            }}
          >
            Top investigadores UAT (papers)
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={invChart} margin={{ top: 4, right: 8, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 9, fill: "var(--text-muted)" }}
                angle={-30}
                textAnchor="end"
                interval={0}
              />
              <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} width={36} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="papers" name="Papers" fill="var(--purple)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// ─── Cosechas tab ────────────────────────────────────────────────────────────

function CosechasTab({ token }: { token: string }) {
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
              await api.recalcularMetricas(token);
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
              const r: SniiApiResultado = await api.cosechaSniiApi(token);
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
              const r: CosechaDispararResponse = await api.cosechaOpenAlexCompleta(token);
              void r;
              silentRefresh();
            }}
            variant="primary"
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>
            VuFind UAT — cosecha completa (~45 min)
          </div>
          <ActionBtn
            label="Cosecha VuFind completa"
            loadingLabel="Encolando…"
            onClick={async () => {
              const r: CosechaDispararResponse = await api.cosechaVuFindCompleta(token);
              void r;
              silentRefresh();
            }}
            variant="primary"
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>
            Crossref — enriquecer papers con DOI (~20 min)
          </div>
          <ActionBtn
            label="Enriquecer con Crossref"
            loadingLabel="Encolando…"
            onClick={async () => {
              const r: CosechaDispararResponse = await api.cosechaCrossrefEnrich(token);
              void r;
              silentRefresh();
            }}
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>
            ORCID — enriquecer investigadores (~30 min)
          </div>
          <ActionBtn
            label="Enriquecer con ORCID"
            loadingLabel="Encolando…"
            onClick={async () => {
              const r: CosechaDispararResponse = await api.cosechaOrcidEnrich(token);
              void r;
              silentRefresh();
            }}
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
          <div className="table-wrap">
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
          </div>
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

const TABS = ["Dashboard", "Cosechas", "Gemelos digitales"] as const;
type Tab = (typeof TABS)[number];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("Dashboard");
  const [stats, setStats] = useState<EstadisticasGlobales | null>(null);
  const [mounted, setMounted] = useState(false);

  const { token, isAuthenticated, clearToken } = useAuthStore();
  const authed = mounted && isAuthenticated();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!authed) return;
    api
      .estadisticasGlobales()
      .then(setStats)
      .catch(() => setStats(null));
  }, [authed]);

  if (!mounted) return null;

  if (!authed) {
    return (
      <LoginGate
        onSuccess={() => {
          /* zustand already updated */
        }}
      />
    );
  }

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
        <div
          style={{
            marginBottom: "var(--sp-6)",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
          }}
        >
          <div>
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
          <button
            className="btn btn-ghost btn-sm"
            style={{ color: "var(--text-muted)", marginTop: 4 }}
            onClick={clearToken}
          >
            Cerrar sesión
          </button>
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
              label="Papers UAT"
              value={stats.total_papers_uat}
              subvalue={`${stats.total_papers.toLocaleString("es-MX")} total (con externos)`}
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
        {tab === "Dashboard" && <DashboardTab />}
        {tab === "Cosechas" && <CosechasTab token={token ?? ""} />}
        {tab === "Gemelos digitales" && <GemelosTab />}
      </div>
    </div>
  );
}
