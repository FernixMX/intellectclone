import Header from "@/components/Header";

const FUENTES = [
  { name: "OpenAlex", desc: "Índice académico global de acceso abierto" },
  { name: "VuFind UAT", desc: "Catálogo de la biblioteca universitaria" },
  { name: "RIUAT", desc: "Repositorio institucional de la UAT" },
  { name: "SNII — Conacyt", desc: "Datos públicos del SNI mexicano" },
];

const PRIVACIDAD = [
  "Los perfiles se construyen únicamente con publicaciones indexadas en bases de datos públicas.",
  "Los investigadores pueden solicitar revisión o corrección en cualquier momento.",
  "El acceso al simulador está restringido a personal autorizado de Rectoría.",
  "Los resultados de simulaciones son confidenciales.",
];

const TOC = [
  ["que-es", "Qué es"],
  ["como-funciona", "Cómo funciona"],
  ["fuentes", "Fuentes"],
  ["privacidad", "Privacidad"],
  ["baja", "Solicitar baja"],
  ["contacto", "Contacto"],
];

export default function AcercaPage() {
  return (
    <div style={{ background: "var(--bg-body)", minHeight: "100vh" }}>
      <Header />

      <nav className="toc">
        <div className="toc-title">Contenido</div>
        {TOC.map(([id, lbl]) => (
          <a key={id} href={`#${id}`} className="toc-link">
            {lbl}
          </a>
        ))}
      </nav>

      <main className="editorial">
        <div className="ed-eyebrow">Acerca del proyecto</div>
        <h1 className="ed-h1">IntellectClone: gemelos digitales de la comunidad académica UAT</h1>
        <p className="ed-lead">
          Un sistema de prospectiva institucional construido sobre la producción intelectual pública
          de los investigadores de la Universidad Autónoma de Tamaulipas, alineado al PDI 2024–2028.
        </p>

        <div className="ed-divider" id="que-es" />
        <h2 className="ed-h2">Qué es IntellectClone</h2>
        <p className="ed-p">
          IntellectClone cosecha, organiza y hace consultable la producción académica pública de los
          investigadores UAT. Sobre esa base, construye para cada investigador un gemelo digital:
          una representación computacional de su forma de razonar, sus áreas de interés y su estilo
          argumentativo, inferidos a partir de su huella académica.
        </p>
        <div className="ed-quote">
          <div className="ed-quote-text">
            «El gemelo digital no es una simulación de la persona: es una simulación de su
            producción académica documentada. Sólo responde con lo que está en los textos.»
          </div>
          <div className="ed-quote-src">Principio de diseño del sistema · versión 1</div>
        </div>

        <div className="ed-divider" id="como-funciona" />
        <h2 className="ed-h2">Cómo funciona</h2>
        <h3 className="ed-h3">Cosecha de datos</h3>
        <p className="ed-p">
          El sistema consulta cuatro fuentes de datos académicos de acceso público. Los datos se
          actualizan periódicamente y no se almacena información que no sea ya pública.
        </p>
        <h3 className="ed-h3">Construcción del gemelo</h3>
        <p className="ed-p">
          A partir del corpus de publicaciones, un pipeline de PLN extrae áreas temáticas,
          posiciones argumentativas y patrones de colaboración que forman la base del agente.
        </p>
        <h3 className="ed-h3">Simulación de escenarios</h3>
        <p className="ed-p">
          Los usuarios autorizados formulan preguntas, seleccionan una cohorte y el simulador
          devuelve respuestas agregadas y desagregadas con indicadores de postura, intensidad y
          consenso.
        </p>

        <div className="ed-divider" id="fuentes" />
        <h2 className="ed-h2">Fuentes de datos</h2>
        <div className="source-grid">
          {FUENTES.map((s) => (
            <div key={s.name} className="source-item">
              <div className="source-name">{s.name}</div>
              <div className="source-desc">{s.desc}</div>
            </div>
          ))}
        </div>

        <div className="ed-divider" id="privacidad" />
        <h2 className="ed-h2">Privacidad</h2>
        <p className="ed-p">
          IntellectClone procesa exclusivamente información académica de carácter público. No accede
          a datos privados.
        </p>
        <ul className="ed-list">
          {PRIVACIDAD.map((item) => (
            <li key={item} className="ed-list-item">
              <span className="ed-list-dot" />
              {item}
            </li>
          ))}
        </ul>

        <div className="ed-divider" id="baja" />
        <h2 className="ed-h2">Solicitar baja del sistema</h2>
        <p className="ed-p">
          Puedes solicitar la eliminación de tu perfil en cualquier momento. Se procesará en máximo
          10 días hábiles.
        </p>
        <a
          href="mailto:intellectclone@uat.edu.mx?subject=Solicitud%20de%20baja"
          className="btn btn-outline btn-md"
          style={{ display: "inline-flex", alignItems: "center", gap: 8 }}
        >
          Solicitar baja del sistema
        </a>

        <div className="ed-divider" id="contacto" />
        <h2 className="ed-h2">Contacto</h2>
        <div className="contact-card">
          <div className="contact-row">
            <div className="contact-label">Proyecto</div>
            <div className="contact-val">IntellectClone · UAT</div>
          </div>
          <div className="contact-row">
            <div className="contact-label">Dependencia</div>
            <div className="contact-val">Oficina de Asesores de Rectoría</div>
          </div>
          <div className="contact-row">
            <div className="contact-label">Correo</div>
            <div className="contact-val">
              <a href="mailto:intellectclone@uat.edu.mx" style={{ color: "var(--blue)" }}>
                intellectclone@uat.edu.mx
              </a>
            </div>
          </div>
          <div className="contact-row">
            <div className="contact-label">Versión</div>
            <div className="contact-val">
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>v1.0 · Mayo 2025</span>
            </div>
          </div>
        </div>
      </main>

      <footer className="pub-footer">
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span className="sidebar-logo-uat">UAT</span>
          <span className="sidebar-logo-sub">IntellectClone</span>
        </div>
        <div style={{ display: "flex", gap: 24 }}>
          {["Privacidad", "Solicitar baja", "Contacto"].map((l) => (
            <a key={l} href="#" style={{ fontSize: 13, color: "#8da2b5", textDecoration: "none" }}>
              {l}
            </a>
          ))}
        </div>
        <div style={{ fontSize: 12, color: "#506a84" }}>
          © 2025 Universidad Autónoma de Tamaulipas
        </div>
      </footer>
    </div>
  );
}
