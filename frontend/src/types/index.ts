export interface EstadisticasGlobales {
  total_personas: number;
  total_papers: number;
  total_coautorias: number;
  total_dependencias: number;
  total_cuerpos_academicos: number;
}

export interface PersonaListItem {
  id: string;
  nombre_completo: string;
  tipo: string;
  nivel_snii: string | null;
  dependencia_id: string | null;
  cargo: string | null;
  total_publicaciones: number;
  indice_h: number;
  activa: boolean;
}

export interface PersonaRead {
  id: string;
  nombre_completo: string;
  nombre_normalizado: string;
  primer_nombre: string | null;
  apellido_paterno: string | null;
  apellido_materno: string | null;
  tipo: string;
  orcid: string | null;
  openalex_id: string | null;
  scopus_id: string | null;
  cvu_conacyt: string | null;
  google_scholar_id: string | null;
  dependencia_id: string | null;
  dependencia_nombre: string | null;
  cuerpo_academico_id: string | null;
  cargo: string | null;
  nivel_snii: string | null;
  snii_vigente_hasta: string | null;
  grado_maximo: string | null;
  grado_disciplina: string | null;
  total_publicaciones: number;
  total_citas: number;
  indice_h: number;
  indice_i10: number;
  primera_publicacion: string | null;
  ultima_publicacion: string | null;
  email_publico: string | null;
  sitio_web: string | null;
  activa: boolean;
  motivo_baja: string | null;
  fecha_baja: string | null;
  fuente_principal: string | null;
  metadatos: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface PaperListItem {
  id: string;
  doi: string | null;
  openalex_id: string | null;
  tipo: string;
  titulo: string;
  año: number | null;
  revista: string | null;
  total_citas: number;
  open_access: boolean | null;
  fuente_origen: string | null;
}

export interface Paginated<T> {
  total: number;
  limit: number;
  offset: number;
  items: T[];
  next_offset: number | null;
}

export interface TopInvestigadorItem {
  persona_id: string;
  nombre_completo: string;
  nivel_snii: string | null;
  n_papers_cosechados: number;
  total_citas: number;
  indice_h: number;
}

export interface NodoCoautoria {
  persona_id: string;
  nombre_completo: string;
  dependencia_id: string | null;
  grado: number;
}

export interface AristaCoautoria {
  persona_a_id: string;
  persona_b_id: string;
  n_papers_comunes: number;
}

export interface RedCoautoria {
  nodos: NodoCoautoria[];
  aristas: AristaCoautoria[];
  total_nodos: number;
  total_aristas: number;
}

export interface CosechaRead {
  id: string;
  fuente: string;
  estado: string;
  iniciada_at: string | null;
  completada_at: string | null;
  duracion_ms: number | null;
  registros_procesados: number;
  registros_nuevos: number;
  errores_count: number;
  disparada_manual: boolean;
  created_at: string;
}

export interface MetricasResultado {
  personas_actualizadas: number;
}

export interface SniiApiResultado {
  dependencias: number;
  personas_actualizadas: number;
  sin_match: number;
}
