# Prompt para Claude Design — IntellectClone Design System

> **Cómo usar este documento:** copia todo el contenido desde la siguiente línea hasta el final y pégalo como contexto inicial en Claude Design. Este es un prompt largo a propósito: contiene todas las decisiones tomadas para que Claude Design no improvise.

---

# Construcción del Design System para IntellectClone

Necesito que construyas un **Design System completo** y, sobre él, **nueve pantallas en alta fidelidad** para una plataforma institucional llamada IntellectClone. Antes de empezar, lee con cuidado todo el contexto: las decisiones de identidad, paleta, tipografía y comportamiento ya están tomadas. Tu trabajo es interpretarlas con criterio y materializarlas en un sistema visual coherente, sofisticado y producible. No improvises identidad ni paleta: ejecuta lo que está aquí.

## 1. Qué es IntellectClone

IntellectClone es una plataforma de gemelos digitales de la comunidad académica de la Universidad Autónoma de Tamaulipas (UAT). El sistema cosecha la producción intelectual pública de los investigadores UAT (papers, áreas de investigación, redes de coautoría, dependencia institucional, trayectoria) y construye, para cada persona, una réplica digital — un agente con personalidad, intereses, sesgos cognitivos y forma de razonar reconstruidos a partir de su huella académica.

Sobre esos gemelos, la plataforma ofrece un módulo de simulación tipo Mirrorfish: un usuario autorizado (Rectoría, oficina de asesores, secretarías académicas) puede formular un escenario o pregunta, seleccionar un subconjunto de la comunidad UAT (por área, dependencia, nivel SNII, cuerpo académico), y obtener cómo reaccionarían esos gemelos al escenario, agregado y desagregado.

El producto tiene tres caras públicas: un **directorio** consultable de la producción intelectual UAT, un **explorador** visual de la red de colaboración interna, y un **simulador** privado para autoridades. La versión 1 cubre solo investigadores con datos públicos (~500-700 personas). El sistema vive en infraestructura UAT propia (VPS Linux IONOS) y será presentado a Rectoría como herramienta de prospectiva institucional alineada al PDI 2024-2028 "La UAT se Transforma".

Es un producto serio, institucional, dirigido a personas que toman decisiones. Pero también es un producto que vive en internet y será visto por la comunidad académica completa: investigadores revisando su perfil, externos consultando colaboradores potenciales, prensa especializada, organismos de evaluación. La identidad visual debe sostener ambos contextos sin fricción.

## 2. Personalidad visual: "Quirúrgico"

La identidad elegida se llama internamente **"Quirúrgico"**. Es un nombre interno descriptivo, no se muestra al usuario. Define el carácter de todo el sistema visual.

Quirúrgico significa: **instrumento de precisión**. Como un microscopio o una herramienta médica de alta gama. La interfaz no decora ni grita; desaparece para que los datos hablen. Cada elemento existe por una razón funcional. La sofisticación viene de la reducción radical, no de la ornamentación. Inspiración directa: Linear, Vercel, Anthropic, Stripe Dashboard. Inspiración aspiracional: Bloomberg Terminal pero con respeto por el usuario, no agresivo.

Lo que NO es Quirúrgico: aburrido, plano, frío, gubernamental, tipo Bootstrap. La frialdad se rompe con calidez tipográfica, microinteracciones cuidadas, y un único color de acento que aparece en momentos exactos. La gente al ver el producto debe pensar: "esto es nivel internacional", "esto le da prestigio a la UAT", "alguien sabe lo que hace".

## 3. Paleta de colores

Paleta deliberadamente restringida. Una sola familia neutra extendida + un único acento.

### Modo claro (primario)

```
Fondos
- bg-base:       #FAFAF9   página principal, marfil casi blanco
- bg-surface:    #FFFFFF   cards y superficies elevadas
- bg-subtle:     #F4F3EE   zonas de agrupación, hover sutil
- bg-muted:      #ECEAE3   estados hover y deshabilitados de surface

Bordes
- border-subtle:  #E8E6DF  divisores discretos
- border-default: #D4D2C9  bordes normales de inputs y cards
- border-strong:  #B4B2A9  bordes en focus o estados activos

Texto
- text-primary:    #0A0A0A  títulos, texto importante
- text-secondary:  #2C2C2A  cuerpo de texto principal
- text-tertiary:   #6B6B68  labels, metadatos, texto auxiliar
- text-quaternary: #A8A6A0  placeholders, hints, texto deshabilitado

Acento (cobalto)
- accent-primary: #1E3A8A  color de acción principal, links, énfasis
- accent-hover:   #1A3175  hover sobre accent-primary
- accent-subtle:  #E8EDF7  fondos sutiles informativos
- accent-text:    #1E3A8A  texto sobre accent-subtle

Semánticos (uso restringido)
- success:        #0F6E56  verde profundo, solo confirmaciones
- success-subtle: #E1F5EE
- warning:        #854F0B  ámbar profundo, solo advertencias
- warning-subtle: #FAEEDA
- danger:         #A32D2D  rojo profundo, solo errores y destructivos
- danger-subtle:  #FCEBEB
```

### Modo oscuro

```
Fondos
- bg-base:       #0A0A0A   negro casi puro, ahorra OLED
- bg-surface:    #141413   superficies elevadas
- bg-subtle:     #1C1C1A   zonas de agrupación
- bg-muted:      #252522   estados hover

Bordes
- border-subtle:  #2A2A28  divisores
- border-default: #3A3A37  bordes normales
- border-strong:  #525250  bordes en focus

Texto
- text-primary:    #FAFAF9
- text-secondary:  #D4D2C9
- text-tertiary:   #888780
- text-quaternary: #5F5E5A

Acento (cobalto)
- accent-primary: #6B8FE0   más claro en oscuro para contraste
- accent-hover:   #8AA8E8
- accent-subtle:  #1A2540   fondos sutiles
- accent-text:    #B5C7EE

Semánticos
- success:        #5DCAA5
- success-subtle: #08503D
- warning:        #EF9F27
- warning-subtle: #4A2A06
- danger:         #F09595
- danger-subtle:  #4A1818
```

### Reglas de uso del color

El cobalto no es decoración. Aparece **solo** en: el botón principal de cada pantalla (uno por pantalla, máximo dos), enlaces, el ícono o indicador del estado del gemelo digital, líneas de énfasis a la izquierda de elementos destacados, focus rings de inputs, y la representación visual del usuario activo (avatar, badge "tú"). En todo lo demás, neutros.

Los semánticos (success, warning, danger) son aún más restringidos: solo en feedback directo del sistema. Una confirmación verde tras guardar. Una advertencia ámbar antes de una simulación cara. Un error rojo cuando algo falla. Nunca decorativos, nunca categóricos, nunca para distinguir tipos de papers o áreas.

## 4. Tipografía

### Decisión de tipografía

**Tipografía protagonista en producción:** Geist (Vercel, gratis, open source).
**Tipografía protagonista en mockups y presentaciones:** Visby (Connary Fagen, comercial).
**Tipografía monoespaciada (datos numéricos):** Geist Mono o JetBrains Mono.

Razón: Visby es la tipografía aspiracional pero su licencia comercial complica el despliegue institucional UAT. Geist es visualmente muy cercana a Visby, gratuita, optimizada para pantalla, y soporta perfectamente el carácter quirúrgico que buscamos. Para los mockups en Claude Design **usa Visby si está disponible en tu sistema**; si no, usa Geist; si tampoco, Manrope. Para todos los componentes del design system, especifica la familia con cascada `"Visby Round CF", "Geist", "Manrope", -apple-system, BlinkMacSystemFont, sans-serif`.

### Escala tipográfica

```
Display:   48px / 600 / -0.025em / 1.05    (titulares de portada, hero)
H1:        32px / 600 / -0.02em  / 1.15    (encabezado de página)
H2:        24px / 600 / -0.015em / 1.2     (secciones mayores)
H3:        18px / 600 / -0.01em  / 1.3     (secciones menores)
H4:        16px / 600 / -0.005em / 1.4     (subsecciones)
Body L:    16px / 400 / 0        / 1.55    (cuerpo de lectura, prosa)
Body:      14px / 400 / 0        / 1.5     (texto general de UI)
Body S:    13px / 400 / 0        / 1.45    (metadatos, descripciones)
Caption:   12px / 500 / 0.02em   / 1.4     (labels, badges)
Eyebrow:   11px / 500 / 0.12em / uppercase (etiquetas de sección)
Mono L:    14px / 500 / 0        / 1.4     (números destacados)
Mono:      13px / 400 / 0        / 1.4     (IDs, métricas inline)
```

Pesos disponibles: 400 regular, 500 medium, 600 semibold. **No usar 700 ni superior**, se ven pesados contra los neutros cálidos. El peso 600 es el "negrita" del sistema.

### Reglas tipográficas

- Sentence case en todo. Nunca Title Case ni MAYÚSCULAS, salvo eyebrows que sí van en uppercase con tracking.
- Números siempre en mono (Geist Mono o JetBrains Mono), incluso si son una sola cifra, cuando representan datos: contadores, métricas, fechas, IDs, citas, índice h, tiempos. Los números en prosa narrativa van en sans normal.
- Comillas tipográficas correctas: « » o " " según contexto, nunca rectas " ".
- Separador decimal por punto, separador de miles por coma (convención científica: "1,284 citas").
- Sin guiones de separación rotos, sin justificación forzada. Texto siempre alineado a la izquierda, ragged right.

## 5. Espaciado y layout

Sistema basado en múltiplos de 4px. Escalas: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96.

### Densidad

La densidad varía por zona del producto:

- **Zonas operativas** (simulador, admin, listados de simulaciones, panel de cosechas, tablas de datos): densidad alta. Padding interno de cards 16px, gap entre cards 12px, fila de tabla 36-40px de altura. Inspiración: Linear, Bloomberg.
- **Zonas de lectura y contemplación** (perfil de investigador, página acerca, vista pública del directorio): densidad media-baja. Padding interno de cards 24-32px, gap entre secciones 32-48px, line-height generoso. Inspiración: Stripe, perfiles de Substack.
- **Zonas de descubrimiento** (home, explorador, landing): densidad baja. Mucho aire, jerarquía clara, una cosa importante por scroll. Inspiración: Anthropic, Vercel home.

### Radios

```
- radius-none:  0px      (botones agresivamente cuadrados, contenedores fullbleed)
- radius-sm:    4px      (inputs, selects, badges, pills)
- radius-md:    6px      (botones, cards pequeños)
- radius-lg:    8px      (cards principales, modales)
- radius-xl:    12px     (contenedores grandes, tarjetas hero)
- radius-full:  9999px   (avatares, dots indicadores)
```

Filosofía: radios pequeños. Quirúrgico no es redondeado; es preciso. Ningún elemento usa radio mayor a 12px excepto avatares.

### Sombras

Mínimas. Plano por default. Sombras solo para indicar elevación funcional (modales, dropdowns, popovers).

```
- shadow-none:  ninguna sombra (default)
- shadow-sm:    0 1px 2px rgba(10, 10, 10, 0.04)        para hover sutil
- shadow-md:    0 4px 12px rgba(10, 10, 10, 0.06)       para dropdowns
- shadow-lg:    0 12px 32px rgba(10, 10, 10, 0.08)      para modales
- shadow-focus: 0 0 0 3px rgba(30, 58, 138, 0.15)       para focus rings (cobalto)
```

En modo oscuro, las sombras se sustituyen por bordes ligeramente más claros.

### Bordes

Todos los bordes son `0.5px` en pantalla retina, `1px` en pantalla normal. La diferencia visual es enorme: 0.5px se siente premium, 1px se siente Bootstrap. Implementar con `border: 1px solid var(--border-default)` y un override `@media (-webkit-min-device-pixel-ratio: 2)` que pone `0.5px` para retina.

## 6. Iconografía

Sistema único: **Lucide Icons** (https://lucide.dev). Línea fina, stroke 1.5px, geometría limpia. No mezclar con otra librería de íconos en ninguna circunstancia.

Tamaños:
```
- icon-xs:   14px   (inline en texto pequeño)
- icon-sm:   16px   (default en botones e inputs)
- icon-md:   20px   (default en navegación)
- icon-lg:   24px   (acciones destacadas)
- icon-xl:   32px   (estados vacíos, ilustraciones)
```

Color: heredan el `currentColor` del contenedor. Sin colores hardcoded en los íconos. Stroke siempre 1.5px en sm/md/lg, 1.25px en xs, 2px en xl.

## 7. Componentes a construir en el design system

Necesito que generes los siguientes componentes con todas sus variantes, en modo claro y modo oscuro:

### Botones

- **Primary**: fondo cobalto, texto blanco, radio 6px, padding 10x16px (default) o 12x20px (large). Hover: oscurece 10%. Active: scale(0.98). Solo uno por pantalla.
- **Secondary**: fondo transparente, borde 0.5px border-default, texto text-primary. Hover: bg-subtle.
- **Ghost**: sin borde, texto text-secondary. Hover: bg-subtle, texto text-primary.
- **Destructive**: fondo danger, texto blanco. Solo para confirmar destrucciones.
- **Tamaños**: sm (32px alto), md (38px alto, default), lg (44px alto).
- **Estados**: default, hover, active, focused (con focus ring cobalto), disabled, loading (con spinner).

### Inputs

- **Text input**: 38px alto, padding 8x12px, borde 0.5px border-default, radio 6px. Focus: borde cobalto + focus ring. Placeholder en text-quaternary. Label arriba del input en eyebrow style.
- **Textarea**: igual pero alto variable, mínimo 80px.
- **Select**: chevron Lucide a la derecha, mismo estilo que text input.
- **Search**: ícono Lucide search a la izquierda, padding-left ajustado, soporta clear button cuando hay texto.
- **Estados**: default, hover, focused, error (borde danger + texto helper en danger), disabled.

### Tags y pills

- **Tag**: rectangular, radio 4px, padding 4x10px, font caption (12px), borde 0.5px. Variantes: neutral (border-default), info (cobalto subtle), success, warning, danger.
- **Pill**: full radius, mismo padding y tipografía. Útil para categorías y filtros.
- **Tag con dot**: pequeño círculo de color a la izquierda del texto, indicador de estado.

### Avatares

- **Tamaños**: xs (24px), sm (32px), md (40px, default), lg (56px), xl (80px).
- **Variantes**: con foto (cuando exista, raro en v1), con iniciales sobre fondo derivado del nombre. Las iniciales en peso 500, color text-primary, fondo en una variante muy sutil del color asociado al nombre. **Sin colores aleatorios**: el fondo de iniciales siempre es bg-subtle con texto text-secondary, salvo el avatar del usuario activo que va con accent-subtle y accent-text.
- **Forma**: circular siempre.

### Cards

- **Surface card**: fondo bg-surface, borde 0.5px border-subtle, radio 8px, padding variable según densidad.
- **Subtle card**: fondo bg-subtle, sin borde, radio 8px. Para agrupaciones secundarias.
- **Highlighted card**: surface card + borde 0.5px accent-primary, indica selección o relevancia. Solo uno destacado a la vez en un grupo.
- **Stat card**: card específico para mostrar métricas. Eyebrow arriba, número en mono grande (Mono L o display), opcional delta o sparkline debajo.

### Navegación

- **Top bar**: 56px alto, fondo bg-base, borde inferior 0.5px border-subtle. Logo IntellectClone a la izquierda, navegación principal al centro o izquierda, controles de usuario y modo a la derecha.
- **Side nav** (para zonas privadas como simulador y admin): 240px ancho, fondo bg-subtle, items con padding 8x12px, ícono Lucide + texto. Item activo con bg-surface y borde izquierdo 2px cobalto.
- **Breadcrumbs**: tipografía body S, separador chevron-right Lucide en text-quaternary.
- **Tabs**: línea inferior 2px transparente que se vuelve cobalto en activo. Sin pills ni boxes, minimalismo absoluto.

### Tablas

- **Cabecera**: bg-subtle, font caption, padding 10x12px, peso 500.
- **Filas**: alto 40px (operativas) o 56px (lectura), borde inferior 0.5px border-subtle, hover bg-subtle.
- **Celdas numéricas**: alineación derecha, mono.
- **Acciones por fila**: aparecen en hover, alineadas a la derecha.

### Modales

- **Overlay**: rgba(10, 10, 10, 0.6) con blur sutil opcional.
- **Container**: bg-surface, borde 0.5px border-default, radio 12px, padding 32px, ancho máximo 560px (default).
- **Header**: título H3, botón cerrar Lucide x a la derecha.
- **Footer**: alineación derecha, botones espaciados 8px, primary a la derecha.

### Estados especiales

- **Empty state**: ícono Lucide xl en text-quaternary, título H4, descripción Body S en text-tertiary, opcional botón secondary para acción.
- **Loading**: skeleton screens con bg-muted animado, no spinners genéricos. Los spinners solo en botones durante una acción.
- **Error**: ícono triangular alert en danger, título, descripción, opcional botón retry.

### Microcomponentes

- **Toggle de modo claro/oscuro**: dos íconos Lucide sun/moon, item activo con fondo bg-surface y sombra sutil, item inactivo en text-quaternary.
- **Indicador de estado del gemelo**: dot 6px con texto pequeño. Estados: "Generado" (cobalto), "Validado" (success), "Pendiente" (text-quaternary), "Desactualizado" (warning).
- **Costo estimado de simulación**: pill especial con ícono Lucide zap a la izquierda, número en mono, tooltip al hover.

## 8. Pantallas a generar (en alta fidelidad)

Después del design system, genera estas nueve pantallas. Cada una debe ser una pantalla completa, tamaño desktop 1440x900, modo claro como default, con su versión en oscuro.

### Públicas (sin autenticación)

1. **Home / Landing de IntellectClone**
   - Hero con titular Display + subtítulo Body L explicando qué es la plataforma.
   - Tres bloques principales: explorar el directorio, ver red de colaboración, conocer el simulador (este último con badge "Solo personal autorizado").
   - Métricas globales del sistema: número de investigadores, número de papers, número de cuerpos académicos, áreas cubiertas. En stat cards horizontales.
   - Sección "respaldado por": Rectoría UAT, Oficina de Asesores, alineado al PDI 2024-2028.
   - Footer con links a privacidad, baja del sistema, contacto.

2. **Directorio de personas**
   - Sidebar izquierdo de filtros: área de conocimiento (chips), dependencia (select), cuerpo académico (select), nivel SNII (chips).
   - Header con búsqueda prominent + total de resultados + ordenamiento (relevancia, alfabético, productividad).
   - Listado en grid de cards medianos: avatar de iniciales, nombre, dependencia, áreas (3 tags max), métricas mini (papers, citas).
   - Paginación abajo, 24 por página.

3. **Perfil individual del investigador** (Dra. María Elena Cárdenas Ruiz como ejemplo)
   - Header con eyebrow "Investigador / Facultad de Ingeniería", nombre H1, dependencia y cuerpo académico, pill de SNII a la derecha.
   - Stat cards en grid de 4: publicaciones, citas, índice h, coautores UAT.
   - Sección áreas de expertise: tags.
   - Sección publicaciones: lista con título, journal, año, citas. Default 5 visibles + "ver todas".
   - Sección red de colaboración: visualización mini de los 10 coautores principales, con link a "explorar red completa".
   - Card del gemelo digital: estado, última actualización, resumen, botón "ver perfil cognitivo del gemelo" (modal con la estructura del agente).
   - Footer con CTA "Incluir en simulación" (solo si el usuario tiene permisos), "Solicitar corrección de datos", "Solicitar baja del sistema".

4. **Explorador de red de colaboración**
   - Visualización principal: grafo force-directed ocupando el 70% del viewport. Nodos = personas (avatar de iniciales miniatura), aristas = coautorías. Tamaño del nodo proporcional a número de papers, grosor de arista proporcional a número de coautorías.
   - Panel derecho: filtros (por dependencia, área, cuerpo académico), leyenda, persona seleccionada (info breve + link al perfil completo).
   - Controles superiores: zoom, reset, exportar imagen.

5. **Acerca del proyecto**
   - Layout editorial de columna única, ancho lectura cómodo (640px).
   - Texto explicativo, secciones con H2 y H3, citas tipográficas, links destacados.
   - Sección final: política de privacidad, cómo solicitar baja, contacto del equipo.

### Privadas (con autenticación)

6. **Pantalla del simulador (composición de escenario)**
   - Layout dos columnas. Izquierda 60%: editor del escenario (textarea grande con Body L), opciones avanzadas (tono de respuesta esperada, idioma, formato de salida). Derecha 40%: selector de cohorte (filtros encadenados, contador en tiempo real "187 gemelos seleccionados"), costo estimado, tiempo estimado.
   - CTA principal abajo: "Lanzar simulación" en primary, requiere confirmación si costo excede umbral.

7. **Resultado de simulación**
   - Header con resumen del escenario, cohorte seleccionada, fecha y hora, costo real, duración real.
   - Tabs: Síntesis ejecutiva | Agrupado por postura | Respuestas individuales.
   - Tab Síntesis: distribución de posturas en stat cards (% a favor, % en contra, % matizado), argumentos más repetidos, áreas con mayor disenso, citas representativas.
   - Tab Agrupado: las posturas con respuestas representativas y nombres de gemelos.
   - Tab Individual: tabla con nombre del gemelo, postura asignada, intensidad, snippet de respuesta, link a respuesta completa.
   - Acciones globales: exportar reporte PDF, compartir con otro usuario autorizado.

8. **Histórico de simulaciones**
   - Tabla densa con columnas: fecha, autor, cohorte (resumida), pregunta (truncada con tooltip), número de gemelos, costo, duración, estado.
   - Filtros laterales: por autor, por fecha, por estado, por cohorte.
   - Acciones por fila: ver resultado, duplicar, exportar.

9. **Panel admin (gestión de usuarios y cosechas)**
   - Top tabs: Usuarios | Cosechas | Gemelos | Configuración.
   - Tab Cosechas: estado de cada harvester (OpenAlex, VuFind UAT, RIUAT, SNII UAT) con última corrida, próxima corrida, registros traídos, errores. Botones para forzar cosecha manual.
   - Tab Gemelos: total generados, pendientes de validación, en error. Acciones masivas.
   - Densidad alta, pensado para uso intensivo por administrador técnico.

## 9. Cómo entregar

Genera primero el **design system completo** como un archivo de referencia: paleta, tipografía, espaciado, componentes con todas sus variantes. Después genera las **nueve pantallas** referenciando ese sistema.

Para cada pantalla, ofrece la versión en modo claro y en modo oscuro. La calidad esperada es de portafolio profesional: si la pantalla apareciera en Mobbin, debería verse competitiva con productos como Stripe Dashboard, Linear, Vercel, Anthropic Console. Detalles que importan: alineación pixel-perfect, jerarquía tipográfica clara, uso restringido del color, microinteracciones implícitas, tratamiento cuidado de números y datos.

Si en algún momento detectas una contradicción entre lo que pide este documento y lo que tu criterio de diseño te indica, **resuelve la contradicción consultándome** antes de improvisar. Lo más valioso que puedes hacer es señalar dudas, no taparlas.

## 10. Lo que NO quiero

- Gradientes de cualquier tipo (lineales, radiales, mesh).
- Glassmorphism, blur decorativo, neumorphism, skeumorphism.
- Sombras pronunciadas o coloreadas.
- Múltiples colores de acento (solo cobalto).
- Íconos sólidos o filled (solo Lucide línea fina).
- Mayúsculas innecesarias (solo en eyebrows).
- Tipografía decorativa en titulares.
- Ilustraciones genéricas tipo Storyset o Undraw.
- Fotos de stock de manos sobre teclados, profesores genéricos, edificios universitarios al atardecer.
- Cualquier referencia visual al logo de la UAT, escudo, totem o color institucional original. IntellectClone tiene identidad propia.

---

Cuando termines el design system, antes de pasar a las pantallas, muéstrame primero los componentes para validación. Si encuentras decisiones que necesitan mi input antes de avanzar (por ejemplo, una variante adicional que tenga sentido), pregúntame. Es mejor pausar que duplicar trabajo.
