# IntellectClone — Changelog del alcance v1

**Fecha:** 3 de mayo de 2026
**Razón:** decisión de Fernando de mantener Mirrorfish como sistema separado.

---

## Qué cambia en el proyecto

IntellectClone v1 originalmente incluía un módulo de simulación tipo Mirrorfish. Por decisión informada de Fernando, esa pieza queda fuera del alcance: él ya tiene un Mirrorfish funcionando que se conectará a IntellectClone vía la API de exportación documentada en `06_contrato_exportacion_mirrorfish.md`.

Esta decisión simplifica IntellectClone v1, reduce alcance, y mejora arquitectura por separación de responsabilidades.

---

## Documentos afectados y cómo se actualizan

### `01_documento_conceptual.md`

**Sección 7 (Arquitectura conceptual):** la "Capa de simulación (Mirrorfish UAT)" queda marcada como **fuera de alcance v1**. En su lugar, hay una "Capa de exportación" que provee gemelos a Mirrorfish por API REST. Las cinco capas se reducen a cuatro: cosecha, almacenamiento, gemelos, presentación. La exportación es un servicio dentro de la capa de presentación.

**Sección 4 (Alcance v1):** "Funcionalidades v1" se ajusta — se elimina "simulador básico" y se agrega "API de exportación de gemelos validados a sistemas externos (Mirrorfish)".

**Sección 5 (Visión de evolución):** las versiones v2-v5 mencionaban evoluciones del simulador interno. Esas se quedan como posibilidad opcional pero NO son la dirección principal: el simulador externo Mirrorfish absorbe esa función.

### `02_especificacion_operativa.md`

**Plan de fases:** la "Fase E — Simulador" se elimina completamente. Las fases siguientes se renumeran:
- Fase E (antes F): UI v1 (sin pantallas de simulación, sí con pantallas de gestión de tokens de exportación).
- Fase F (antes G): Despliegue.
- Fase G (antes H): Refinamiento y demo institucional.

Total estimado para v1 baja de 12 a aproximadamente 9-10 semanas.

**Sección "Documentos por crear en Fase 2":** el `06_simulador_mirrorfish.md` se reemplaza por `06_contrato_exportacion_mirrorfish.md` (este documento ya creado).

**Criterios de cierre de v1:** se elimina el criterio "Capacidad de ejecutar simulación con cohorte de 100+ gemelos en menos de 5 minutos" y se reemplaza por "API de exportación funcionando, con al menos un cliente externo (Mirrorfish) consumiendo gemelos validados exitosamente."

### `03_modelo_de_datos.md` y los archivos SQL

Las tablas `simulacion` y `respuesta_simulacion` se mantienen en el modelo de datos pero **no se usan en v1**. Razones para mantenerlas:
- Quitarlas requiere migración cuando se quieran agregar después.
- Ocupan cero espacio cuando están vacías.
- En el futuro, si IntellectClone quiere ofrecer un simulador interno opcional para casos donde Mirrorfish no esté disponible, las tablas ya están listas.

Se agrega una nueva tabla simple `export_token` para gestionar tokens de Mirrorfish:

```sql
CREATE TABLE export_token (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre          VARCHAR(100) NOT NULL,
    token_hash      VARCHAR(255) NOT NULL UNIQUE,
    permisos        TEXT[] NOT NULL DEFAULT ARRAY['read:gemelos'],
    creado_por      UUID REFERENCES usuario_sistema (id) ON DELETE SET NULL,
    expira_en       TIMESTAMPTZ,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_uso      TIMESTAMPTZ,
    total_requests  BIGINT NOT NULL DEFAULT 0,
    metadatos       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Esta tabla se agregará en una migración posterior. No hay urgencia de incluirla en el SQL inicial.

### `05_perfilador_y_gemelo.md`

Sin cambios sustantivos. El perfilador sigue produciendo gemelos exactamente igual. Lo único que cambia es que después de la generación, el destino del gemelo es la base de datos local + (después de validación humana) la API de exportación, en lugar de un simulador interno.

### `IntellectClone_Prompt_Claude_Design.md`

**Pantallas a generar:** las pantallas privadas relacionadas con simulación cambian:

- Se elimina "Pantalla del simulador (composición de escenario)".
- Se elimina "Resultado de simulación".
- Se elimina "Histórico de simulaciones".
- Se agrega "Panel de tokens de exportación" (gestión de tokens, ver uso).
- Se agrega "Panel de validación de gemelos" (pendientes, validados, en revisión).

El total de pantallas pasa de 9 a 8 (uno menos en privadas, uno más en privadas, neto cero, pero la naturaleza de la sección privada cambia).

---

## Documentos pendientes ajustados

Antes de la decisión, faltaban cuatro documentos técnicos para handoff a Claude Code:

1. `04_especificaciones_harvesters.md`
2. `05_perfilador_y_gemelo.md` ✅ (ya generado)
3. `06_simulador_mirrorfish.md`
4. `07_api_interna.md`

Después de la decisión, los pendientes son:

1. `04_especificaciones_harvesters.md` — pendiente.
2. ~~`06_simulador_mirrorfish.md`~~ — reemplazado por `06_contrato_exportacion_mirrorfish.md` ✅ (ya generado).
3. `07_api_interna.md` — pendiente, ahora más simple porque no incluye endpoints de simulación.

Total estimado de sesiones restantes con Claude.ai: 1-2 sesiones más para documentos 04 y 07.

---

## Mensaje a Claude Code (cuando reciba el paquete)

Si estás leyendo esto como parte del paquete de handoff, ten en cuenta:

- IntellectClone v1 **no** tiene módulo de simulación interno.
- La forma de "usar" gemelos es exportarlos a Mirrorfish vía API REST.
- Las tablas `simulacion` y `respuesta_simulacion` existen en el esquema pero quedan inactivas en v1; **no implementes lógica de simulación contra ellas**.
- El esfuerzo de UI se concentra en directorio, perfiles, validación y gestión de tokens, no en simulador.
- La capa de exportación es funcionalidad crítica de v1; trátala con el rigor de cualquier API pública (auth, rate limits, observabilidad, tests).

---

*Fin del changelog. Aplicar en próximas iteraciones de los documentos afectados.*
