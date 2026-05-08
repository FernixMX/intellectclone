import type {
  CosechaRead,
  EstadisticasGlobales,
  MetricasResultado,
  Paginated,
  PaperListItem,
  PersonaListItem,
  PersonaRead,
  RedCoautoria,
  SniiApiResultado,
  TopInvestigadorItem,
} from "@/types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(`${API_URL}${path}`);
  if (params) {
    Object.entries(params)
      .filter(([, v]) => v !== undefined && v !== null && v !== "")
      .forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${res.status} en ${path}`);
  }
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${res.status} en ${path}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  estadisticasGlobales: () => get<EstadisticasGlobales>("/api/v1/analitica/estadisticas-globales"),

  personas: (params?: {
    limit?: number;
    offset?: number;
    q?: string;
    tipo?: string;
    activa?: string;
    nivel_snii?: string;
    solo_uat?: boolean;
  }) =>
    get<Paginated<PersonaListItem>>("/api/v1/personas", params as Record<string, string | number>),

  persona: (id: string) => get<PersonaRead>(`/api/v1/personas/${id}`),

  papers: (params?: {
    limit?: number;
    offset?: number;
    q?: string;
    año?: number;
    persona_id?: string;
  }) => get<Paginated<PaperListItem>>("/api/v1/papers", params as Record<string, string | number>),

  topInvestigadores: (params?: { limite?: number; orden?: string }) =>
    get<{ items: TopInvestigadorItem[] }>(
      "/api/v1/analitica/top-investigadores",
      params as Record<string, string | number>
    ),

  redCoautoria: (params?: { persona_id?: string; limite_nodos?: number }) =>
    get<RedCoautoria>("/api/v1/analitica/red-coautoria", params as Record<string, string | number>),

  cosechas: (params?: { limit?: number; offset?: number }) =>
    get<Paginated<CosechaRead>>("/api/v1/cosechas", params as Record<string, string | number>),

  recalcularMetricas: () => post<MetricasResultado>("/api/v1/perfilador/metricas/recalcular"),

  cosechaSniiApi: () => post<SniiApiResultado>("/api/v1/cosechas/snii-api"),
};
