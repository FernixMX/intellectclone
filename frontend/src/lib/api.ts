import type {
  CosechaDispararResponse,
  CosechaRead,
  Dependencia,
  EstadisticasGlobales,
  MetricasResultado,
  Paginated,
  PaperListItem,
  PapersPorAnio,
  PersonaListItem,
  PersonaRead,
  RedCoautoria,
  SniiApiResultado,
  TopDependenciaItem,
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

async function post<T>(
  path: string,
  body?: unknown,
  extraHeaders?: Record<string, string>
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(extraHeaders ?? {}) },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${res.status} en ${path}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  login: (password: string) =>
    post<{ access_token: string; token_type: string }>("/api/v1/auth/login", { password }),

  estadisticasGlobales: () => get<EstadisticasGlobales>("/api/v1/analitica/estadisticas-globales"),

  papersPorAnio: () =>
    get<{ datos: PapersPorAnio[]; total_papers_historico: number }>(
      "/api/v1/analitica/papers-por-año"
    ),

  topDependencias: (params?: { limite?: number }) =>
    get<{ items: TopDependenciaItem[] }>(
      "/api/v1/analitica/top-dependencias",
      params as Record<string, string | number>
    ),

  personas: (params?: {
    limit?: number;
    offset?: number;
    q?: string;
    tipo?: string;
    activa?: string;
    nivel_snii?: string;
    solo_uat?: boolean;
    dependencia_id?: string;
    area?: string;
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

  redCoautoria: (params?: {
    persona_id?: string;
    dependencia_id?: string;
    limite_nodos?: number;
  }) =>
    get<RedCoautoria>("/api/v1/analitica/red-coautoria", params as Record<string, string | number>),

  cosechas: (params?: { limit?: number; offset?: number }) =>
    get<Paginated<CosechaRead>>("/api/v1/cosechas", params as Record<string, string | number>),

  conceptosPersona: (id: string, limite = 5) =>
    get<string[]>(`/api/v1/personas/${id}/conceptos`, { limite }),

  recalcularMetricas: (token?: string) =>
    post<MetricasResultado>(
      "/api/v1/perfilador/metricas/recalcular",
      undefined,
      token ? { Authorization: `Bearer ${token}` } : undefined
    ),

  cosechaSniiApi: (token?: string) =>
    post<SniiApiResultado>(
      "/api/v1/cosechas/snii-api",
      undefined,
      token ? { Authorization: `Bearer ${token}` } : undefined
    ),

  cosechaOpenAlexCompleta: (token?: string) =>
    post<CosechaDispararResponse>(
      "/api/v1/cosechas/openalex-completa",
      undefined,
      token ? { Authorization: `Bearer ${token}` } : undefined
    ),

  cosechaVuFindCompleta: (token?: string) =>
    post<CosechaDispararResponse>(
      "/api/v1/cosechas/vufind-completa",
      undefined,
      token ? { Authorization: `Bearer ${token}` } : undefined
    ),

  cosechaCrossrefEnrich: (token?: string) =>
    post<CosechaDispararResponse>(
      "/api/v1/cosechas/crossref-enrich",
      undefined,
      token ? { Authorization: `Bearer ${token}` } : undefined
    ),

  cosechaOrcidEnrich: (token?: string) =>
    post<CosechaDispararResponse>(
      "/api/v1/cosechas/orcid-enrich",
      undefined,
      token ? { Authorization: `Bearer ${token}` } : undefined
    ),

  dependencias: (params?: { limit?: number; offset?: number }) =>
    get<Paginated<Dependencia>>("/api/v1/dependencias", params as Record<string, string | number>),

  conceptosFrecuentes: (limite = 20) =>
    get<string[]>("/api/v1/analitica/conceptos-frecuentes", { limite }),
};
