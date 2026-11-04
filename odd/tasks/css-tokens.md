# Colores en variables CSS

Objetivo: sustituir los colores escritos directamente en `frontend/src/style.css` por variables CSS en `:root`, sin ningún cambio visual. Es la base del futuro tema claro y de los estilos de tabla y de foco de la Fase 1.
Rama: `refactor/css-tokens` desde `main`. Primer bloque de la Fase 1: no depende de otros; `native-tables` y `keyboard-accessibility` usan sus variables. Entrega: `ask-on-risk`, previsión ~60 líneas cambiadas (las 38 líneas de `style.css` son muy largas), un único PR.
Comprobaciones: `npm run build` y `npm run e2e` en `frontend/`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`; además, la comparación de capturas de S2. Estado: en curso desde el 2026-11-04 (L4).

## Specs

- **S1 — Variables de color.** Bloque «Colores en variables CSS» de la Fase 1, autorizado en L2: «Con D1 resuelta, puede preparar las tareas de la Fase 1 en `odd/tasks/`, incluyendo dependencias, criterios de aceptación y pruebas, sin comenzar todavía la implementación.» Paleta de referencia: guía visual, §2.1 (`surface/page`, `surface/card`, `surface/raised`, `text/primary`, `text/secondary`, `accent`, `success`, `warning`, `danger`, `border/control`).
  - Cada color literal de `style.css` (en `main` `27734ba`: 86 apariciones, 44 valores distintos) pasa a `var(--…)`, con la variable definida en `:root`.
  - Nombres: el token de la guía cuando el uso coincide (`--surface-page`, `--text-primary`…); los colores sin equivalente en la guía se nombran por su función, no por su valor (por ejemplo, `--status-pending-bg`, no `--blue-2`).
  - Aceptación: fuera de `:root` no queda en `style.css` ningún literal `#…`, `rgb()`, `rgba()`, `hsl()` ni `hsla()`, comprobable con `grep`. Se permiten `transparent`, `currentColor` e `inherit`.
- **S2 — Sin cambio visual.** Cada color mantiene su valor actual, aunque difiera del que propone la guía. Las diferencias con la guía se anotan en el Log como entrada para el tema claro (Fase 4), sin aplicarlas.
  - Aceptación: capturas de `main` y de la rama con los mismos datos ficticios, en 1440 × 900 y 390 × 844, de la bienvenida, Credenciales (Duplicados y Todas), Auditoría, Papelera y Ajustes, y de los diálogos de comparación, ficha, sesión y confirmación. La diferencia debe ser de 0 píxeles. El script de capturas vive en un directorio temporal fuera del repositorio y no se versiona.
- **S3 — Contraste medido, no corregido.** Guía, §2.1: «Colores **propuestos**, sujetos a mediciones automáticas de contraste en implementación: AA en texto normal (≥ 4,5:1), ≥ 3:1 para componentes/indicadores significativos y foco visible.» Se calcula el contraste de los pares texto/fondo, control/fondo y foco/fondo que estén en uso, y se registra en el Log. **Supuesto:** corregir un par que no cumpla supone un cambio visual, así que se decide con el usuario y queda fuera de esta rama.
- **S4 — Fuera de alcance.** El tema claro, su selector y la preferencia del usuario (Fase 4). Los colores que PrimeVue inyecta en tiempo de ejecución en las tablas, que desaparecen con `native-tables`.

## Tasks

- [x] T1 — S1, S2: inventario y correspondencia valor → variable en el Log (cada literal, dónde se usa, la variable elegida y su diferencia con la guía). Ruta: inline. Sin código. Tabla en L5.
- [ ] T2 — S1, S2: sustitución en `style.css` y comparación de capturas `main` frente a la rama (0 píxeles de diferencia). Excepción a RED: refactorización sin cambio de comportamiento; las comprobaciones son S1 (`grep`), S2 (capturas), `npm run build` y `npm run e2e` en verde. Riesgo: punto 6 (ninguna prueba versionada detecta una regresión visual), mitigado por la comparación de capturas; requiere verificación independiente. Ruta: inline.
- [ ] T3 — S3: tabla de contrastes en el Log. Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-03).** Decisión D1 y encargo de la Fase 1. Texto completo en `odd/tasks/native-tables.md`, L2. Fragmentos que afectan a este bloque: «mantener toda una biblioteca de componentes no parece justificado, especialmente cuando queremos mejorar la accesibilidad, incorporar temas y optimizar el frontend.» «Mantendría las tareas pequeñas e independientes y el flujo habitual de implementación, revisión y aceptación antes de integrar en `main`.» «Con D1 resuelta, puede preparar las tareas de la Fase 1 en `odd/tasks/`, incluyendo dependencias, criterios de aceptación y pruebas, sin comenzar todavía la implementación.» «No hace falta resolver D2–D7 para planificar los bloques de la Fase 1 que no dependen de esas decisiones.» Y: «No implementes nada.»
- **L3 (2026-11-03).** Análisis en `main` (`27734ba`): `style.css` no define ninguna variable CSS (solo usa `--header-height` y `--nav-height`, que fija `App.vue` en línea). Tiene 86 colores literales (44 distintos). Ya incluye `:focus-visible` con un contorno de 3 px y `prefers-reduced-motion`. Tres selectores dependen de clases de PrimeVue (`.p-datatable…`); los retira `native-tables`, no este bloque. Orden recomendado de la Fase 1: `css-tokens` → `native-tables` → `keyboard-accessibility` → `frontend-bundle` (T1 de `frontend-bundle` puede ir en cualquier momento). Ruta declarada: inline en todas las tareas; no aplica ningún disparador de escritor (una sola unidad sobre un archivo).
- **L4 (2026-11-04).** El usuario aprueba empezar: «¿Empiezo con `css-tokens`?» Respuesta: «Sí». Rama `refactor/css-tokens` desde `main` (`a5f033e`). Comprobado de nuevo: `style.css` tiene 86 colores literales de 44 valores distintos, y no hay colores en los `.vue` ni en los `.ts`.
- **L5 (2026-11-04).** T1: correspondencia valor → variable. 47 variables para 86 usos. Un mismo valor lleva dos variables cuando cumple dos funciones (`#101923`, `#293b50` y `#9bd6ff`). Solo dos colores difieren de la guía: `--danger` y `--border-control`; se conservan sin cambios (S2) y quedan como entrada para el tema claro (Fase 4).

| Variable | Valor | Token de la guía | Diferencia con la guía | Usos |
|---|---|---|---|---|
| `--surface-page` | `#0b1017` | `surface/page` | igual | 3: `.shell (background); .sticky-head (background); :root (background)` |
| `--surface-card` | `#141c27` | `surface/card` | igual | 4: `.card,.metric (background); .desktop-table td (background); .drawer-actions (background); .mobile-nav (background)` |
| `--surface-raised` | `#1b2635` | `surface/raised` | igual | 6: `.audit-block (background); .compare-card (background); .desktop-table th (background); .record-card (background); .sidebar .brand:hover:not(:disabled) (background); button (background)` |
| `--surface-sidebar` | `#101923` | — | — | 1: `.sidebar (background)` |
| `--surface-input` | `#101923` | — | — | 2: `.filters input:not([type=checkbox]),.filters select,.editor-fields input:not([type=checkbox]),.editor-fields textarea,.editor-fields select (background); .session-field input (background)` |
| `--surface-hover` | `#293b50` | — | — | 1: `button:hover:not(:disabled) (background)` |
| `--surface-chip` | `#293b50` | — | — | 1: `.compare-flags span (background)` |
| `--surface-selected` | `#1d3854` | — | — | 2: `.dropzone.dragging (background); .sidebar nav button.active (background)` |
| `--surface-track` | `#364456` | — | — | 1: `.progress (background)` |
| `--overlay` | `#000a` | — | — | 1: `.overlay (background)` |
| `--shadow` | `#0008` | — | — | 2: `.error (box-shadow); .warning (box-shadow)` |
| `--text-primary` | `#f1f5f9` | `text/primary` | igual | 5: `.audit-count (color); .filters input:not([type=checkbox]),.filters select,.editor-fields input:not([type=checkbox]),.editor-fields textarea,.editor-fields select (color); .session-field input (color); :root (color); button (color)` |
| `--text-secondary` | `#b6c4d5` | `text/secondary` | igual | 6: `.brand small (color); .metric span (color); .mobile-nav button (color); .tabs button (color); p (color); small,.muted,.hint (color)` |
| `--text-table-head` | `#c5d6e7` | — | — | 1: `.desktop-table th (color)` |
| `--text-link` | `#9bd6ff` | — | — | 1: `.table-link (color)` |
| `--text-nav-active` | `#b6deff` | — | — | 1: `.sidebar nav button.active (color)` |
| `--text-on-accent` | `#092035` | — | — | 1: `.primary (color)` |
| `--accent` | `#7cc4ff` | `accent` | igual | 10: `.big-icon (color); .brand-mark (color); .check input (accent-color); .dropzone.dragging (border-color); .mobile-nav button.active (color); .primary (background); .primary (border-color); .tabs button.selected (border-bottom); .tabs button.selected (color); button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible (outline)` |
| `--accent-hover` | `#b4deff` | — | — | 1: `.primary:hover:not(:disabled) (background)` |
| `--success` | `#61d6b1` | `success` | igual | 1: `.progress span (background)` |
| `--warning` | `#ffd07a` | `warning` | igual | 1: `.status.multiple-accounts (color)` |
| `--danger` | `#ffb4ba` | `danger` | la guía propone `#ff929d` | 2: `.danger (color); .status.conflict,.status.incorrect (color)` |
| `--danger-bg` | `#43252d` | — | — | 2: `.danger:hover:not(:disabled) (background); .status.conflict,.status.incorrect (background)` |
| `--danger-border` | `#6b3a44` | — | — | 1: `.danger (border-color)` |
| `--status-text` | `#ccd5e1` | — | — | 1: `.status (color)` |
| `--status-border` | `#48576b` | — | — | 1: `.status (border)` |
| `--status-info-text` | `#9bd6ff` | — | — | 1: `.status.exact,.status.reviewed (color)` |
| `--status-info-bg` | `#1b3854` | — | — | 1: `.status.exact,.status.reviewed (background)` |
| `--status-success-text` | `#8eebcf` | — | — | 1: `.status.verified (color)` |
| `--status-success-bg` | `#164337` | — | — | 1: `.status.verified (background)` |
| `--status-warning-bg` | `#4a3922` | — | — | 1: `.status.multiple-accounts (background)` |
| `--border-control` | `#52657b` | `border/control` | la guía propone `#62758f` | 2: `.filters input:not([type=checkbox]),.filters select,.editor-fields input:not([type=checkbox]),.editor-fields textarea,.editor-fields select (border); .session-field input (border)` |
| `--border-button` | `#42566e` | — | — | 1: `button (border)` |
| `--border-card` | `#29384a` | — | — | 3: `.card,.metric (border); .desktop-table th,.desktop-table td (border-bottom); .drawer-actions (border-top)` |
| `--border-raised` | `#34445a` | — | — | 3: `.compare-card (border); .mobile-nav (border-top); .record-card (border)` |
| `--border-sidebar` | `#28374a` | — | — | 1: `.sidebar (border-right)` |
| `--border-sticky-head` | `#1d2938` | — | — | 1: `.sticky-head (border-bottom)` |
| `--border-tabs` | `#304057` | — | — | 1: `.tabs (border-bottom)` |
| `--border-dropzone` | `#4d6e8a` | — | — | 1: `.dropzone (border)` |
| `--border-audit` | `#334359` | — | — | 1: `.audit-block (border)` |
| `--border-audit-item` | `#46566a` | — | — | 2: `.audit-block details (border); .audit-item (border-bottom)` |
| `--border-settings-row` | `#405169` | — | — | 1: `.settings-row (border-bottom)` |
| `--notice-error-bg` | `#552a36` | — | — | 1: `.error (background)` |
| `--notice-error-text` | `#ffe5e7` | — | — | 1: `.error (color)` |
| `--notice-warning-bg` | `#4a3a1e` | — | — | 1: `.warning (background)` |
| `--notice-warning-text` | `#ffe9c4` | — | — | 1: `.warning (color)` |
| `--notice-warning-footer` | `#e8cf9f` | — | — | 1: `.warning-footer (color)` |
