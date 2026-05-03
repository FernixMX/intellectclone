# IntellectClone — Selección de modelos LLM y gestión de presupuesto

**Documento técnico 08 — Configuración de proveedores y control de costos**
**Versión 0.1**
**Audiencia:** Claude Code (constructor) + revisión humana de Fernando

---

## Por qué este documento existe

Los documentos previos mencionan tangencialmente la elección de LLM en varias secciones (perfilador en doc 05, costos en doc 05, endpoint de regeneración en doc 07), pero no consolidan en un solo lugar **cómo el admin elige y controla qué modelo se usa cuándo**. Este documento llena ese vacío.

Aplica a **toda llamada a LLM dentro de IntellectClone**, no solo al perfilador. Cuando llegue v1.5 con módulo de simulación interno, este mismo sistema de selección de modelos lo gobierna también.

---

## 1. Filosofía

### Tres principios

**Primero, default sólido + override fácil.** El admin no debería tener que elegir modelo en cada generación de gemelo. Por defecto se usa Claude Sonnet (decisión Fernando). Si en una generación específica quiere Opus para máxima calidad o Gemini Flash para máxima economía, lo selecciona puntualmente. La fricción está en lo excepcional, no en lo común.

**Segundo, transparencia de costos en tiempo real.** Antes de disparar cualquier operación que consuma LLM, el admin ve la estimación de costo en USD para los modelos disponibles. No hay sorpresas a fin de mes.

**Tercero, alertas con acción humana.** Cuando el presupuesto se acerque al límite, el sistema alerta al admin pero **NO toma decisiones automáticas** (decisión Fernando: "alerta y sigo manualmente"). El control de cuándo seguir, cuándo pausar, cuándo cambiar de modelo, queda en manos humanas.

---

## 2. Proveedores soportados en v1

| Proveedor | Modelo principal | Uso recomendado | Costo aprox por gemelo |
|---|---|---|---|
| **Anthropic Claude** | Claude Sonnet 4.6 | **Default del sistema** | $0.15 |
| Anthropic Claude | Claude Opus 4.7 | Gemelos VIP, máxima calidad | $0.80 |
| Anthropic Claude | Claude Haiku 4.5 | Pruebas, casos rápidos | $0.04 |
| Google Gemini | Gemini 2.5 Pro | Alternativa a Claude Sonnet | $0.08 |
| Google Gemini | Gemini 2.5 Flash | Generación masiva económica | $0.02 |
| OpenAI | GPT-5 (cuando disponible) | Comparación / respaldo | variable |

Los costos son estimaciones para corpus promedio (~50K caracteres). El costo real lo registra cada gemelo en `gemelo.costo_generacion_usd`.

### Default establecido: Claude Sonnet

El admin configura **un solo default global**. La decisión inicial (Fernando, sesión 3 de mayo de 2026): **Claude Sonnet 4.6**. Razones:

- Mejor relación calidad/costo para extracción estructurada psicométrica.
- Razonamiento HEXACO + Schwartz de calidad cercana a Opus.
- Costo razonable para generación masiva (~$105 USD para 700 gemelos completos).
- Disponibilidad robusta de la API Anthropic en 2026.

Este default es **modificable** desde el panel admin sin tocar código.

---

## 3. Capa de abstracción de LLMs

### Estructura del módulo

```
backend/intellectclone/llm/
├── __init__.py
├── base.py                # ClienteLLMBase (interfaz)
├── anthropic_client.py    # ClienteAnthropic
├── gemini_client.py       # ClienteGemini
├── openai_client.py       # ClienteOpenAI
├── factory.py             # selector de cliente según config
├── presupuesto.py         # tracking de consumo y alertas
├── modelos_disponibles.py # registro de modelos y precios
└── exceptions.py
```

### Interfaz común

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class RespuestaLLM:
    contenido: str
    modelo_usado: str
    proveedor: str
    tokens_prompt: int
    tokens_completion: int
    costo_usd: float
    duracion_ms: int
    metadatos: dict

class ClienteLLMBase(ABC):
    """Interfaz común para todos los proveedores de LLM."""

    @abstractmethod
    async def generar(
        self,
        modelo: str,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperatura: float = 0.2,
        formato_json: bool = False,
        timeout_segundos: int = 120,
    ) -> RespuestaLLM:
        """Genera contenido con el modelo especificado."""
        ...

    @abstractmethod
    def calcular_costo(self, modelo: str, tokens_prompt: int, tokens_completion: int) -> float:
        """Calcula costo USD según pricing del modelo."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Verifica que el proveedor está disponible."""
        ...
```

### Factory que selecciona cliente

```python
def obtener_cliente_llm(modelo_id: str) -> ClienteLLMBase:
    """
    modelo_id es el identificador canónico, ej:
      'anthropic:claude-sonnet-4-6'
      'anthropic:claude-opus-4-7'
      'google:gemini-2.5-pro'
      'google:gemini-2.5-flash'
      'openai:gpt-5'
    """
    proveedor, modelo = modelo_id.split(':', 1)
    if proveedor == 'anthropic':
        return ClienteAnthropic()
    elif proveedor == 'google':
        return ClienteGemini()
    elif proveedor == 'openai':
        return ClienteOpenAI()
    else:
        raise ValueError(f"Proveedor desconocido: {proveedor}")
```

### Configuración por variables de entorno

```env
# .env
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
OPENAI_API_KEY=sk-...

# Default global del sistema
LLM_MODELO_DEFAULT=anthropic:claude-sonnet-4-6

# Presupuesto mensual en USD
LLM_PRESUPUESTO_MENSUAL_USD=500
LLM_ALERTA_PORCENTAJE=80
```

---

## 4. Selección de modelo en cada operación

### Flujo conceptual

Toda operación que consume LLM (generación de gemelo, validación de consistencia, futura simulación en v1.5) sigue este flujo:

```
[Admin dispara operación]
    ↓
[Sistema lee modelo elegido]
    ├─ Si admin pasó modelo explícito → usa ese
    └─ Si no → usa LLM_MODELO_DEFAULT
    ↓
[Verifica presupuesto disponible]
    ├─ Si suficiente → procede
    └─ Si excede límite → bloquea operación, alerta admin
    ↓
[Estima costo y muestra al admin]
    ↓
[Admin confirma]
    ↓
[Ejecuta operación con modelo elegido]
    ↓
[Registra en `gemelo.modelo_perfilador` y costo real]
    ↓
[Actualiza tracking de presupuesto]
    ↓
[Si superó umbral de alerta → notifica admin]
```

### Tres puntos donde el admin elige modelo

**Punto 1: Default global.** Configuración en panel admin → "Configuración del sistema" → "Modelo LLM por defecto". Cambia `LLM_MODELO_DEFAULT`. Aplica a todas las operaciones que no especifiquen modelo.

**Punto 2: Override por persona/operación.** En cada flujo de generación de gemelo (botón "Generar gemelo de X"), aparece un selector de modelo. Pre-seleccionado el default. Admin puede cambiarlo solo para esa generación específica.

**Punto 3: Override por pase del perfilador.** El perfilador tiene 6 pases (HEXACO, Schwartz, idiolecto, posturas, síntesis, validación). Configuración avanzada permite asignar distintos modelos a distintos pases. Por ejemplo, "HEXACO con Opus, idiolecto con Flash". Útil para usuarios técnicamente avanzados.

---

## 5. Componente de UI: selector de modelo

### Diseño

Componente React reutilizable `<SelectorModeloLLM />` que aparece en:

- Modal de "Generar gemelo individual".
- Modal de "Regenerar masivamente".
- Modal de "Solicitar corrección de gemelo" con regeneración.
- Configuración avanzada del perfilador.

### Estructura visual (modo claro y oscuro)

```
┌────────────────────────────────────────────────────────────────┐
│ Modelo de IA para esta generación                             │
│                                                                │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ ● Claude Sonnet 4.6           Default · $0.15 por gemelo  │ │
│ │ ○ Claude Opus 4.7             Premium · $0.80 por gemelo  │ │
│ │ ○ Claude Haiku 4.5            Económico · $0.04 por gemelo│ │
│ │ ○ Gemini 2.5 Pro              Alterno · $0.08 por gemelo  │ │
│ │ ○ Gemini 2.5 Flash            Masivo · $0.02 por gemelo   │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                │
│ Gemelos a generar: 1                                          │
│ Costo estimado total: $0.15 USD                               │
│ Presupuesto del mes: $47.30 / $500 (9.5% usado)               │
│                                                                │
│ [Cancelar]              [Generar con modelo seleccionado]      │
└────────────────────────────────────────────────────────────────┘
```

Cada opción muestra:
- Radio button.
- Nombre del modelo.
- Etiqueta de carácter ("Default", "Premium", "Económico", etc.).
- Costo estimado por gemelo en USD.

Debajo del selector, en tiempo real:
- Cantidad de gemelos a generar.
- Costo total estimado para esa cantidad.
- Estado del presupuesto del mes (consumido vs límite).

### Lógica frontend

```typescript
// frontend/src/components/SelectorModeloLLM.tsx
interface ModeloLLM {
  id: string;
  nombre: string;
  proveedor: 'anthropic' | 'google' | 'openai';
  caracter: 'default' | 'premium' | 'economico' | 'alterno' | 'masivo';
  costo_por_gemelo_usd: number;
  disponible: boolean;
  razon_no_disponible?: string;
}

interface Props {
  cantidad_gemelos: number;
  modelo_seleccionado: string;
  onCambiar: (modelo_id: string) => void;
}

// Carga modelos disponibles desde GET /api/v1/llm/modelos-disponibles
// Carga estado de presupuesto desde GET /api/v1/stats/costos-llm
// Calcula costo total = costo_por_gemelo * cantidad_gemelos
```

---

## 6. Sistema de presupuesto

### Configuración

```sql
-- Tabla auxiliar en migración posterior al esquema inicial
CREATE TABLE configuracion_presupuesto (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    presupuesto_mensual_usd     NUMERIC(10,2) NOT NULL DEFAULT 500.00,
    umbral_alerta_porcentaje    SMALLINT NOT NULL DEFAULT 80,
    fallback_automatico_activo  BOOLEAN NOT NULL DEFAULT FALSE,
    fallback_modelo_id          VARCHAR(100),                      -- 'google:gemini-2.5-flash'
    bloqueo_al_limite           BOOLEAN NOT NULL DEFAULT TRUE,     -- bloquear cuando se alcance 100%
    actualizado_por             UUID REFERENCES usuario_sistema (id),
    actualizado_en              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Solo existe una fila activa de configuración. El admin la edita desde el panel.

### Tracking de consumo

Cada llamada a LLM se registra en una tabla auxiliar:

```sql
CREATE TABLE consumo_llm (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    modelo_id           VARCHAR(100) NOT NULL,                     -- 'anthropic:claude-sonnet-4-6'
    proveedor           VARCHAR(20) NOT NULL,
    proposito           VARCHAR(50) NOT NULL,                      -- 'perfilado_hexaco' | 'perfilado_schwartz' | etc.
    tokens_prompt       INTEGER NOT NULL,
    tokens_completion   INTEGER NOT NULL,
    costo_usd           NUMERIC(10,5) NOT NULL,
    duracion_ms         INTEGER,
    gemelo_id           UUID REFERENCES gemelo (id),
    persona_id          UUID REFERENCES persona (id),
    usuario_id          UUID REFERENCES usuario_sistema (id),
    error               BOOLEAN NOT NULL DEFAULT FALSE,
    error_mensaje       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_consumo_llm_fecha ON consumo_llm (created_at DESC);
CREATE INDEX idx_consumo_llm_proveedor ON consumo_llm (proveedor);
CREATE INDEX idx_consumo_llm_proposito ON consumo_llm (proposito);
CREATE INDEX idx_consumo_llm_persona ON consumo_llm (persona_id);
```

Esto permite generar reportes detallados: cuánto consumió cada persona, qué modelo se usó más, cuál pase del perfilador es más caro, etc.

### Cálculo del consumido del mes

```sql
SELECT COALESCE(SUM(costo_usd), 0) AS consumido_mes_usd
FROM consumo_llm
WHERE created_at >= date_trunc('month', NOW())
  AND error = FALSE;
```

### Política de alertas

Por decisión de Fernando, **solo alertas, sin fallback automático**. El sistema es estricto:

**80% del presupuesto consumido (configurable):**
- Notificación in-app al admin.
- Email al admin.
- Banner persistente en panel: "Has consumido el 80% del presupuesto LLM del mes ($400 / $500). Considera pausar generaciones o cambiar a un modelo más económico."

**95% del presupuesto:**
- Segunda alerta más urgente.
- Banner en rojo.
- Sigue permitiendo operaciones.

**100% del presupuesto (si `bloqueo_al_limite = TRUE`):**
- Las nuevas operaciones que consuman LLM se bloquean.
- Mensaje: "Presupuesto del mes agotado. Aumenta el límite o espera al próximo mes."
- Admin puede aumentar límite con un click si tiene autorización.

**100% del presupuesto (si `bloqueo_al_limite = FALSE`):**
- Sigue permitiendo operaciones, pero cada acción muestra advertencia clara.
- Útil si tienes presupuesto adicional pero quieres ser consciente del exceso.

### Notificaciones

Cuando se cruza un umbral, se dispara:

1. **In-app:** ícono de campana en navegación con badge.
2. **Email:** al correo del admin (template `presupuesto_alerta.html`).
3. **Auditoría:** registro en tabla `auditoria` con `accion='presupuesto_alerta_X_porcentaje'`.

---

## 7. Endpoints API para configuración

### `GET /api/v1/llm/modelos-disponibles`

Lista los modelos disponibles con su info y disponibilidad.

Response:
```json
{
  "modelos": [
    {
      "id": "anthropic:claude-sonnet-4-6",
      "nombre": "Claude Sonnet 4.6",
      "proveedor": "anthropic",
      "caracter": "default",
      "costo_por_gemelo_usd": 0.15,
      "disponible": true,
      "es_default_actual": true
    },
    {
      "id": "anthropic:claude-opus-4-7",
      "nombre": "Claude Opus 4.7",
      "proveedor": "anthropic",
      "caracter": "premium",
      "costo_por_gemelo_usd": 0.80,
      "disponible": true,
      "es_default_actual": false
    },
    {
      "id": "google:gemini-2.5-pro",
      "nombre": "Gemini 2.5 Pro",
      "proveedor": "google",
      "caracter": "alterno",
      "costo_por_gemelo_usd": 0.08,
      "disponible": true
    }
  ]
}
```

Si un modelo no está disponible (API key faltante, proveedor caído), se devuelve con `disponible: false` y `razon_no_disponible: "..."`.

### `GET /api/v1/llm/configuracion`

Devuelve la configuración actual del sistema. Solo admin.

Response:
```json
{
  "modelo_default": "anthropic:claude-sonnet-4-6",
  "presupuesto_mensual_usd": 500.00,
  "consumido_mes_usd": 47.30,
  "porcentaje_consumido": 9.5,
  "umbral_alerta_porcentaje": 80,
  "bloqueo_al_limite": true,
  "fallback_automatico_activo": false,
  "estado": "ok",
  "ultima_actualizacion": "2026-04-01T..."
}
```

### `PATCH /api/v1/llm/configuracion`

Actualizar configuración. Solo admin.

Request:
```json
{
  "modelo_default": "anthropic:claude-sonnet-4-6",
  "presupuesto_mensual_usd": 750.00,
  "umbral_alerta_porcentaje": 75
}
```

Response 200: nueva configuración aplicada.

### `GET /api/v1/llm/consumo`

Detalle de consumo. Solo admin/rectoria.

Query params:
- `periodo`: `hoy | ayer | este_mes | mes_anterior | rango_personalizado`
- `desde`, `hasta`: si periodo es personalizado
- `agrupar_por`: `modelo | proveedor | proposito | persona | dia`

Response:
```json
{
  "total_usd": 47.30,
  "total_tokens_prompt": 5250000,
  "total_tokens_completion": 1280000,
  "operaciones": 187,
  "agrupado_por": "modelo",
  "grupos": [
    {
      "clave": "anthropic:claude-sonnet-4-6",
      "operaciones": 165,
      "costo_usd": 39.20,
      "porcentaje": 82.9
    },
    {
      "clave": "anthropic:claude-opus-4-7",
      "operaciones": 12,
      "costo_usd": 7.10,
      "porcentaje": 15.0
    }
  ]
}
```

### `POST /api/v1/llm/test-modelo`

Prueba que un modelo funciona antes de usarlo. Útil cuando el admin quiere verificar API keys.

Request:
```json
{
  "modelo_id": "anthropic:claude-sonnet-4-6"
}
```

Response:
```json
{
  "disponible": true,
  "latencia_ms": 1240,
  "tokens_consumidos": 25,
  "costo_usd": 0.0001
}
```

---

## 8. Persistencia del modelo usado en cada gemelo

Esto ya está en el modelo de datos pero vale la pena hacerlo explícito.

Cada vez que se genera un gemelo, en la tabla `gemelo`:

| Campo | Ejemplo | Significado |
|---|---|---|
| `modelo_perfilador` | `anthropic:claude-sonnet-4-6` | qué modelo se usó |
| `prompt_perfilador_version` | `0.2` | qué versión de prompt |
| `tokens_consumidos` | 12500 | total prompt + completion |
| `costo_generacion_usd` | 0.1430 | costo real (no estimado) |
| `duracion_generacion_ms` | 8420 | duración total |

Esto permite:
- Comparar calidad de gemelos generados con distintos modelos.
- Auditar costo histórico exacto.
- Identificar si un modelo específico está produciendo gemelos de menor calidad.

Si en el futuro se descubre que un modelo específico produjo gemelos defectuosos, una sola query identifica todos los afectados:

```sql
SELECT persona_id, score_veracidad, costo_generacion_usd
FROM gemelo
WHERE modelo_perfilador = 'anthropic:claude-haiku-4-5'
  AND es_version_actual = TRUE
ORDER BY score_veracidad ASC;
```

---

## 9. Casos de uso típicos

Para que el sistema quede claro, te ilustro tres escenarios reales:

### Caso A: Generación masiva inicial

**Situación:** Acabas de cosechar 700 personas UAT, quieres generar gemelos para todas.

**Flujo:**

1. Vas al panel admin → "Generación masiva".
2. Filtras: "Investigadores SNII activos" → 587 personas.
3. Estimación automática: con default Claude Sonnet, costo total ~$88 USD.
4. Decides bajar a Gemini 2.5 Flash para esta operación. Costo nuevo estimado: ~$12 USD.
5. Confirmas. Sistema procesa en background, te notifica al terminar.
6. Después validas en lote piloto los primeros 15-20 generados.

### Caso B: Generación VIP

**Situación:** El gemelo de la Rectora necesita ser de máxima calidad.

**Flujo:**

1. Vas al perfil de la Rectora → "Regenerar gemelo".
2. Override de modelo: cambias de Claude Sonnet (default) a Claude Opus.
3. Costo estimado: $0.80 (vs $0.15 con default).
4. Confirmas. Generación procesa.
5. Validas el gemelo manualmente con cuidado.

### Caso C: Alerta de presupuesto

**Situación:** Es 25 del mes y has consumido $400 de los $500 disponibles.

**Flujo:**

1. Sistema detecta cruce del 80%.
2. Recibes notificación in-app y email.
3. Banner en el panel: "Has consumido el 80% del presupuesto LLM del mes."
4. Decides:
   - Pausar generaciones hasta el siguiente mes.
   - O continuar con modelos más económicos (Haiku, Flash).
   - O aumentar el presupuesto si tienes autorización.
5. Sistema sigue funcionando hasta llegar al 100% (o al límite que configures).

---

## 10. Mensaje a Claude Code

Cuando construyas el sistema:

1. La capa `llm/` es central, **constrúyela primero**, antes que el perfilador.
2. El selector `<SelectorModeloLLM />` es un componente reutilizable, no específico al perfilador.
3. La tabla `consumo_llm` se llena desde la capa `llm/`, no desde cada caller.
4. Las alertas de presupuesto se disparan en hooks post-llamada, no en cada caller.
5. El default se lee de configuración de DB primero, fallback a variable de entorno `LLM_MODELO_DEFAULT`.
6. Las API keys de proveedores **nunca** se exponen en respuestas API. Solo en variables de entorno.
7. El test de modelo (`POST /llm/test-modelo`) consume tokens reales (mínimo posible, ~25 tokens). Cuenta en el presupuesto.

Tiempo estimado de implementación de la capa `llm/` completa: 3-5 días para Claude Code.

---

## Cierre

Este documento cierra formalmente el paquete técnico v1 de IntellectClone. Cubre lo que faltaba: cómo el admin elige y controla qué modelo de LLM se usa en cada operación, con qué presupuesto, con qué alertas.

El paquete completo ahora son **13 documentos + SQL validado**, listo para handoff a Claude Code.

---

*Fin del documento técnico 08. Versión 0.1 — pendiente de validación de Fernando.*
*Fin formal del paquete v1 de IntellectClone.*
