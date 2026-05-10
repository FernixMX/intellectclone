import Link from "next/link";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import type { EstadisticasGlobales } from "@/types";

const RESEARCHERS = [
  {
    init: "MC",
    name: "Dra. María Elena Cárdenas",
    dep: "Fac. de Ingeniería",
    papers: 84,
    citas: 1284,
    color: "blue",
  },
  {
    init: "JH",
    name: "Dr. Jorge Hernández Mota",
    dep: "Fac. de Medicina",
    papers: 118,
    citas: 2341,
    color: "green",
  },
  {
    init: "EC",
    name: "Dr. Ernesto Chávez Ramírez",
    dep: "Fac. de Ingeniería",
    papers: 134,
    citas: 3102,
    color: "purple",
  },
  {
    init: "BJ",
    name: "Dra. Beatriz Jiménez Cruz",
    dep: "UAMRR",
    papers: 102,
    citas: 2198,
    color: "orange",
  },
];

const FEATURES = [
  {
    icon: "👥",
    bg: "var(--blue-light)",
    title: "Directorio de investigadores",
    desc: "Consulta la producción intelectual de investigadores UAT: publicaciones, citas, áreas de especialización y redes de colaboración.",
    cta: "Explorar directorio",
    href: "/directorio",
    restricted: false,
  },
  {
    icon: "🕸️",
    bg: "var(--green-light)",
    title: "Red de colaboración",
    desc: "Visualiza cómo se conectan los investigadores a través de coautorías. Nodos proporcionales a productividad.",
    cta: "Ver red",
    href: "/red",
    restricted: false,
  },
  {
    icon: "⚙️",
    bg: "var(--purple-light)",
    title: "Panel de administración",
    desc: "Gestiona cosechas de datos, recalcula métricas bibliométricas y supervisa el estado del sistema.",
    cta: "Abrir panel",
    href: "/admin",
    restricted: true,
  },
];

async function getStats(): Promise<EstadisticasGlobales | null> {
  try {
    return await api.estadisticasGlobales();
  } catch {
    return null;
  }
}

export default async function Home() {
  const stats = await getStats();

  const stripStats = [
    { val: stats?.total_personas.toLocaleString("es-MX") ?? "—", lbl: "investigadores activos" },
    { val: stats?.total_papers.toLocaleString("es-MX") ?? "—", lbl: "publicaciones indexadas" },
    { val: stats?.total_dependencias.toLocaleString("es-MX") ?? "—", lbl: "dependencias" },
    {
      val: stats?.total_cuerpos_academicos.toLocaleString("es-MX") ?? "—",
      lbl: "cuerpos académicos",
    },
  ];

  return (
    <div style={{ background: "var(--bg-body)", minHeight: "100vh" }}>
      <Header />
      <div className="pub-content">
        {/* Hero */}
        <div style={{ background: "#14243c" }}>
          <div className="hero-wrap">
            <div>
              <div className="hero-eyebrow">Universidad Autónoma de Tamaulipas · PDI 2024–2028</div>
              <h1 className="hero-title">
                La comunidad académica UAT,
                <br />
                <span>en forma digital</span>
              </h1>
              <p className="hero-desc">
                IntellectClone construye gemelos digitales de los investigadores UAT a partir de su
                producción académica pública. Consulta perfiles, explora redes y simula respuestas
                institucionales.
              </p>
              <div className="hero-actions">
                <Link href="/directorio" className="btn btn-primary btn-lg">
                  Explorar directorio
                </Link>
                <Link
                  href="/acerca"
                  className="btn btn-outline btn-lg"
                  style={{ borderColor: "#2a4060", color: "#8da2b5" }}
                >
                  Conocer el proyecto
                </Link>
              </div>
            </div>

            <div className="hero-visual">
              <div className="hero-vis-title">Investigadores destacados</div>
              {RESEARCHERS.map((r) => (
                <div key={r.init} className="hero-researcher-row">
                  <div className={`avatar avatar-sm avatar-${r.color}`}>{r.init}</div>
                  <div>
                    <div className="hero-res-name">{r.name}</div>
                    <div className="hero-res-dep">{r.dep}</div>
                  </div>
                  <div className="hero-res-metrics">
                    <div className="hero-metric">
                      <div className="hero-metric-val">{r.papers}</div>
                      <div className="hero-metric-lbl">papers</div>
                    </div>
                    <div className="hero-metric">
                      <div className="hero-metric-val">{r.citas.toLocaleString("es-MX")}</div>
                      <div className="hero-metric-lbl">citas</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Stats strip */}
        <div className="stats-row">
          {stripStats.map((s) => (
            <div key={s.lbl} className="stat-strip-item">
              <div className="stat-strip-val">{s.val}</div>
              <div className="stat-strip-lbl">{s.lbl}</div>
            </div>
          ))}
        </div>

        {/* Features */}
        <section className="features-section">
          <div className="features-eyebrow">Plataforma</div>
          <h2 className="features-title">Todo sobre la comunidad académica UAT</h2>
          <div className="features-grid">
            {FEATURES.map((f) => (
              <Link key={f.title} href={f.href} className="feature-card">
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                  }}
                >
                  <div className="feature-icon-wrap" style={{ background: f.bg, fontSize: 22 }}>
                    {f.icon}
                  </div>
                  {f.restricted && <span className="badge badge-orange">Solo autorizado</span>}
                </div>
                <div className="feature-card-title">{f.title}</div>
                <div className="feature-card-desc">{f.desc}</div>
                <div className="feature-card-cta">{f.cta} →</div>
              </Link>
            ))}
          </div>
        </section>

        {/* Endorsed */}
        <div className="endorsed-section">
          <div className="endorsed-inner">
            <div className="endorsed-label">Respaldado por</div>
            <div className="endorsed-logos">
              <div style={{ textAlign: "center" }}>
                <div className="endorsed-item-name">Rectoría UAT</div>
                <div className="endorsed-item-sub">Universidad Autónoma de Tamaulipas</div>
              </div>
              <div style={{ width: 1, height: 36, background: "var(--border-color)" }} />
              <div style={{ textAlign: "center" }}>
                <div className="endorsed-item-name">Oficina de Asesores</div>
                <div className="endorsed-item-sub">Secretaría Académica</div>
              </div>
              <div style={{ width: 1, height: 36, background: "var(--border-color)" }} />
              <div className="pdi-tag">PDI 2024–2028 · «La UAT se Transforma»</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="pub-footer">
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <div className="pub-footer-logo-uat">UAT</div>
            <div className="pub-footer-logo-sub">IntellectClone</div>
          </div>
          <div className="pub-footer-links">
            <a href="#" className="pub-footer-link">
              Privacidad
            </a>
            <a href="#" className="pub-footer-link">
              Solicitar baja
            </a>
            <a href="#" className="pub-footer-link">
              Contacto
            </a>
            <Link href="/acerca" className="pub-footer-link">
              Acerca
            </Link>
          </div>
          <div className="pub-footer-copy">© 2026 Universidad Autónoma de Tamaulipas · v1.0</div>
        </footer>
      </div>
    </div>
  );
}
