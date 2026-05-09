import Link from "next/link";
import { notFound } from "next/navigation";
import Header from "@/components/Header";
import { api } from "@/lib/api";
import { translateConcept } from "@/lib/translations";

const AVATAR_COLORS = ["blue", "green", "orange", "purple", "red", "teal"];
function avatarColor(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) & 0xffff;
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

function initials(name: string): string {
  return name
    .split(" ")
    .filter((w) => /^[A-ZÁÉÍÓÚÑ]/u.test(w))
    .slice(0, 2)
    .map((w) => w[0])
    .join("");
}

const SNII_LABELS: Record<string, string> = {
  candidato: "SNI Candidato",
  nivel_1: "SNI Nivel I",
  nivel_2: "SNI Nivel II",
  nivel_3: "SNI Nivel III",
  emerito: "SNI Emérito",
};
function formatSnii(nivel: string): string {
  return SNII_LABELS[nivel] ?? nivel;
}

interface Props {
  params: Promise<{ id: string }>;
}

export default async function PerfilPage({ params }: Props) {
  const { id } = await params;

  let persona;
  try {
    persona = await api.persona(id);
  } catch {
    notFound();
  }

  let papersData = null;
  try {
    papersData = await api.papers({ persona_id: id, limit: 20, offset: 0 });
  } catch {
    // no crítico — se muestra sección vacía
  }

  let conceptos: string[] = [];
  try {
    conceptos = await api.conceptosPersona(id, 5);
  } catch {
    // no crítico
  }

  const color = avatarColor(persona.id);
  const inits = initials(persona.nombre_completo);

  const statsMini = [
    {
      icon: "📄",
      bg: "var(--blue-light)",
      val: persona.total_publicaciones.toLocaleString("es-MX"),
      lbl: "Publicaciones",
    },
    {
      icon: "💬",
      bg: "var(--green-light)",
      val: persona.total_citas.toLocaleString("es-MX"),
      lbl: "Citas totales",
    },
    { icon: "📈", bg: "var(--orange-light)", val: String(persona.indice_h), lbl: "Índice h" },
    { icon: "🔬", bg: "var(--purple-light)", val: String(persona.indice_i10), lbl: "Índice i10" },
  ];

  const areas: string[] = [];
  if (persona.grado_disciplina) areas.push(persona.grado_disciplina);
  const metaAreas = persona.metadatos?.areas_conocimiento;
  if (Array.isArray(metaAreas)) {
    for (const a of metaAreas as string[]) areas.push(a);
  }

  return (
    <div style={{ background: "var(--bg-body)", minHeight: "100vh" }}>
      <Header />

      <div className="profile-shell" style={{ paddingTop: 80 }}>
        {/* Breadcrumb */}
        <div className="breadcrumb" style={{ marginBottom: "var(--sp-4)" }}>
          <Link href="/directorio">Directorio</Link>
          <span className="breadcrumb-sep">›</span>
          <span className="breadcrumb-current">{persona.nombre_completo}</span>
        </div>

        {/* Hero */}
        <div className="profile-hero">
          <div
            className={`profile-avatar-ring avatar-${color}`}
            style={{ background: `var(--${color})` }}
          >
            {inits}
          </div>
          <div>
            <div className="profile-name">{persona.nombre_completo}</div>
            <div className="profile-sub">
              {persona.cargo ?? persona.tipo}
              {persona.grado_maximo ? ` · ${persona.grado_maximo}` : ""}
            </div>
            <div style={{ fontSize: 13, color: "#8da2b5", marginBottom: 8 }}>
              🏛 {persona.dependencia_nombre ?? "Sin dependencia asignada"}
            </div>
            {conceptos.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                {conceptos.map((c) => (
                  <span
                    key={c}
                    className="badge"
                    style={{
                      background: "rgba(255,255,255,0.08)",
                      color: "rgba(255,255,255,0.65)",
                      fontSize: 11,
                    }}
                  >
                    {translateConcept(c)}
                  </span>
                ))}
              </div>
            )}
            <div className="profile-badges">
              {persona.nivel_snii && (
                <span className="badge badge-blue">{formatSnii(persona.nivel_snii)}</span>
              )}
              {persona.activa ? (
                <span className="badge badge-green">Perfil activo</span>
              ) : (
                <span className="badge badge-muted">Inactivo</span>
              )}
              {persona.orcid && (
                <a
                  href={`https://orcid.org/${persona.orcid}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="badge"
                  style={{ background: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.8)" }}
                >
                  ORCID
                </a>
              )}
            </div>
          </div>
          <div className="profile-hero-actions">
            <a href="#publicaciones" className="btn btn-primary btn-md">
              Ver publicaciones
            </a>
            {persona.sitio_web && (
              <a
                href={persona.sitio_web}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline btn-sm"
                style={{ borderColor: "rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.5)" }}
              >
                Sitio web
              </a>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="stats-row-4">
          {statsMini.map((s) => (
            <div key={s.lbl} className="stat-mini">
              <div className="stat-mini-icon" style={{ background: s.bg, fontSize: 20 }}>
                {s.icon}
              </div>
              <div>
                <div className="stat-mini-val">{s.val}</div>
                <div className="stat-mini-lbl">{s.lbl}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Grid */}
        <div className="profile-grid">
          <div>
            {/* Areas */}
            {areas.length > 0 && (
              <div className="section-card" style={{ marginBottom: "var(--sp-4)" }}>
                <div className="section-card-header">
                  <div className="section-card-title">Áreas de especialización</div>
                </div>
                <div
                  className="section-card-body"
                  style={{ display: "flex", flexWrap: "wrap", gap: 6 }}
                >
                  {areas.map((a) => (
                    <span key={a} className="badge badge-muted">
                      {translateConcept(a)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Publications */}
            <div
              id="publicaciones"
              className="section-card"
              style={{ marginBottom: "var(--sp-4)" }}
            >
              <div className="section-card-header">
                <div className="section-card-title">Publicaciones</div>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 12,
                    color: "var(--text-muted)",
                  }}
                >
                  {persona.total_publicaciones} total
                </span>
              </div>
              <div className="section-card-body">
                {papersData && papersData.items.length > 0 ? (
                  <>
                    {papersData.items.map((p) => (
                      <div key={p.id} className="pub-item">
                        <div className="pub-title">
                          {p.doi ? (
                            <a
                              href={`https://doi.org/${p.doi}`}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {p.titulo}
                            </a>
                          ) : (
                            p.titulo
                          )}
                        </div>
                        <div className="pub-meta">
                          {p.año && <span>{p.año}</span>}
                          {p.revista && <span>{p.revista}</span>}
                          {p.total_citas > 0 && (
                            <span className="pub-citas">🗣 {p.total_citas} citas</span>
                          )}
                        </div>
                      </div>
                    ))}
                    {papersData.total > 20 && (
                      <div
                        style={{
                          paddingTop: "var(--sp-3)",
                          fontSize: 13,
                          color: "var(--text-muted)",
                        }}
                      >
                        Mostrando 20 de {papersData.total} publicaciones.
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6 }}>
                    {persona.primera_publicacion && (
                      <p style={{ marginBottom: 8 }}>
                        Primera publicación: <strong>{persona.primera_publicacion}</strong>
                        {persona.ultima_publicacion && (
                          <>
                            {" "}
                            · Última: <strong>{persona.ultima_publicacion}</strong>
                          </>
                        )}
                      </p>
                    )}
                    <p>No se encontraron publicaciones indexadas para este investigador.</p>
                  </div>
                )}
              </div>
            </div>

            {/* IDs externos */}
            {(persona.openalex_id ?? persona.scopus_id ?? persona.cvu_conacyt) && (
              <div className="section-card">
                <div className="section-card-header">
                  <div className="section-card-title">Identificadores externos</div>
                </div>
                <div
                  className="section-card-body"
                  style={{ display: "flex", flexDirection: "column", gap: 8 }}
                >
                  {persona.openalex_id && (
                    <div style={{ fontSize: 13 }}>
                      <span style={{ color: "var(--text-muted)" }}>OpenAlex: </span>
                      <span style={{ fontFamily: "var(--font-mono)" }}>{persona.openalex_id}</span>
                    </div>
                  )}
                  {persona.orcid && (
                    <div style={{ fontSize: 13 }}>
                      <span style={{ color: "var(--text-muted)" }}>ORCID: </span>
                      <a
                        href={`https://orcid.org/${persona.orcid}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontFamily: "var(--font-mono)" }}
                      >
                        {persona.orcid}
                      </a>
                    </div>
                  )}
                  {persona.cvu_conacyt && (
                    <div style={{ fontSize: 13 }}>
                      <span style={{ color: "var(--text-muted)" }}>CVU Conacyt: </span>
                      <span style={{ fontFamily: "var(--font-mono)" }}>{persona.cvu_conacyt}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar derecho */}
          <div>
            <div className="twin-card" style={{ marginBottom: "var(--sp-4)" }}>
              <div className="twin-card-header">
                <div className="twin-card-title">Gemelo digital</div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span className="twin-dot pending" />
                  <span style={{ fontSize: 12, color: "#6b8fe0", fontWeight: 500 }}>Pendiente</span>
                </div>
              </div>
              <div className="twin-card-body">
                <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.55 }}>
                  El gemelo digital de este investigador aún no ha sido generado. Requiere
                  validación del corpus bibliométrico.
                </div>
                <button
                  className="btn btn-outline btn-sm"
                  style={{ width: "100%", justifyContent: "center" }}
                  disabled
                >
                  Generación pendiente
                </button>
              </div>
            </div>

            <div className="section-card">
              <div className="section-card-header">
                <div className="section-card-title">Acciones</div>
              </div>
              <div
                className="section-card-body"
                style={{ display: "flex", flexDirection: "column", gap: 8 }}
              >
                <button className="btn btn-outline btn-sm" style={{ justifyContent: "flex-start" }}>
                  ✏️ Solicitar corrección de datos
                </button>
                {persona.email_publico && (
                  <a
                    href={`mailto:${persona.email_publico}`}
                    className="btn btn-ghost btn-sm"
                    style={{ justifyContent: "flex-start" }}
                  >
                    ✉️ {persona.email_publico}
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
