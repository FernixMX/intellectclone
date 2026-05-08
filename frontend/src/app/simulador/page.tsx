"use client";

import { useState, useMemo } from "react";
import Header from "@/components/Header";

const DEPS: Record<string, number> = {
  Todas: 612,
  Ingeniería: 148,
  Medicina: 112,
  UAMRR: 98,
  Derecho: 74,
  Educación: 61,
  Comercio: 55,
  Mante: 64,
};

const SNII_NIVELES: Record<string, number> = {
  Todos: 612,
  C: 231,
  I: 187,
  II: 134,
  III: 60,
};

const AREAS: Record<string, number> = {
  Todas: 612,
  "Ciencias Exactas": 201,
  "Ciencias de la Salud": 178,
  "Ciencias Sociales": 142,
  Humanidades: 91,
};

export default function SimuladorPage() {
  const [scenario, setScenario] = useState("");
  const [tone, setTone] = useState("académico");
  const [lang, setLang] = useState("español");
  const [format, setFormat] = useState("estructurado");
  const [dep, setDep] = useState("Todas");
  const [snii, setSnii] = useState("Todos");
  const [area, setArea] = useState("Todas");

  const count = useMemo(() => {
    let b = 612;
    if (dep !== "Todas") b = Math.min(b, DEPS[dep] ?? 612);
    if (snii !== "Todos") b = Math.floor(b * ((SNII_NIVELES[snii] ?? 612) / 612));
    if (area !== "Todas") b = Math.floor(b * ((AREAS[area] ?? 612) / 612));
    return Math.max(1, b);
  }, [dep, snii, area]);

  const cost = (count * 0.013).toFixed(2);
  const mins = Math.ceil(count * 0.018);

  return (
    <div
      style={{
        background: "var(--bg-body)",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Header />

      {/* Page header */}
      <div
        style={{
          marginTop: 60,
          padding: "var(--sp-5) var(--sp-7)",
          background: "var(--bg-card)",
          borderBottom: "1px solid var(--border-color)",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)" }}>
          Simulador
        </span>
        <span style={{ color: "var(--text-light)", fontSize: 16 }}>/</span>
        <span style={{ fontSize: 14, color: "var(--text-muted)" }}>Nuevo escenario</span>
        <span
          style={{
            marginLeft: 12,
            padding: "3px 10px",
            background: "var(--orange-light)",
            color: "var(--orange)",
            fontSize: 11,
            fontWeight: 600,
            borderRadius: "var(--radius-full)",
            border: "1px solid var(--orange)",
          }}
        >
          Próximamente — Fase D
        </span>
      </div>

      {/* Two-panel layout */}
      <div className="sim-layout" style={{ flex: 1 }}>
        {/* Editor panel */}
        <div className="sim-editor">
          <div className="sim-editor-inner">
            {/* Scenario textarea */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">Escenario de simulación</div>
              </div>
              <div className="card-body">
                <textarea
                  className="scenario-ta"
                  placeholder="Describe el escenario o pregunta que quieres simular. Ejemplo: «La Universidad está considerando adoptar un modelo de educación híbrida permanente para todos los programas de licenciatura a partir de 2026. ¿Qué postura tendría la comunidad académica?»"
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                  disabled
                />
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 6 }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 11,
                      color: "var(--text-light)",
                    }}
                  >
                    {scenario.length} caracteres
                  </span>
                </div>
              </div>
            </div>

            {/* Advanced options */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">Opciones avanzadas</div>
              </div>
              <div className="card-body">
                <div className="options-grid">
                  {(
                    [
                      {
                        lbl: "Tono de respuesta",
                        val: tone,
                        set: setTone,
                        opts: ["académico", "directo", "deliberativo", "neutral"],
                      },
                      {
                        lbl: "Idioma",
                        val: lang,
                        set: setLang,
                        opts: ["español", "inglés", "bilingüe"],
                      },
                      {
                        lbl: "Formato de salida",
                        val: format,
                        set: setFormat,
                        opts: ["estructurado", "narrativo", "tabular"],
                      },
                    ] as const
                  ).map((f) => (
                    <div key={f.lbl}>
                      <label className="form-label">{f.lbl}</label>
                      <select
                        className="form-control form-select"
                        value={f.val}
                        onChange={(e) => (f.set as (v: string) => void)(e.target.value)}
                        disabled
                      >
                        {f.opts.map((o) => (
                          <option key={o}>{o}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="sim-footer">
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
                La simulación de escenarios estará disponible en la Fase D del proyecto.
              </span>
            </div>
            <button className="btn btn-outline btn-md" disabled>
              Guardar borrador
            </button>
            <button className="btn btn-primary btn-lg" disabled>
              Lanzar simulación
            </button>
          </div>
        </div>

        {/* Cohort panel */}
        <div className="sim-cohort">
          <div className="sim-cohort-inner">
            {/* Counter */}
            <div className="counter-card">
              <div className="counter-num">{count.toLocaleString("es-MX")}</div>
              <div>
                <div className="counter-lbl">gemelos seleccionados</div>
                <div className="counter-sub">de 612 disponibles en v1</div>
              </div>
            </div>

            {/* Dependencia */}
            <div>
              <div className="section-title-sm">Dependencia</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {Object.entries(DEPS).map(([d, n]) => (
                  <button
                    key={d}
                    className={`fchip${dep === d ? "active" : ""}`}
                    onClick={() => setDep(d)}
                  >
                    {d}{" "}
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 10,
                        opacity: 0.7,
                      }}
                    >
                      {n}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Nivel SNII */}
            <div>
              <div className="section-title-sm">Nivel SNII</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {Object.keys(SNII_NIVELES).map((s) => (
                  <button
                    key={s}
                    className={`fchip${snii === s ? "active" : ""}`}
                    onClick={() => setSnii(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Área */}
            <div>
              <div className="section-title-sm">Área de conocimiento</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {Object.keys(AREAS).map((a) => (
                  <button
                    key={a}
                    className={`fchip${area === a ? "active" : ""}`}
                    onClick={() => setArea(a)}
                  >
                    {a}
                  </button>
                ))}
              </div>
            </div>

            {/* Estimate */}
            <div className="estimate-card">
              <div className="section-title-sm" style={{ marginBottom: 8 }}>
                Estimación (referencial)
              </div>
              {(
                [
                  ["Costo estimado", `$${cost} USD`],
                  ["Tiempo estimado", `~${mins} min`],
                  ["Gemelos", count.toLocaleString("es-MX")],
                ] as const
              ).map(([lbl, val]) => (
                <div key={lbl} className="estimate-row">
                  <span className="estimate-lbl">{lbl}</span>
                  <span className="estimate-val">{val}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
