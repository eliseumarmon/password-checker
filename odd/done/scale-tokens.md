# Tipografía y radios en variables CSS

Objetivo: sustituir los tamaños de letra, la familia tipográfica, los pesos, las alturas de línea y los radios escritos directamente en `frontend/src/style.css` por variables CSS en `:root`, sin ningún cambio visual. Es la base para probar la nueva dirección visual tocando pocas líneas.
Rama: `refactor/scale-tokens` desde `main` (`4ef1105`). Continúa `css-tokens` (Fase 1), que solo cubrió los colores. Fase 2, n.º 2: va antes de la dirección visual y de rehacer la Auditoría (L3). Entrega: `ask-on-risk`.
Comprobaciones: `npm run build` y `npm run e2e` en `frontend/`, más la comparación de estilos calculados de S2. Estado: hecho (L8); verificación independiente superada.

## Specs

- **S1 — Origen.** Del usuario, tras descartar `audit-layout`: «Sin duda no hay jerarquía, pero eso no es un problema de auditoría únicamente, veo que es un problema general de toda la aplicación. Es todo muy monótono. Menos mal que usamos css-token para poder experimentar sin tocar mucho.» Y: «hacemos un css-tokens de nuevo?»
- **S2 — Variables.** Cada `font-size`, `font-family`, `font-weight`, `line-height` y `border-radius` literal de `style.css` pasa a `var(--…)`, con la variable definida en `:root`.
  - Nombres por función, no por valor, como en `css-tokens`: `--type-…` para tamaños de texto, `--icon-…` para los iconos de texto que se dimensionan con `font-size`, `--weight-…`, `--leading-…`, `--font-…` y `--radius-…`.
  - Hoy: 34 `font-size` de 13 valores, 17 `border-radius` de 8 valores, 9 `font-weight`, 4 `line-height` y 1 `font-family`.
  - Aceptación: fuera de `:root` no queda ningún literal de esas propiedades, comprobable con `grep`. Se permiten `0`, `inherit` y `font:inherit`.
- **S3 — Espaciado: fuera, a la dirección visual (L6).** Al ver que conservar los valores exactos exigía 133 variables, una por uso, el usuario aclaró: «Pensaba que ibas a hacer lo de la direccion visual y no extraer todas las variables». La dirección visual lo resolverá con una escala sobre la base de 4 px de la guía y unas pocas variables de función.
- **S4 — Sin cambio visual.** Usuario, al elegir entre conservar los valores o reducirlos ya a una escala: «Sí» a conservarlos. Cada valor se mantiene aunque difiera de la guía; elegir la escala es una decisión de la dirección visual.
  - Aceptación: estilos calculados idénticos entre `main` y la rama en todos los elementos visibles, a 1440 × 900 y 390 × 844, en la bienvenida, Credenciales (Duplicados y Todas), Auditoría, Papelera, Ajustes y los diálogos de comparación, ficha, sesión y confirmación. Es el método de `css-tokens` (L6), más fiable que comparar píxeles. El script vive fuera del repositorio.
- **S5 — Diferencias con la guía, anotadas y no corregidas.** La guía visual (§2.2) pide textos de 13 px o más, espaciado sobre una base de 4 px y radios de 8, 12 y 16 px. El código usa textos de 11 y 12 px y ocho radios distintos. El espaciado, también fuera de la base de 4 px (5, 6, 7, 9, 10, 15 px…), lo resuelve la dirección visual (S3). Cada diferencia queda en el Log como entrada para la dirección visual.
- **S6 — Fuera de alcance.**
  - **La escala tipográfica, la identidad y la jerarquía.** Son la dirección visual, que reescribirá §1 y §2 de la guía.
  - **`feat/audit-layout`.** Aparcada sin fusionar (su L10).

## Tasks

- [x] T1 — S2, S5: inventario y correspondencia valor → variable de tipografía y radios en el Log: cada literal, dónde se usa, la variable elegida y su diferencia con la guía. Ruta: inline. Sin código.
- [x] T2 — S2, S4: sustitución de tipografía y radios en `style.css` y comparación de estilos calculados entre `main` y la rama. Excepción a RED: refactorización sin cambio de comportamiento; las comprobaciones son S2 (`grep`), S4 (estilos calculados), `npm run build` y `npm run e2e`. Riesgo: ninguna prueba versionada detecta una regresión visual, así que lleva verificación independiente. Ruta: inline.
- ~~T3 — inventario del espaciado~~ y ~~T4 — sustitución del espaciado~~: retiradas en L6; el espaciado pasa a la dirección visual.
- [x] T5 — Documentación: la guía visual (§2.2) dice que los valores de tipografía y radios viven en variables y enlaza las diferencias de S5; la hoja de ruta pasa el espaciado a la dirección visual. Ruta: inline.

## Log

- **L1 (2026-11-12).** El usuario descarta `audit-layout` tras probarlo y propone experimentar con la interfaz de toda la aplicación. Análisis de `style.css` en `feat/audit-layout`: `css-tokens` convirtió en variables solo los colores (unas 45). Quedan a mano 14 tamaños de letra en 36 sitios, 7 radios, la familia tipográfica del sistema y unos 32 valores de espaciado. La guía visual (§2.2) ya fija una escala, un espaciado base y tres radios que el código no sigue, y su §1 no define identidad ni jerarquía.
- **L2 (2026-11-12).** Decisiones del usuario:
  - Aparcar `feat/audit-layout`: «Sí. Me parece que es lo mejor. La UI es igual de importante para entender lo que se está haciendo.»
  - Conservar los valores actuales en las variables, sin cambio visual: «Sí».
  - Sobre la guía, preguntó «deberíamos establecer una guia visual?». Ya existe, `docs/guia-visual.md`; la dirección visual reescribirá su §1 y su §2 en lugar de crear otra.
  - Rama `refactor/scale-tokens` desde `main` (`4ef1105`). Recuento en `main`: 34 `font-size` (13 valores), 17 `border-radius` (8 valores), 9 `font-weight`, 4 `line-height`, 1 `font-family`. El espaciado queda fuera (S5). Previsión: ~60 líneas cambiadas, porque las líneas de `style.css` son muy largas.
- **L3 (2026-11-12).** Decisiones del usuario: «Sí, añádelo a la Fase 2. Los espaciados también deberían entrar. Aunque sea más trabajo.»
  - Hoja de ruta: este plan pasa a ser el n.º 2 de la Fase 2, seguido de la dirección visual (plan por escribir) y de rehacer la Auditoría. El resto de la Fase 2 va después, para no rehacer el estilo de cada plan.
  - El espaciado entra (S3), con su inventario (T3) y su sustitución (T4) separados de los de tipografía y radios. Recuento en `main`: 185 valores en píxeles en `padding`, `margin` y `gap`, de 34 valores distintos. Previsión total: ~100 líneas cambiadas; las líneas de `style.css` son muy largas, así que cada una agrupa muchos cambios.
- **L4 (2026-11-12).** T1: correspondencia valor → variable de tipografía y radios, sobre `main` (`4ef1105`). 33 variables para 61 usos (de los 65 literales, se retiran dos reglas muertas y quedan dos radios `0`). Los tamaños se agrupan por su papel en la jerarquía, no por componente: un componente usa la variable del papel que cumple. Los iconos de texto llevan `--icon-…` aparte, porque la dirección visual los cambiará con otro criterio que el texto.
  - **Dos reglas muertas, que se retiran en T2.** En móvil, `.topbar h1{font-size:23px}` y `.metric strong{font-size:23px}` nunca se aplican: la cabecera y las métricas viven siempre dentro de `.sticky-head`, y `.sticky-head h1` (20 px, mismo peso y declarada después) y `.sticky-head .metric strong` (16 px, más específica) las anulan. Darles una variable sería nombrar un valor que no se ve; retirarlas no cambia ningún estilo calculado, y S4 lo comprueba.

| Variable | Valor | Usos | Guía (§2.2) |
|---|---|---|---|
| `--font-sans` | `Segoe UI,Roboto,Noto Sans,Arial,sans-serif` | `:root` | igual |
| `--type-heading-1` | 26px | `h1` | 24–28 px: dentro |
| `--type-heading-1-compact` | 20px | `.sticky-head h1` (móvil) | — |
| `--type-heading-2` | 20px | `h2` | 18–20 px: dentro |
| `--type-heading-3` | 17px | `h3` | por debajo de los 18–20 px de un título de sección |
| `--type-body` | 16px | `:root`, `.warning-title` | igual |
| `--type-data` | 14px | `.desktop-table`, `.audit-item`, `.editor-fields>label:not(.check)`, `.session-field` | 14–15 px: dentro |
| `--type-data-compact` | 13px | `.audit-item` (móvil) | por debajo de los 14–15 px de los datos |
| `--type-help` | 13px | `small,.muted,.hint`, `.topbar p`, `.section-heading p`, `.warning-footer` | 13–14 px: dentro |
| `--type-control-compact` | 13px | `.desktop-table button`, `.compare-actions button`, `.sticky-head .top-actions button` (móvil) | — |
| `--type-caption` | 12px | `.brand small`, `.sidebar-note`, `.metric span`, `.status`, `.compare-flags span`, `.mobile-nav button span` (móvil) | **por debajo de 13 px** |
| `--type-caption-compact` | 11px | `.sticky-head .metric span` (móvil) | **por debajo de 13 px** |
| `--type-metric` | 20px | `.metric strong` | — |
| `--type-metric-compact` | 16px | `.sticky-head .metric strong` (móvil) | — |
| `--type-audit-count` | 25px | `.audit-count` | — |
| `--icon-brand` | 32px | `.brand-mark` | iconos de 18–24 px: **por encima** |
| `--icon-hero` | 38px | `.big-icon` | **por encima** |
| `--icon-nav` | 22px | `.mobile-nav button` (móvil) | dentro |
| `--icon-sort` | 12px | `.sort-icon` | **por debajo** |
| `--weight-regular` | 400 | `:root`, `.editor-fields input…` | — |
| `--weight-semibold` | 600 | `.sidebar nav button`, `.desktop-table th`, `.table-link`, `.editor-fields>label:not(.check)`, `.session-field` | — |
| `--weight-bold` | 700 | `.primary`, `.audit-count` | — |
| `--leading-body` | 1.5 | `p` | — |
| `--leading-table` | 1.35 | `.desktop-table .table-link`, `.desktop-table .url-truncate` | — |
| `--leading-tight` | 1.2 | `.metric strong`, `.sticky-head .metric span` (móvil) | — |
| `--radius-card` | 15px | `.card,.metric` | 12 px en tarjetas: **distinto** |
| `--radius-dropzone` | 14px | `.dropzone` | 16 px en paneles: **distinto** |
| `--radius-item` | 12px | `.audit-block`, `.compare-card`, `.record-card` | 12 px: igual |
| `--radius-notice` | 10px | `.error`, `.warning`, `.change` | **sin equivalente** |
| `--radius-track` | 10px | `.progress` | **sin equivalente** |
| `--radius-control` | 9px | `button`, campos de `.filters` y `.editor-fields`, `.audit-block details`, `.session-field input` | 8 px en controles: **distinto** |
| `--radius-badge` | 7px | `.status` | **sin equivalente** |
| `--radius-chip` | 6px | `.compare-flags span` | **sin equivalente** |

  - Se quedan como literales: `border-radius:0` (`.tabs button`, `.desktop-table th .sort-button`) y `font:inherit` (S2).
  - Para la dirección visual (S5): siete textos y un icono por debajo de 13 px; cuatro papeles con 13 px (ayuda, datos compactos, controles compactos) y tres con 20 px (título de sección, título compacto, métrica), sin nada que los distinga; ocho radios donde la guía pide tres.
- **L5 (2026-11-12).** T2 hecha. `style.css` define en `:root`, tras los colores, las 33 variables de L4, y las usa en 61 declaraciones. Se retiran las dos reglas muertas de L4.
  - S2: fuera de `:root` solo quedan los dos `border-radius:0` permitidos (`grep`).
  - S4: comparación de estilos calculados sobre el mismo DOM, cambiando la hoja de estilos de la página entre la de la rama y la de `main` compilada aparte. Cubre todas las propiedades salvo las variables, en cada elemento y en sus `::before` y `::after`. 22 estados: bienvenida, confirmación, Duplicados, comparación, Todas, ficha, sesión, Auditoría, Papelera, Ajustes y un aviso de error insertado como sonda, cada uno a 1440 × 900 y a 390 × 844; con el aviso de importación y el de cambio visibles. Resultado: 4 604 elementos, 0 diferencias.
  - Control negativo: con un solo radio alterado en el CSS de `main` (`.status`, de 7 a 8 px), la comparación da diferencias en todas las pantallas donde aparece una etiqueta de estado.
  - Sin cubrir por la comparación: los estados `:hover` y `:focus-visible`. Ninguna de sus reglas declara las propiedades de este plan (`grep`), así que no les afecta.
  - `npm run build` y la suite E2E completa (196 pruebas) en verde.
- **L6 (2026-11-12).** T3 llegó a una correspondencia completa del espaciado: 136 declaraciones, 133 variables (casi una por uso, porque apenas hay funciones que compartan valor) y cinco declaraciones muertas más dentro de `.sticky-head`. Ante la pregunta de si aplicarla o dejar el espaciado para la dirección visual, el usuario aclaró: «Pensaba que ibas a hacer lo de la direccion visual y no extraer todas las variables». Había entendido «Los espaciados también deberían entrar» como extraerlos ya; la intención era resolverlos con la escala. Se retiran T3 y T4 sin aplicar nada: el espaciado pasa a la dirección visual, con una escala sobre la base de 4 px y pocas variables de función. Las cinco declaraciones muertas (`.topbar` y `.metrics` `margin-bottom`; en móvil, `.top-actions` `margin-top`, `.metrics` `gap` y `.metric` `padding`) quedan anotadas para entonces.
- **L7 (2026-11-12).** T5, documentación: `docs/guia-visual.md` (§2.2: dónde viven las variables, sus diferencias con la escala y que el espaciado queda para la dirección visual) y `docs/hoja-de-ruta.md` (el plan enlaza a `odd/done/`). El plan pasa a `odd/done/`.
- **L8 (2026-11-12).** Verificación independiente de T2: **superada**, sin bloqueos ni advertencias. El verificador trabajó en copias aparte de `main` (`4ef1105`) y de la rama (`f282a81`), cada una compilada y servida por turnos en el puerto 5173, con un script propio:
  - S2: fuera de `:root` solo quedan `border-radius:0` y `font:inherit`; las 33 variables están definidas y en uso; `style.css` es el único archivo de código que cambia.
  - S4: estilos calculados de cada elemento y de sus `::before` y `::after` en 11 estados a 1440 × 900 y a 390 × 844, con el aviso de importación y el de cambio visibles: 3 888 entradas, 0 diferencias. Control negativo: un radio de `.status` alterado en 1 px da 44 diferencias por tamaño.
  - Las dos reglas retiradas estaban muertas: el único `h1` y las cuatro métricas viven siempre dentro de `.sticky-head`.
  - `npm run build` pasa en las dos copias. Sin cubrir, igual que en T2: `:hover` y `:focus-visible`, que no declaran estas propiedades.
