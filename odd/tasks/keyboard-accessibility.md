# Accesibilidad y teclado

Objetivo: hacer la revisión de accesibilidad y teclado que pide `docs/pendiente.md`, y corregir lo que ya se sabe que falta: la gestión del foco en los diálogos de comparación, ficha y sesión, y la semántica de las pestañas y de la navegación.
Rama: `feat/keyboard-accessibility` desde `main`, después de integrar `css-tokens` y `native-tables` (comparten `style.css` y `App.vue`; el teclado de las tablas se resuelve en `native-tables`). Entrega: `ask-on-risk`, previsión ~350 líneas cambiadas, un único PR.
Comprobaciones por tarea: `npm run build` y `npm run e2e` en `frontend/`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: planificado, sin empezar.

## Specs

- **S1 — Alcance.** `docs/pendiente.md`, «Trabajo pendiente»: «Una revisión más amplia de accesibilidad y teclado.» Decisión D1 (L2): «queremos mejorar la accesibilidad». Y en L2: «No hace falta resolver D2–D7 para planificar los bloques de la Fase 1 que no dependen de esas decisiones.» Por eso `Esc` (D2) queda fuera. Se conserva lo documentado en `docs/flujo-usuario.md`: «Los demás diálogos (comparación, ficha, sesión cifrada) no se cierran con `Esc`.»
- **S2 — Revisión.** Criterios de `docs/guia-visual.md`:
  - §2.2: «Foco de teclado destacado (contorno sólido de 2 px, color contrastado). Componentes tabulares navegables con teclado.» «Iconos de **18–24 px**, siempre acompañados de etiqueta accesible.» «Controles táctiles: objetivo **44 × 44 px o mayor**, salvo controles de escritorio claramente diferenciados.» «Respetar `prefers-reduced-motion`.»
  - §4: «**Interacción teclado:** `Tab` recorre controles, `Enter` abre registro; confirmar de forma explícita las acciones destructivas.»
  - §8: «Zoom 200 % y teclado | Foco visible, navegación y controles no ocultos»; «Móvil 360 px con teclado abierto | Guardar/cancelar siempre accesible».
  - Resultado: lista de hallazgos en el Log, cada uno con la pantalla, el criterio y la evidencia. Lo que S3 y S4 no cubran se convierte en una tarea nueva solo con la aprobación del usuario.
  - **Supuesto:** no se añaden herramientas automáticas (por ejemplo, axe-core), porque serían una dependencia nueva; si se quieren, es una decisión aparte.
  - Ya existen, y la revisión solo comprueba que cubren todos los controles: `:focus-visible` con contorno de 3 px en `button`, `input`, `select` y `textarea`, y `prefers-reduced-motion`.
- **S3 — Foco en los diálogos de comparación, ficha y sesión.** Hoy solo `ConfirmDialog` gestiona el foco. Según `docs/flujo-usuario.md`, el diálogo de confirmación «empieza con el foco en «Cancelar», `Tab` no sale de él y, al cerrarse, el foco vuelve al control que lo abrió». Los otros tres diálogos deben comportarse igual:
  - Al abrirse, el foco entra en el diálogo. **Supuesto, a confirmar al aprobar el plan:** en la ficha, el campo «Nombre»; en la sesión, el primer campo; en la comparación, su título (`tabindex="-1"`), para que se lea el contenido antes que los botones.
  - Mientras está abierto, `Tab` y `Mayús+Tab` no salen de él.
  - Al cerrarse, el foco vuelve al control que lo abrió. **Supuesto:** si ese control ya no existe (por ejemplo, la fila se movió a la papelera), el foco va al título de la sección.
  - El diálogo de confirmación abierto encima de otro diálogo sigue funcionando como hoy.
  - La lógica de foco de `ConfirmDialog` se extrae a una única función reutilizable que usan los cuatro diálogos; las E2E actuales de `ConfirmDialog` siguen pasando.
- **S4 — Pestañas y navegación.**
  - «Duplicados» y «Todas» siguen el patrón de pestañas de WAI-ARIA APG: `role="tab"`, `aria-selected`, `aria-controls`, el panel con `role="tabpanel"`, y las flechas cambian de pestaña. **Supuesto:** activación automática al moverse con las flechas.
  - Las E2E que pulsan «Todas (N)» como `button` (unas 13 en `component-events.spec.ts` e `import-warnings.spec.ts`) pasan a seleccionar el rol `tab`; las aserciones no cambian.
  - Navegación lateral e inferior: la pantalla activa lleva `aria-current="page"`.
- **S5 — Fuera de alcance:**
  - `Esc` (D2).
  - El teclado de las tablas (`native-tables`).
  - Corregir contrastes (`css-tokens`, S3, decisión del usuario).
  - Los avisos de error y advertencia: `NoticeBase.vue` ya usa `role="alert"` y `role="status"`.

## Tasks

- [ ] T1 — S2: revisión con teclado, zoom al 200 % y pantalla de 360 px; hallazgos en el Log. Ruta: inline. Sin código.
- [ ] T2 — S3: foco de los diálogos. Ruta: inline.
  - RED primero: E2E de foco inicial, `Tab` que no sale del diálogo y retorno del foco, en cada uno de los tres diálogos.
  - Implementar la función compartida y migrar `ConfirmDialog` a ella.
  - Comprobación diferencial: las E2E de `ConfirmDialog` dan el mismo resultado antes y después.
  - Riesgo: punto 3 (la lógica de foco de `ConfirmDialog` pasa a ser compartida). Requiere verificación independiente.
- [ ] T3 — S4: pestañas y navegación. Ruta: inline.
  - RED primero: E2E de flechas, `aria-selected` y `aria-current`.
  - Cambio de los selectores de rol en las E2E afectadas.
- [ ] T4 — Documentación: `docs/flujo-usuario.md` (foco de los diálogos y teclado en las pestañas) y, si cambia algún criterio, `docs/guia-visual.md`. Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-03).** Decisión D1 y encargo de la Fase 1. Texto completo en `odd/tasks/native-tables.md`, L2. Fragmentos que afectan a este bloque: «2. Accesibilidad desde el principio: HTML semántico, `aria-sort`, navegación por teclado y gestión correcta del foco.» «Mantendría las tareas pequeñas e independientes y el flujo habitual de implementación, revisión y aceptación antes de integrar en `main`.» «Con D1 resuelta, puede preparar las tareas de la Fase 1 en `odd/tasks/`, incluyendo dependencias, criterios de aceptación y pruebas, sin comenzar todavía la implementación.» «No hace falta resolver D2–D7 para planificar los bloques de la Fase 1 que no dependen de esas decisiones.» Y: «No implementes nada.»
- **L3 (2026-11-03).** Análisis en `main` (`27734ba`):
  - `focus()` solo aparece en `ConfirmDialog.vue`.
  - La barra de pestañas tiene `role="tablist"`, pero sus botones no llevan `role="tab"` ni `aria-selected`.
  - `NoticeBase.vue` ya asigna `role="alert"` o `role="status"` (con `:role`). La evaluación inicial lo dio por ausente porque la búsqueda no detectó el atributo enlazado; está corregido y se ha quitado del alcance.
  - `style.css` ya incluye `:focus-visible` (3 px) y `prefers-reduced-motion`.
  - Ruta: inline en todas las tareas; no aplica el disparador de escritor (las unidades comparten `App.vue`, `style.css` y los E2E).
