# Colores en variables CSS

Objetivo: sustituir los colores escritos directamente en `frontend/src/style.css` por variables CSS en `:root`, sin ningún cambio visual. Es la base del futuro tema claro y de los estilos de tabla y de foco de la Fase 1.
Rama: `refactor/css-tokens` desde `main`. Primer bloque de la Fase 1: no depende de otros; `native-tables` y `keyboard-accessibility` usan sus variables. Entrega: `ask-on-risk`, previsión ~60 líneas cambiadas (las 38 líneas de `style.css` son muy largas), un único PR.
Comprobaciones: `npm run build` y `npm run e2e` en `frontend/`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`; además, la comparación de capturas de S2. Estado: planificado, sin empezar.

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

- [ ] T1 — S1, S2: inventario y correspondencia valor → variable en el Log (cada literal, dónde se usa, la variable elegida y su diferencia con la guía). Ruta: inline. Sin código.
- [ ] T2 — S1, S2: sustitución en `style.css` y comparación de capturas `main` frente a la rama (0 píxeles de diferencia). Excepción a RED: refactorización sin cambio de comportamiento; las comprobaciones son S1 (`grep`), S2 (capturas), `npm run build` y `npm run e2e` en verde. Riesgo: punto 6 (ninguna prueba versionada detecta una regresión visual), mitigado por la comparación de capturas; requiere verificación independiente. Ruta: inline.
- [ ] T3 — S3: tabla de contrastes en el Log. Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-03).** Decisión D1 y encargo de la Fase 1. Texto completo en `odd/tasks/native-tables.md`, L2. Fragmentos que afectan a este bloque: «mantener toda una biblioteca de componentes no parece justificado, especialmente cuando queremos mejorar la accesibilidad, incorporar temas y optimizar el frontend.» «Mantendría las tareas pequeñas e independientes y el flujo habitual de implementación, revisión y aceptación antes de integrar en `main`.» «Con D1 resuelta, puede preparar las tareas de la Fase 1 en `odd/tasks/`, incluyendo dependencias, criterios de aceptación y pruebas, sin comenzar todavía la implementación.» «No hace falta resolver D2–D7 para planificar los bloques de la Fase 1 que no dependen de esas decisiones.» Y: «No implementes nada.»
- **L3 (2026-11-03).** Análisis en `main` (`27734ba`): `style.css` no define ninguna variable CSS (solo usa `--header-height` y `--nav-height`, que fija `App.vue` en línea). Tiene 86 colores literales (44 distintos). Ya incluye `:focus-visible` con un contorno de 3 px y `prefers-reduced-motion`. Tres selectores dependen de clases de PrimeVue (`.p-datatable…`); los retira `native-tables`, no este bloque. Orden recomendado de la Fase 1: `css-tokens` → `native-tables` → `keyboard-accessibility` → `frontend-bundle` (T1 de `frontend-bundle` puede ir en cualquier momento). Ruta declarada: inline en todas las tareas; no aplica ningún disparador de escritor (una sola unidad sobre un archivo).
