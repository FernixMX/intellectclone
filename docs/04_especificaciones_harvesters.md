# IntellectClone — Especificaciones de harvesters

**Documento técnico 04 — Cosechadores de fuentes externas**
**Versión 0.1**
**Audiencia:** Claude Code (constructor) + revisión humana de Fernando

---

## Índice

1. [Filosofía de la cosecha](#1-filosofía-de-la-cosecha)
2. [Arquitectura del sistema de cosecha](#2-arquitectura-del-sistema-de-cosecha)
3. [Harvester base (interfaz común)](#3-harvester-base-interfaz-común)
4. [OpenAlex Harvester (fuente principal)](#4-openalex-harvester-fuente-principal)
5. [VuFind UAT Harvester](#5-vufind-uat-harvester)
6. [RIUAT Harvester](#6-riuat-harvester)
7. [SNII UAT Harvester](#7-snii-uat-harvester)
8. [ORCID Harvester (desambiguación)](#8-orcid-harvester-desambiguación)
9. [Crossref Harvester (respaldo)](#9-crossref-harvester-respaldo)
10. [Web Harvesters opcionales (ResearchGate, Academia.edu, web personal)](#10-web-harvesters-opcionales)
11. [Normalizador y desambiguador](#11-normalizador-y-desambiguador)
12. [Deduplicación de papers](#12-deduplicación-de-papers)
13. [Manejo de PDFs y abstracts](#13-manejo-de-pdfs-y-abstracts)
14. [Panel admin de cosechas](#14-panel-admin-de-cosechas)
15. [Tests de aceptación](#15-tests-de-aceptación)

---

## 1. Filosofía de la cosecha

La cosecha es el primer eslabón del sistema. Si la cosecha trae datos limpios, normalizados y con buena trazabilidad, todo lo demás funciona. Si trae datos sucios, el perfilador genera gemelos basados en información ruidosa y todo el sistema pierde credibilidad.

### Cinco principios

**Primero, control humano explícito.** Por decisión de Fernando, **toda cosecha se dispara manualmente desde el panel admin**. No hay cron jobs, no hay sincronización automática, no hay polling silencioso. El admin decide cuándo cosechar, qué fuente, con qué parámetros. Esto va en contra de la práctica común pero refleja la filosofía del proyecto: control humano sobre cada decisión que afecta los datos institucionales.

**Segundo, fuente principal + complementos.** OpenAlex es la fuente primaria de papers. Las demás fuentes (VuFind UAT, RIUAT, SNII UAT, ORCID, Crossref) complementan, validan o enriquecen lo que OpenAlex ya tiene. Si OpenAlex está caído, el sistema sigue funcionando con lo cosechado previamente; no hay dependencia crítica única.

**Tercero, metadatos primero, PDFs bajo demanda.** La cosecha solo trae metadatos: título, autores, abstract, DOI, año, citas, conceptos. Los PDFs no se descargan en cosecha. Solo se descargan cuando el admin dispara generar un gemelo de una persona específica, y solo se descargan los PDFs de esa persona. Esto reduce drásticamente el costo computacional y de ancho de banda, y respeta a las fuentes externas evitando requests masivos innecesarios.

**Cuarto, deduplicación automática fuerte.** Un mismo paper puede aparecer en OpenAlex, Crossref, RIUAT y VuFind UAT al mismo tiempo. El sistema detecta y consolida automáticamente, sin pedir confirmación humana cuando hay match por DOI, ORCID o identificador OpenAlex (alta confianza). Solo casos fuzzy (sin identificadores, solo similitud de título + autores + año con score 0.85-0.95) se marcan para revisión humana.

**Quinto, observabilidad completa.** Cada corrida de cosecha registra: cuándo empezó, cuándo terminó, qué fuente, qué parámetros, cuántos registros procesó, cuántos eran nuevos, cuántos eran actualizaciones, cuántos fueron descartados, qué errores ocurrieron, en qué momento ocurrieron, con qué causa raíz. El admin puede consultar el histórico completo desde el panel.

### Lo que la cosecha NO hace

- No genera gemelos. La cosecha solo trae datos. La generación de gemelos es proceso separado.
- No descarga PDFs (excepto bajo demanda al generar gemelo).
- No analiza contenido. Solo cataloga metadatos.
- No envía notificaciones a las personas cosechadas. La cosecha es invisible para los retratados.

---

## 2. Arquitectura del sistema de cosecha

### Componentes

El sistema de cosecha vive en `backend/intellectclone/harvesters/` y consiste en:

```
harvesters/
├── __init__.py
├── base.py                    # Clase BaseHarvester (interfaz común)
├── openalex.py                # OpenAlexHarvester
├── vufind_uat.py              # VuFindUATHarvester
├── riuat.py                   # RIUATHarvester
├── snii_uat.py                # SNIIUATHarvester
├── orcid.py                   # OrcidHarvester
├── crossref.py                # CrossrefHarvester
├── web/
│   ├── researchgate.py        # opcional, v1 puede omitirlo
│   ├── academia_edu.py        # opcional, v1 puede omitirlo
│   └── cv_publico.py          # opcional, v1 puede omitirlo
├── normalizer.py              # Normalización post-cosecha
├── deduplicator.py            # Deduplicación de papers
├── disambiguator.py           # Desambiguación de autores
└── runner.py                  # Orquestador de corridas
```

### Tareas Celery

Cada cosecha se ejecuta como una tarea Celery asíncrona. El admin dispara desde la UI; FastAPI encola la tarea; Celery la ejecuta en background; la UI hace polling del estado por API.

### Flujo de una corrida

```
[Admin presiona "Cosechar OpenAlex" en panel]
    ↓
[FastAPI valida permisos y crea registro `cosecha` con estado=programada]
    ↓
[Encola tarea Celery con cosecha_id]
    ↓
[Celery worker toma la tarea]
    ↓
[Marca cosecha como estado=en_curso]
    ↓
[Ejecuta el OpenAlexHarvester]
    ↓
[Para cada batch de resultados:
    - Validar
    - Normalizar
    - Desambiguar autores
    - Deduplicar
    - Persistir en PostgreSQL
    - Actualizar contadores en cosecha]
    ↓
[Si todo OK: estado=completada]
[Si errores no críticos: estado=completada_con_errores]
[Si error crítico: estado=fallida]
    ↓
[Notificación al admin (email + notificación in-app)]
```

---

## 3. Harvester base (interfaz común)

Todos los harvesters implementan esta interfaz para que el orquestador los trate uniformemente.

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from datetime import datetime

class BaseHarvester(ABC):
    """Interfaz común para todos los harvesters de IntellectClone."""

    nombre: str                           # 'openalex', 'vufind_uat', etc.
    fuente_tipo: TipoFuente                # enum del modelo de datos
    rate_limit_requests_por_segundo: float  # configuración por harvester

    @abstractmethod
    async def configurar(self, config: dict) -> None:
        """Recibe configuración: API keys, límites, parámetros."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Verifica que la fuente está disponible antes de empezar."""
        ...

    @abstractmethod
    async def cosechar(
        self,
        cosecha_id: UUID,
        modo: str,                       # 'completa' | 'incremental' | 'persona_individual'
        parametros: dict,                # parámetros específicos por modo
    ) -> AsyncIterator[ResultadoCosecha]:
        """
        Generador asíncrono que va emitiendo resultados conforme cosecha.
        Cada yield es un objeto con metadatos de un paper o persona.
        """
        ...

    @abstractmethod
    async def parsear_registro(self, raw_data: dict) -> dict:
        """
        Convierte el formato nativo de la fuente al formato canónico
        del sistema. Implementación específica por fuente.
        """
        ...

    async def manejar_error(
        self,
        error: Exception,
        contexto: dict,
        intento: int
    ) -> ResultadoIntento:
        """
        Política común de manejo de errores con backoff:
        - Intento 1: reintentar después de 60 seg
        - Intento 2: reintentar después de 5 min
        - Intento 3: reintentar después de 30 min
        - Intento 4+: marcar registro como error y continuar
        """
        ...
```

### Política de errores común

Implementada en `BaseHarvester.manejar_error`:

**Errores transitorios** (red, timeout, 5xx, 429): retry con backoff exponencial. Después de 3 intentos, registrar en log y continuar con el siguiente registro. NO detiene la cosecha.

**Errores de autenticación** (401, 403): detener inmediatamente, marcar cosecha como fallida, alertar admin (problema de configuración).

**Errores de validación** (registro mal formado): registrar en log con `nivel=warning`, descartar el registro, continuar.

**Errores críticos** (error de programación, OOM, panic): detener cosecha, marcar como fallida, alertar admin con stack trace completo.

### Estructura del log estructurado

Cada error se registra con esta estructura JSON:

```json
{
  "cosecha_id": "uuid",
  "timestamp": "2026-05-03T14:32:11Z",
  "fuente": "openalex",
  "nivel": "error",
  "tipo_error": "rate_limit",
  "mensaje": "OpenAlex returned 429 after 3 retries",
  "contexto": {
    "openalex_id": "W1234567890",
    "intento": 4,
    "ultimo_status": 429,
    "headers_relevantes": {...}
  },
  "stack_trace": "..."
}
```

Esta es la estructura que respeta tu pedido explícito de "dejar claro cuándo, cómo y por qué falló".

---

## 4. OpenAlex Harvester (fuente principal)

### Por qué es la principal

OpenAlex es la fuente más completa y confiable disponible para este caso de uso:
- Cobertura masiva: ~250M de papers indexados, incluye Scopus, Web of Science, fuentes locales.
- API gratuita, sin API key obligatoria (solo email para "polite pool" con prioridad).
- Filtrado por afiliación institucional vía ROR ID o nombre.
- Datos ricos: DOI, autores con sus IDs, abstract, citas por año, conceptos, open access status.
- Identificador único `openalex_id` que permite tracking estable.

### Configuración

```python
config = {
    "polite_pool_email": "fernando@uat.edu.mx",  # registrado en OpenAlex
    "ror_id_uat": "https://ror.org/00qm7vk32",   # ROR ID de la UAT
    "rate_limit_rps": 10.0,                       # 10 requests/seg en polite pool
    "max_works_por_corrida": 5000,                # límite seguro
    "user_agent": "IntellectClone/1.0 (mailto:fernando@uat.edu.mx)"
}
```

### Modos de cosecha

**Modo `completa`:** trae todos los papers UAT existentes.
- Endpoint: `/works?filter=institutions.ror:00qm7vk32`
- Paginación con cursor, 200 papers por página.
- Estimado para UAT: ~3,771 papers, ~20 páginas, ~3-5 minutos.

**Modo `incremental`:** trae solo lo nuevo desde última cosecha exitosa.
- Endpoint: `/works?filter=institutions.ror:00qm7vk32,from_publication_date:YYYY-MM-DD`
- Fecha tomada del último `cosecha.completada_at` con estado completada.

**Modo `persona_individual`:** trae los papers de una persona específica.
- Endpoint: `/works?filter=author.id:A1234567890`
- Útil cuando se va a regenerar un gemelo y se quiere asegurar que tiene el corpus completo.

### Mapeo de campos OpenAlex → modelo IntellectClone

| Campo OpenAlex | Campo `paper` | Notas |
|---|---|---|
| `id` | `openalex_id` | quitar prefijo URL |
| `doi` | `doi` | quitar prefijo `https://doi.org/` |
| `title` | `titulo` | |
| `abstract_inverted_index` | `abstract_texto` | reconstruir desde inverted index |
| `publication_year` | `año` | |
| `publication_date` | `fecha_publicacion` | |
| `language` | `idioma` | ISO 639-1 |
| `primary_location.source.display_name` | `revista` | |
| `primary_location.source.issn_l` | `issn` | |
| `host_organization` | `editorial` | |
| `biblio.volume / issue / first_page-last_page` | `volumen / numero / paginas` | |
| `open_access.is_oa` | `open_access` | |
| `primary_location.pdf_url` | `url_pdf` | |
| `primary_location.landing_page_url` | `url_landing` | |
| `cited_by_count` | `total_citas` | |
| `counts_by_year` | `citas_por_año` | array → JSONB |
| `concepts[].display_name` | `conceptos` | array de strings |
| `authorships[]` | tabla `coautoria` | uno por autor |
| `type` | `tipo` | mapear: `journal-article` → `articulo`, etc. |

### Mapeo de autorías

Para cada `authorship` en `authorships[]`:

```python
authorship = {
    "author": {
        "id": "A1234567890",
        "display_name": "Maria Elena Cardenas Ruiz",
        "orcid": "https://orcid.org/0000-0002-1234-5678"
    },
    "institutions": [
        {
            "id": "I1234567890",
            "ror": "https://ror.org/00qm7vk32",
            "display_name": "Universidad Autónoma de Tamaulipas"
        }
    ],
    "author_position": "first",
    "is_corresponding": True
}
```

Por cada autorship donde `institutions` incluya el ROR de la UAT, se busca o crea una `persona` con:
- `openalex_id` = `author.id` sin prefijo
- `orcid` = `author.orcid` si existe
- `nombre_completo` = `author.display_name`
- `tipo` = `investigador` (default)

Y se crea una fila en `coautoria`:
- `posicion` derivada de `author_position` (first=1, middle=2, last=N)
- `es_primer_autor` = (`author_position == "first"`)
- `es_autor_correspondiente` = `is_corresponding`
- `metodo_match` = `'orcid'` si tiene ORCID, `'openalex'` si no.

### Política de cosecha estricta UAT

Por decisión de Fernando, solo se crean filas en `persona` para autores con afiliación UAT confirmada (ROR match). Los coautores externos:
- Si tienen `openalex_id`, se almacenan como personas con `tipo='externo'` y `dependencia_id=NULL`.
- Si NO tienen `openalex_id`, su nombre se guarda solo en `coautoria.afiliacion_declarada` como texto crudo, sin crear persona.

Esto garantiza que el grafo de coautoría queda completo (sabemos con quién publicó cada autor UAT) sin generar centenares de "personas externas" sombra.

### Tests de aceptación OpenAlex

- Cosecha completa de UAT trae al menos 3,500 papers (referencia: portal indica 3,771).
- Toda persona creada tiene `openalex_id` no nulo.
- Toda persona tiene al menos 1 fila en `coautoria`.
- Ningún paper está duplicado (mismo `openalex_id` no aparece en dos filas).
- El reconstructor de abstract desde `abstract_inverted_index` produce texto legible para el 95%+ de papers.

---

## 5. VuFind UAT Harvester

### Estatus de la fuente

VuFind UAT está en `https://publicaciones.uat.edu.mx/vufind/` y agrega vía OAI-PMH varias fuentes UAT: el RIUAT, EduCiencia (revista institucional), OJS UAT, otros OJS/OMP institucionales. La API REST oficial está bloqueada (403), pero la búsqueda HTML funciona y devuelve identificadores estables.

### Estrategia

Como la API REST no es accesible, la cosecha es por **scraping HTML estructurado** de las páginas de búsqueda y registro:

- Página de búsqueda: `https://publicaciones.uat.edu.mx/vufind/Search/Results?lookfor=&type=AllFields&limit=20&page=N`
- Página de registro individual: `https://publicaciones.uat.edu.mx/vufind/Record/{record_id}`

### Configuración

```python
config = {
    "base_url": "https://publicaciones.uat.edu.mx/vufind",
    "rate_limit_rps": 1.0,                # bajo, respetar servidor UAT
    "max_paginas_por_corrida": 100,
    "timeout_segundos": 30,
    "user_agent": "IntellectClone/1.0 (uso institucional UAT)"
}
```

### Parsing

Cada página de resultados contiene cards `<div class="result">` con metadatos básicos. Cada card tiene un link `<a class="title">` al registro completo. El registro completo tiene:
- `<h1 class="record-title">` → título
- `<span class="author">` → autores (texto)
- `<dt>Año:</dt><dd>YYYY</dd>` → año
- `<dt>Tipo:</dt><dd>...</dd>` → tipo (artículo, tesis, libro, etc.)
- `<a class="fulltext-link">` → URL al PDF/landing si existe

### Mapeo

| Campo VuFind | Campo `paper` |
|---|---|
| record_id | `metadatos.vufind_id` (no es campo directo, va a JSONB) |
| título | `titulo` |
| año | `año` |
| tipo (mapeado) | `tipo` |
| URL fulltext | `url_landing` |
| autor texto | parsing manual + match contra `persona` existente |

### Match contra OpenAlex

Cada paper cosechado de VuFind se intenta matchear contra la tabla `paper` ya poblada por OpenAlex:
1. Si tiene DOI extraíble del registro → match por DOI.
2. Si no, fuzzy match por título normalizado + año (similitud >0.95).

Si match → se actualiza el paper existente agregando `metadatos.fuentes_secundarias = ["vufind_uat"]` y eventuales campos faltantes (handle, URL local).

Si no match → se crea un nuevo registro con `fuente_origen='vufind_uat'`. Esto cubre papers locales no indexados en OpenAlex (revistas UAT internas).

### Tests de aceptación VuFind

- La cosecha completa devuelve al menos 500 registros (estimación conservadora).
- Al menos 30% de los registros matchean con OpenAlex (los que están en revistas indexadas).
- Los registros que no matchean (locales puros) tienen título, autor y año correctamente extraídos.

---

## 6. RIUAT Harvester

### Estatus de la fuente

RIUAT (Repositorio Institucional UAT) en `https://riuat.uat.edu.mx` corre sobre DSpace. Solo tiene 920 documentos en total: 556 artículos, 200 tesis de maestría, 105 libros, 38 tesis de doctorado, 21 capítulos de libro.

OAI-PMH y REST API parecen caídos (devolvieron 503 en pruebas). El handler primario es por scraping HTML por handle.

### Estrategia

**Intento primario:** usar OAI-PMH si revive. Endpoint estándar DSpace: `https://riuat.uat.edu.mx/oai/request?verb=ListRecords&metadataPrefix=oai_dc&set=col_handle_X`.

**Fallback (probable estrategia real):** scraping HTML iterando handles.
- Listado de comunidades: `https://riuat.uat.edu.mx/handle/123456789/X`
- Cada item: `https://riuat.uat.edu.mx/handle/123456789/{N}`

### Configuración

```python
config = {
    "base_url": "https://riuat.uat.edu.mx",
    "oai_endpoint": "https://riuat.uat.edu.mx/oai/request",
    "rate_limit_rps": 0.5,
    "preferir_oai": True,                # intentar OAI primero, fallback a HTML
    "max_handles_por_corrida": 1000      # cubre casi todo el repositorio
}
```

### Mapeo OAI Dublin Core → modelo

| OAI DC | Campo `paper` |
|---|---|
| `dc:identifier` (handle) | `handle_riuat` |
| `dc:title` | `titulo` |
| `dc:creator` | autores → `coautoria` |
| `dc:date` | `fecha_publicacion` |
| `dc:type` | `tipo` (mapear: "Tesis Maestría" → `tesis_maestria`, etc.) |
| `dc:description` | `abstract_texto` |
| `dc:language` | `idioma` |

### Caso especial: tesis

Las tesis son contenido único de RIUAT que no está en OpenAlex. Para cada tesis:
- `tipo` = `tesis_doctorado` o `tesis_maestria` según mapeo.
- El `dc:creator` es el autor de la tesis (estudiante).
- Se crea persona con `tipo='estudiante'` si no existía.
- Director(es) de tesis aparecen en `dc:contributor`. Se matchean contra `persona` existente UAT.

### Tests de aceptación RIUAT

- Cosecha completa trae al menos 800 registros (RIUAT reporta 920).
- Los 200 registros tipo tesis tienen autor (estudiante) y al menos un director identificado.
- Match con OpenAlex: ~70% de artículos RIUAT matchean (los que tienen DOI); el resto son locales.

---

## 7. SNII UAT Harvester

### Estatus de la fuente

El portal `produccioncientifica.uat.edu.mx` tiene varias páginas relevantes:
- `Buscador.aspx` — búsqueda de investigadores SNII.
- `Proyectos.aspx` — proyectos vigentes.
- `CampusCA.aspx` — cuerpos académicos.

Es ASP.NET WebForms con ViewState y postbacks AJAX. **Es la fuente más compleja de cosechar.**

### Estrategia

Usar **Playwright** (browser automation) en lugar de requests directos, porque el contenido se carga vía JavaScript y postbacks.

```python
config = {
    "base_url": "https://produccioncientifica.uat.edu.mx",
    "headless": True,
    "timeout_ms": 60000,
    "rate_limit_segundos_entre_requests": 3.0,  # respetuoso con el servidor
    "user_agent_browser": "Mozilla/5.0 IntellectClone/1.0"
}
```

### Cosecha de cuerpos académicos

Más simple porque el listado parece ser estático:

1. Navegar a `CampusCA.aspx`.
2. Para cada campus en el dropdown (Victoria, Tampico, Reynosa, etc.):
   - Seleccionar campus.
   - Esperar carga AJAX.
   - Extraer tabla de cuerpos académicos.
   - Para cada CA: nombre, estatus, dependencia, líneas de generación.
3. Persistir en tabla `cuerpo_academico`.

### Cosecha de investigadores SNII

Más compleja porque requiere búsqueda iterativa:

1. Navegar a `Buscador.aspx`.
2. Iterar por dependencia (todas las facultades UAT).
3. Para cada resultado: nombre, nivel SNII, área, cuerpo académico al que pertenece.
4. Match contra `persona` existente (cosechada por OpenAlex) por nombre normalizado + dependencia.
5. Actualizar `persona.nivel_snii`, `persona.cuerpo_academico_id`.

Si no hay match, se crea persona con `tipo='investigador'` y `fuente_principal='snii_uat'`.

### Cosecha de proyectos

Opcional para v1, marcar como "implementar después":

- Navegar a `Proyectos.aspx`.
- Extraer proyectos vigentes.
- Esto requiere una tabla `proyecto` que NO está en el modelo de datos de v1. Se posterga a v2.

### Manejo de antiscraping

ASP.NET sites a veces tienen captchas o bloqueos. Si el harvester detecta:
- HTTP 403 sostenido.
- Captcha en la respuesta.
- Cambio inesperado de estructura HTML.

Detiene la cosecha, marca como fallida, alerta al admin con captura de pantalla del estado para diagnóstico.

### Tests de aceptación SNII UAT

- Cosecha completa trae al menos 500 investigadores SNII.
- Cada investigador SNII tiene nivel asignado (candidato, nivel_1, nivel_2, nivel_3 o emerito).
- Al menos 70% de los investigadores SNII matchean con personas ya cosechadas por OpenAlex.
- Cuerpos académicos: al menos 80 cosechados (estimación basada en universidad pública mediana).

---

## 8. ORCID Harvester (desambiguación)

### Propósito

ORCID no es fuente principal de papers (ya los tenemos por OpenAlex), pero es **la fuente de oro para desambiguar autores**. Si una persona tiene ORCID confirmado, todos los papers que aparezcan en su ORCID son inequívocamente suyos.

### Configuración

```python
config = {
    "base_url": "https://pub.orcid.org/v3.0",
    "rate_limit_rps": 12.0,            # ORCID es generoso
    "user_agent": "IntellectClone/1.0"
}
```

### Modo de uso

Se ejecuta como **enriquecedor**, no como cosechador masivo. Para cada persona en la base con `orcid` no nulo:

1. GET `https://pub.orcid.org/v3.0/{orcid}/works`
2. Extraer lista de DOIs de los works.
3. Para cada DOI:
   - Si existe en `paper` → asegurar que la `coautoria` tiene `metodo_match='orcid'` y `confianza_match=1.0`.
   - Si no existe → marcar para investigación (puede ser un paper que OpenAlex no tiene).

### Tests de aceptación ORCID

- Para personas con ORCID confirmado, al menos 90% de los papers en la base tienen `coautoria.metodo_match='orcid'`.
- ORCID detecta papers faltantes en al menos 5% de los casos (usual).

---

## 9. Crossref Harvester (respaldo)

### Propósito

Crossref tiene la base canónica de DOIs. Se usa solo para:
- Validar metadatos de papers cuyo DOI sea sospechoso (formato extraño, conflicto entre fuentes).
- Resolver papers que aparecen en VuFind o RIUAT con datos incompletos pero tienen DOI.

NO es fuente primaria. NO se hace cosecha masiva contra Crossref.

### Configuración

```python
config = {
    "base_url": "https://api.crossref.org",
    "rate_limit_rps": 50.0,            # polite pool con email
    "user_agent": "IntellectClone/1.0 (mailto:fernando@uat.edu.mx)"
}
```

### Modo de uso

Solo bajo demanda. Endpoint: `/works/{doi}`.

---

## 10. Web Harvesters opcionales

Por decisión de Fernando de "fuentes amplias con riesgo asumido", el sistema puede cosechar opcionalmente:

- **ResearchGate**: requiere autenticación, ToS prohíben scraping. **Opcional, alto riesgo, postergar a v1.5.**
- **Academia.edu**: similar a ResearchGate. **Opcional, postergar.**
- **CV público / sitio web personal**: si la persona tiene URL pública conocida, se descarga el HTML, se extrae texto plano, se almacena como `documento_corpus` con `tipo='cv_publico'`.

Para v1 inicial, mi recomendación operativa es **omitir ResearchGate y Academia.edu** y solo implementar cosecha de CV/sitio personal cuando el admin lo configure manualmente persona por persona. Esto reduce riesgo legal y de bloqueo manteniendo la opción.

### Configuración para sitios personales

```python
config = {
    "rate_limit_rps_por_dominio": 0.5,
    "max_paginas_por_sitio": 20,
    "respetar_robots_txt": True,
    "user_agent": "IntellectClone/1.0 (uso institucional UAT, contacto: fernando@uat.edu.mx)"
}
```

El admin pega una URL en el panel de la persona; el sistema descarga, extrae texto plano (con `trafilatura` o similar), guarda en `documento_corpus`.

---

## 11. Normalizador y desambiguador

### Normalización de nombres

Pipeline para `persona.nombre_normalizado`:

```python
def normalizar_nombre(nombre: str) -> str:
    """
    Convierte 'María Elena Cárdenas-Ruiz' a 'maria elena cardenas ruiz'.
    Hace match-friendly sin perder información.
    """
    import unicodedata
    # 1. Lowercase
    n = nombre.lower()
    # 2. Eliminar acentos (NFKD descompone, encode/decode quita marcas)
    n = unicodedata.normalize('NFKD', n)
    n = n.encode('ASCII', 'ignore').decode('ASCII')
    # 3. Reemplazar guiones y puntos por espacios
    n = n.replace('-', ' ').replace('.', ' ')
    # 4. Colapsar espacios múltiples
    n = ' '.join(n.split())
    return n
```

### Desambiguación de autores (cascada)

Por decisión de Fernando: ORCID prioritario, OpenAlex como fallback. Implementación de la cascada:

```python
def desambiguar_autor(authorship: dict, db) -> Persona:
    """
    Recibe un authorship de OpenAlex y devuelve la persona correcta.
    Crea persona nueva si no existe match confiable.
    """
    # Nivel 1: ORCID (confianza 1.0)
    orcid = authorship.get('author', {}).get('orcid')
    if orcid:
        orcid_clean = orcid.replace('https://orcid.org/', '')
        existente = db.query(Persona).filter(Persona.orcid == orcid_clean).first()
        if existente:
            return existente

    # Nivel 2: OpenAlex Author ID (confianza 0.95)
    openalex_author_id = authorship.get('author', {}).get('id', '').split('/')[-1]
    if openalex_author_id:
        existente = db.query(Persona).filter(
            Persona.openalex_id == openalex_author_id
        ).first()
        if existente:
            # Si el authorship tiene ORCID y el existente no, actualizar
            if orcid and not existente.orcid:
                existente.orcid = orcid_clean
            return existente

    # Nivel 3: Fuzzy match por nombre + dependencia (confianza variable)
    nombre = authorship.get('author', {}).get('display_name', '')
    nombre_norm = normalizar_nombre(nombre)
    instituciones = authorship.get('institutions', [])

    candidatos = db.query(Persona).filter(
        Persona.nombre_normalizado.op('%')(nombre_norm)  # pg_trgm similarity
    ).all()

    mejor = None
    mejor_score = 0.0
    for cand in candidatos:
        score = ratio_similitud(nombre_norm, cand.nombre_normalizado)
        # Boost si comparten dependencia
        if instituciones and cand.dependencia_id:
            for inst in instituciones:
                if inst.get('ror') == ROR_UAT and cand.dependencia_id is not None:
                    score += 0.05
        if score > mejor_score:
            mejor = cand
            mejor_score = score

    # Decisión final
    if mejor and mejor_score >= 0.95:
        return mejor                    # match confiable, usar existente
    elif mejor and mejor_score >= 0.85:
        # Match dudoso, marcar para revisión humana
        marcar_para_revision_dedup(authorship, mejor, mejor_score)
        return crear_persona_nueva(authorship)  # crear y dejar que admin decida
    else:
        return crear_persona_nueva(authorship)  # claramente no es la misma
```

---

## 12. Deduplicación de papers

### Algoritmo de deduplicación

Por decisión de Fernando: dedup automática fuerte. Implementación:

```python
def deduplicar_paper(paper_nuevo: dict, db) -> tuple[Paper, bool]:
    """
    Devuelve (paper_canonico, es_duplicado).
    Si es_duplicado=True, paper_nuevo se descartó y paper_canonico se actualizó.
    """
    # Nivel 1: DOI (match exacto, confianza absoluta)
    doi = paper_nuevo.get('doi')
    if doi:
        doi_norm = normalizar_doi(doi)
        existente = db.query(Paper).filter(Paper.doi == doi_norm).first()
        if existente:
            consolidar_metadatos(existente, paper_nuevo)
            return existente, True

    # Nivel 2: OpenAlex ID
    openalex_id = paper_nuevo.get('openalex_id')
    if openalex_id:
        existente = db.query(Paper).filter(Paper.openalex_id == openalex_id).first()
        if existente:
            consolidar_metadatos(existente, paper_nuevo)
            return existente, True

    # Nivel 3: Handle RIUAT
    handle = paper_nuevo.get('handle_riuat')
    if handle:
        existente = db.query(Paper).filter(Paper.handle_riuat == handle).first()
        if existente:
            consolidar_metadatos(existente, paper_nuevo)
            return existente, True

    # Nivel 4: Fuzzy match (título + año + primer autor)
    titulo_norm = normalizar_titulo(paper_nuevo['titulo'])
    año = paper_nuevo.get('año')
    primer_autor = obtener_primer_autor(paper_nuevo)

    if titulo_norm and año and primer_autor:
        candidatos = db.query(Paper).filter(
            Paper.año == año,
            Paper.titulo_normalizado.op('%')(titulo_norm)
        ).all()

        for cand in candidatos:
            sim = ratio_similitud(titulo_norm, cand.titulo_normalizado)
            if sim >= 0.95:
                primer_autor_existente = obtener_primer_autor_de_paper(cand)
                if nombres_coinciden(primer_autor, primer_autor_existente):
                    consolidar_metadatos(cand, paper_nuevo)
                    return cand, True
            elif sim >= 0.85:
                # Marcar para revisión humana
                marcar_paper_para_revision_dedup(paper_nuevo, cand, sim)

    # No es duplicado: crear nuevo
    return crear_paper(paper_nuevo), False
```

### Consolidación de metadatos

Cuando un paper duplicado se detecta, se actualiza el existente:
- Campos `null` en el existente que están presentes en el nuevo → se llenan.
- Campos no nulos en ambos → gana el de fuente más confiable (jerarquía: OpenAlex > Crossref > VuFind > RIUAT).
- `metadatos.fuentes_secundarias` se agrega como array para registrar todas las fuentes que reportaron el mismo paper.

---

## 13. Manejo de PDFs y abstracts

### Filosofía: solo lo necesario, cuando se necesita

Por decisión de Fernando, los PDFs **no se descargan en cosecha**. Solo cuando se va a generar un gemelo de una persona específica.

### Workflow de generación de corpus para gemelo

Cuando admin dispara "generar gemelo de persona X":

1. Sistema lista todos los `paper` donde X es coautor.
2. Sistema separa los papers en dos grupos:
   - **Con abstract**: usa el abstract directamente.
   - **Sin abstract**: descarga PDF si tiene `url_pdf`, extrae texto, guarda como `documento_corpus`.
3. Sistema concatena: abstracts + textos extraídos + documentos manuales subidos = corpus.
4. Corpus va al perfilador.

### Modo económico vs modo profundo

El admin elige al disparar:

- **Modo económico** (default): solo abstracts, sin descargar PDFs. Rápido, gratis (cero LLM tokens en cosecha), corpus más corto. Adecuado para personas con 30+ papers donde los abstracts ya dan riqueza suficiente.
- **Modo profundo**: descarga PDFs, extrae textos completos, corpus maximizado. Mejor calidad de gemelo, costo más alto en LLM tokens (corpus 3-5x más grande). Adecuado para personas VIP o con pocos papers donde necesitas exprimir cada texto.

Decisión por persona, registrada en `gemelo.metadatos.modo_corpus`.

### Extracción de texto desde PDF

Librería recomendada: `pypdf` para PDFs simples, `pdfplumber` para PDFs con tablas o layout complejo. Si el PDF está escaneado (sin texto, solo imagen), se omite con warning.

```python
def extraer_texto_pdf(pdf_path: str) -> tuple[str, dict]:
    """Devuelve (texto, metadata)."""
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    paginas = []
    for pagina in reader.pages:
        texto = pagina.extract_text()
        if texto:
            paginas.append(texto)
    texto_completo = '\n\n'.join(paginas)
    metadata = {
        'total_paginas': len(reader.pages),
        'paginas_con_texto': len(paginas),
        'es_escaneado': len(paginas) < len(reader.pages) * 0.5
    }
    return texto_completo, metadata
```

### Almacenamiento de PDFs

Los PDFs descargados se almacenan en `/var/intellectclone/storage/pdfs/{paper_id}.pdf`. La ruta se registra en `documento_corpus.archivo_path`. Después de extraer el texto, el PDF se conserva (puede ser útil para futura regeneración con mejor OCR).

---

## 14. Panel admin de cosechas

Como las cosechas son manuales, el panel admin es **crítico**. Sin él, el sistema no funciona.

### Pantalla principal: estado de fuentes

Tabla con una fila por fuente:

| Fuente | Última cosecha | Registros nuevos | Estado | Acción |
|---|---|---|---|---|
| OpenAlex | hace 2 días | +47 papers | OK | Cosechar ahora |
| VuFind UAT | hace 2 días | +12 registros | OK | Cosechar ahora |
| RIUAT | hace 5 días | +3 tesis | OK | Cosechar ahora |
| SNII UAT | hace 30 días | +5 SNII actualizados | Atrasada | **Cosechar ahora** |
| ORCID enriquecimiento | hace 1 día | 156 personas enriquecidas | OK | Cosechar ahora |

Cada botón "Cosechar ahora" abre un modal:
- Modo (completa / incremental / persona individual).
- Confirmación con costo estimado (ancho de banda, no tokens).
- Botón "Iniciar cosecha".

### Pantalla detalle: corrida en progreso

Cuando una cosecha está en curso, el admin puede ver:

- Progreso (registros procesados / estimados, %).
- Velocidad (registros por minuto).
- ETA estimado.
- Log en vivo de errores (si los hay).
- Botón "Cancelar".

### Pantalla histórico

Tabla con todas las corridas pasadas:

| Fecha | Fuente | Modo | Estado | Duración | Nuevos | Actualizados | Errores |

Click en una corrida abre detalle completo con log estructurado de errores.

### Notificaciones

Cuando una cosecha completa, falla o termina con errores, el admin recibe:
- Notificación in-app (campana en navegación).
- Email al correo registrado del admin.

---

## 15. Tests de aceptación

Los tests por harvester individual están en sus secciones respectivas. Tests integrales del sistema de cosecha completo:

**Test E1 — Cosecha completa OpenAlex desde cero:** sistema vacío → ejecutar cosecha completa OpenAlex → verificar que se crearon ≥3,500 papers, ≥500 personas UAT, ≥10,000 coautorías.

**Test E2 — Re-cosecha incremental:** después de E1, esperar 1 día → ejecutar cosecha incremental → verificar que solo entran papers nuevos, que ningún paper viejo se duplica.

**Test E3 — Cosecha multi-fuente:** después de E1 → ejecutar cosechas de VuFind, RIUAT, SNII en orden → verificar que el cruce funciona: no hay duplicados, los registros locales que no están en OpenAlex se crearon nuevos, los SNII enriquecieron personas existentes.

**Test E4 — Recuperación de fallo:** simular caída de OpenAlex en medio de cosecha (mock 503) → verificar que el sistema reintenta con backoff, alerta al admin, y al tercer fallo registra error y continúa.

**Test E5 — Deduplicación cross-fuente:** poblar manualmente un paper con DOI X desde OpenAlex → ejecutar cosecha VuFind que tiene el mismo paper → verificar que NO se crea duplicado, que se consolida en el existente con `metadatos.fuentes_secundarias=['vufind_uat']`.

**Test E6 — Desambiguación con homónimos:** poblar dos personas distintas con el mismo `nombre_normalizado` (María García en distintas dependencias) → ejecutar cosecha que traiga papers atribuidos a "María García" sin ORCID → verificar que se marca para revisión humana en lugar de asignar a la persona equivocada.

---

## Cierre

Este documento define cómo IntellectClone trae datos del mundo. Cada harvester tiene responsabilidad atómica, contrato de salida claro, y tests verificables. La política de control humano (cosecha solo manual) está reflejada en la arquitectura: no hay cron, hay panel admin con botones explícitos.

Cuando Claude Code lo reciba:

1. Implementará primero `BaseHarvester` con su política de errores.
2. Implementará `OpenAlexHarvester` (la más rica y estable).
3. Implementará `VuFindUATHarvester` y `RIUATHarvester` en paralelo.
4. Dejará `SNIIUATHarvester` para el final por su complejidad ASP.NET.
5. ORCID y Crossref como enriquecedores se implementan en una fase de pulido.
6. Web harvesters (sitios personales) van como funcionalidad opcional, no bloqueante para v1.

Tiempo estimado de Fase C (cosechadores) en el plan operativo: 2-4 semanas para Claude Code.

---

*Fin del documento técnico 04. Versión 0.1 — pendiente de validación de Fernando.*
