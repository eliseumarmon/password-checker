# Accesibilidad y teclado

Objetivo: hacer la revisión de accesibilidad y teclado que pide `docs/pendiente.md`, y corregir lo que ya se sabe que falta: la gestión del foco en los diálogos de comparación, ficha y sesión, y la semántica de las pestañas y de la navegación.
Rama: `feat/keyboard-accessibility` desde `main`, después de integrar `css-tokens` y `native-tables` (comparten `style.css` y `App.vue`; el teclado de las tablas se resuelve en `native-tables`). Entrega: `ask-on-risk`, por tramos a `main` (L9): tramo 1, T2 con su documentación; tramo 2, T3 y lo que quede de T4.
Comprobaciones por tarea: `npm run build` y `npm run e2e` en `frontend/`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: en curso desde el 2026-11-09 (L5). **Hecho** (L18). Tramos 1 y 2 integrados en `main` (`e1dd3f5` y `2db587b`); el tramo 3 se integra con esta rama.

## Specs

- **S1 — Alcance.** `docs/pendiente.md`, «Trabajo pendiente»: «Una revisión más amplia de accesibilidad y teclado.» Decisión D1 (L2): «queremos mejorar la accesibilidad». Y en L2: «No hace falta resolver D2–D7 para planificar los bloques de la Fase 1 que no dependen de esas decisiones.»
  - **D2 aprobada, opción A (L5).** `Esc` entra como requisito de T2 con su prueba E2E. Deja de aplicarse lo documentado en `docs/flujo-usuario.md`: «Los demás diálogos (comparación, ficha, sesión cifrada) no se cierran con `Esc`.»
- **S2 — Revisión.** Criterios de `docs/guia-visual.md`:
  - §2.2: «Foco de teclado destacado (contorno sólido de 2 px, color contrastado). Componentes tabulares navegables con teclado.» «Iconos de **18–24 px**, siempre acompañados de etiqueta accesible.» «Controles táctiles: objetivo **44 × 44 px o mayor**, salvo controles de escritorio claramente diferenciados.» «Respetar `prefers-reduced-motion`.»
  - §4: «**Interacción teclado:** `Tab` recorre controles, `Enter` abre registro; confirmar de forma explícita las acciones destructivas.»
  - §8: «Zoom 200 % y teclado | Foco visible, navegación y controles no ocultos»; «Móvil 360 px con teclado abierto | Guardar/cancelar siempre accesible».
  - Resultado: lista de hallazgos en el Log, cada uno con la pantalla, el criterio y la evidencia. Lo que S3 y S4 no cubran se convierte en una tarea nueva solo con la aprobación del usuario.
  - **Supuesto:** no se añaden herramientas automáticas (por ejemplo, axe-core), porque serían una dependencia nueva; si se quieren, es una decisión aparte.
  - Ya existen, y la revisión solo comprueba que cubren todos los controles: `:focus-visible` con contorno de 3 px en `button`, `input`, `select` y `textarea`, y `prefers-reduced-motion`.
- **S3 — Foco en los diálogos de comparación, ficha y sesión.** Hoy solo `ConfirmDialog` gestiona el foco. Según `docs/flujo-usuario.md`, el diálogo de confirmación «empieza con el foco en «Cancelar», `Tab` no sale de él y, al cerrarse, el foco vuelve al control que lo abrió». Los otros tres diálogos deben comportarse igual:
  - Al abrirse, el foco entra en el diálogo. **Confirmado por el usuario (L7):** en la ficha, el campo «Nombre»; en la sesión, el primer campo; en la comparación, su título (`tabindex="-1"`), para que se lea el contenido antes que los botones.
  - Mientras está abierto, `Tab` y `Mayús+Tab` no salen de él.
  - Al cerrarse, el foco vuelve al control que lo abrió. **Decidido por el usuario (L7):** si ese control ya no existe (por ejemplo, la fila se movió a la papelera), se aplica la misma regla que en las tablas: el foco pasa al mismo control de la fila siguiente, o de la anterior si era la última, o al título de la sección si no quedan filas.
  - El diálogo de confirmación abierto encima de otro diálogo sigue funcionando como hoy.
  - La lógica de foco de `ConfirmDialog` se extrae a una única función reutilizable que usan los cuatro diálogos; las E2E actuales de `ConfirmDialog` siguen pasando.
  - `Esc` (D2, opción A) cierra el diálogo de comparación, la ficha y la sesión. La ficha con cambios sin guardar pide confirmación antes de cerrarse, igual que con «✕». Con varios diálogos abiertos, `Esc` solo actúa sobre el superior.
- **S4 — Pestañas y navegación.**
  - «Duplicados» y «Todas» siguen el patrón de pestañas de WAI-ARIA APG: `role="tab"`, `aria-selected`, `aria-controls`, el panel con `role="tabpanel"`, y las flechas cambian de pestaña. **Decidido por el usuario (L7):** activación automática al moverse con las flechas.
  - Las E2E que pulsan «Todas (N)» como `button` (unas 13 en `component-events.spec.ts` e `import-warnings.spec.ts`) pasan a seleccionar el rol `tab`; las aserciones no cambian.
  - Navegación lateral e inferior: la pantalla activa lleva `aria-current="page"`.
- **S6 — Hallazgos aprobados por el usuario (L16).** De los hallazgos de T1, el usuario elige: «Foco tapado (Recomendado), Teclado móvil al abrir (Recomendado)».
  - **H1:** el control con foco no queda tapado por la cabecera fija, la barra inferior ni la barra de «Guardar» de la ficha.
  - **Teclado móvil:** en pantallas táctiles, la ficha empieza con el foco en su título, para que no se abra el teclado virtual. La sesión no cambia.
  - H2, H3 y H4 quedan pendientes.
- **S5 — Fuera de alcance:**
  - El teclado de las tablas (`native-tables`).
  - Corregir contrastes (`css-tokens`, S3, decisión del usuario).
  - Los avisos de error y advertencia: `NoticeBase.vue` ya usa `role="alert"` y `role="status"`.

## Tasks

- [x] T1 — S2: revisión con teclado, zoom al 200 % y pantalla de 360 px; hallazgos en el Log. Ruta: inline. Sin código. Evidencia en L6.
- [x] T2 — S3: foco de los diálogos y `Esc`. Ruta: inline. Commits `eddd5f8`, `5492194` y el de L11; evidencia en L8, L10 y L11.
  - RED primero: E2E de foco inicial, `Tab` que no sale del diálogo, retorno del foco y `Esc`, en cada uno de los tres diálogos.
  - Implementar la función compartida y migrar `ConfirmDialog` a ella.
  - Comprobación diferencial: las E2E de `ConfirmDialog` dan el mismo resultado antes y después.
  - Riesgo: punto 3 (la lógica de foco de `ConfirmDialog` pasa a ser compartida). Requiere verificación independiente.
- [x] T3 — S4: pestañas y navegación. Ruta: inline. Commit `a4b5c7d` y el de L14; evidencia en L13 y L14.
  - RED primero: E2E de flechas, `aria-selected` y `aria-current`.
  - Cambio de los selectores de rol en las E2E afectadas.
- [x] T4 — Documentación: `docs/flujo-usuario.md` (foco de los diálogos, hecho con T2 en L9; teclado en las pestañas, en L13) y, si cambia algún criterio, `docs/guia-visual.md`. Ruta: inline.

- [x] T5 — S6: foco no tapado. RED primero en E2E. Ruta: inline. Evidencia en L16.
- [x] T6 — S6: la ficha empieza en el título en pantallas táctiles. RED primero en E2E. Ruta: inline. Evidencia en L16.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-03).** Decisión D1 y encargo de la Fase 1. Texto completo en `odd/done/native-tables.md`, L2. Fragmentos que afectan a este bloque: «2. Accesibilidad desde el principio: HTML semántico, `aria-sort`, navegación por teclado y gestión correcta del foco.» «Mantendría las tareas pequeñas e independientes y el flujo habitual de implementación, revisión y aceptación antes de integrar en `main`.» «Con D1 resuelta, puede preparar las tareas de la Fase 1 en `odd/tasks/`, incluyendo dependencias, criterios de aceptación y pruebas, sin comenzar todavía la implementación.» «No hace falta resolver D2–D7 para planificar los bloques de la Fase 1 que no dependen de esas decisiones.» Y: «No implementes nada.»
- **L3 (2026-11-03).** Análisis en `main` (`27734ba`):
  - `focus()` solo aparece en `ConfirmDialog.vue`.
  - La barra de pestañas tiene `role="tablist"`, pero sus botones no llevan `role="tab"` ni `aria-selected`.
  - `NoticeBase.vue` ya asigna `role="alert"` o `role="status"` (con `:role`). La evaluación inicial lo dio por ausente porque la búsqueda no detectó el atributo enlazado; está corregido y se ha quitado del alcance.
  - `style.css` ya incluye `:focus-visible` (3 px) y `prefers-reduced-motion`.
  - Ruta: inline en todas las tareas; no aplica el disparador de escritor (las unidades comparten `App.vue`, `style.css` y los E2E).
- **L4 (2026-11-04).** Petición: «Necesito que documentes todos los planes y que marques las decisiones pendientes.» Con ella, el usuario aporta una revisión externa que recomienda resolver D2 durante la Fase 1, antes del bloque de accesibilidad. Se marca D2 como decisión pendiente en S1 y como dependencia de T2; las opciones están en `docs/hoja-de-ruta.md`.
- **L5 (2026-11-09).** El usuario resuelve D2: «Opción A». Y aprueba empezar: «Sí», a «¿Empiezo `keyboard-accessibility`?». Rama `feat/keyboard-accessibility`, desde `6f553e4`. Se actualizan S1, S3, S5 y T2. Las dependencias ya están integradas: `css-tokens`, `native-tables`.
- **L6 (2026-11-09).** T1, revisión con un script fuera del repositorio y datos ficticios. Recorre con `Tab` y mide 36 combinaciones: 9 estados (Duplicados, Todas, Auditoría, Papelera, Ajustes y los diálogos de comparación, ficha, sesión y confirmación) en 4 tamaños (1280 × 720; 640 × 360, equivalente a zoom al 200 %; 360 × 640; y 360 × 340, que simula el teclado virtual abierto). **No sustituye** a probar con un lector de pantalla ni con un teclado virtual real.
  - **Cumple:** todos los controles que reciben foco tienen contorno visible (3 px); ningún control carece de nombre accesible; no hay desplazamiento horizontal en ningún tamaño; el foco nunca queda fuera de la pantalla; `prefers-reduced-motion` está definido, y `ConfirmDialog` retiene el foco.
  - **Lo cubre S3:** en comparación, ficha y sesión, `Tab` sale del diálogo hacia la página de detrás.
  - **Lo cubre S4:** pestañas y navegación.
  - **Hallazgos que S3 y S4 no cubren** (según S2, pasan a tarea solo si el usuario lo aprueba):
    - **H1 — Foco tapado por la cabecera fija y la barra inferior** (§8, «Zoom 200 % y teclado | Foco visible, navegación y controles no ocultos»). A 640 × 360, la cabecera (155 px) y la barra (86 px) ocupan 241 de 360 px; en Todas quedan tapadas 41 de 89 paradas de `Tab`, y a 360 × 340, 78 de 89. A 360 × 640 solo quedan tapadas 2 paradas en Duplicados y 2 en Todas. No hay `scroll-padding` definido.
    - **H2 — Objetivos táctiles de menos de 44 px en móvil** (§2.2): «Editar →», «Comparar →» y «Restaurar», 40 px de alto; papelera, 42 × 40; pestañas, 39 de alto; campos, 43 de alto; casilla «Solo pendientes», 18 × 18; botones del comparador, 36 de alto; cierre «✕», 43 × 40.
    - **H3 — Icono de papelera de 16 px** (§2.2: 18–24 px). Tiene etiqueta accesible.
    - **H4 — «Guardar» y «Cancelar» fuera de la vista al abrir** la ficha y la sesión a 640 × 360 y 360 × 340 (§8, «Guardar/cancelar siempre accesible»). En la sesión se llega con `Tab`; en la ficha, el recorrido no llegó a esos botones (tope de 90 pulsaciones) y se comprobará en T2.
- **L7 (2026-11-09).** Decisiones del usuario sobre los supuestos de S3 y S4:
  - Foco al abrir: «Sí, correcto.»
  - Foco si el control ya no existe: «Creo recordar que iba a la fila siguiente y si no ha fila siguiente entonces sí al título. Puede ser?» Es la regla de `native-tables` (L13), con el paso intermedio de la fila anterior, y S3 la decía de otra forma. Se alinea con esa regla.
  - Pestañas: «Automático.»
- **L8 (2026-11-09).** T2:
  - **RED:** nueve pruebas nuevas en `frontend/e2e/dialogs.spec.ts`, que fallaban: foco inicial, `Tab` que no sale, `Esc` y retorno del foco en la ficha, la comparación y la sesión (guardar y abrir); `Esc` con cambios sin guardar pide confirmación y solo cierra el diálogo superior; llegar a «Guardar cambios» con `Tab`; y el foco cuando la fila que abrió el diálogo desaparece (siguiente, anterior, título, tarjetas en móvil y grupos en la comparación).
  - **GREEN:** `frontend/src/dialogFocus.ts` con `useDialogFocus`, que usan los cuatro diálogos; `ConfirmDialog` pierde su lógica propia. Una pila de diálogos abiertos hace que el teclado solo afecte al superior. Las tarjetas móviles llevan `data-row-id`, como las filas. `seed`, `chromiumRow` y demás datos de prueba pasan de `tables.spec.ts` a `e2e/tables.ts`, para compartirlos.
  - **Comprobación diferencial:** las E2E de `ConfirmDialog` siguen pasando sin cambios.
  - **Auditoría repetida** (el script de L6): 0 paradas de `Tab` fuera del diálogo en los 16 casos.
    - **H4 se reduce:** en la ficha y en la sesión, «Guardar» y «Cancelar» siguen fuera de la vista al abrir a 640 × 360 y 360 × 340, pero `Tab` llega a ellos.
    - **H1 se amplía:** ya dentro de la ficha, la barra fija de «Guardar» y «Cancelar» tapa a veces el campo con foco («Estado de revisión» a 1280 × 720, y «Código 2FA» y su botón a 360 × 640), y «Notas» es más alto que la pantalla en tamaños pequeños. No lo causa este cambio: antes no se veía porque `Tab` se salía del diálogo.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 131 de 131. Riesgo: punto 3 (la lógica de foco de `ConfirmDialog` pasa a ser compartida); pendiente de verificación independiente.
- **L9 (2026-11-09).** Estrategia de entrega, elegida por el usuario: «Por tramos a main (Recomendado)». T2 superaba la previsión (unas 440 líneas en la rama, 30 de ellas datos de prueba movidos de archivo). La parte de T4 sobre los diálogos (`docs/flujo-usuario.md`) va con T2, junto al comportamiento que describe.
- **L10 (2026-11-09).** Verificación independiente de T2 (`eddd5f8` frente a `6f553e4`, en una copia limpia): sin bloqueos, y S3 cumple. `npm run e2e`, 131 de 131, y las E2E de `ConfirmDialog` no cambian. Comprobó además, con pruebas propias: la ficha abierta desde la comparación, la confirmación sobre dos diálogos, descartar la única fila de la última página (el foco va a la última fila de la página anterior), abrir con el enlace del nombre, un diálogo cuyo origen sigue en su sitio, la sesión con un error dentro y abrir y cerrar diálogos varias veces.
  - **Aviso corregido:** `Esc` mientras se guarda la ficha abría la confirmación de descartar cambios, que se quedaba sin ficha detrás. Ahora `Esc` no hace nada en la ficha mientras hay una petición en curso. Prueba: `ignores Escape while its save is in flight`, que fallaba. La «✕» tiene el mismo problema desde antes de este plan, y es más difícil de provocar: no se cambia aquí.
  - **Cambio de comportamiento en `ConfirmDialog`,** sin efecto visible con sus dos botones: `Tab` recorre todos los controles enfocables y el foco se devuelve tras `nextTick`.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 132 de 132; `python -m unittest discover -s tests`, OK; `ruff check .`, sin avisos.
  - **No probado:** un lector de pantalla real, ni un teclado virtual real. En un móvil, poner el foco en «Nombre» al abrir la ficha puede hacer aparecer el teclado virtual.
- **L11 (2026-11-09).** Revisión del tramo 1 hasta `5492194` (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Se aplican sus dos avisos, que no bloqueaban nada, cada uno con una prueba que fallaba:
  - **`R3-001`:** `Esc` en la sesión no hace nada mientras se abre un archivo, para que el resultado o el error tengan dónde mostrarse. Al guardar, la aplicación no marca `busy`, así que `Esc` sigue cerrando el diálogo y la descarga continúa, como ya pasaba con «✕»: no se pierde nada.
  - **`R3-002`:** mantener `Esc` pulsado solo actúa una vez. Antes, cada repetición de la tecla cerraba el siguiente diálogo.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 134 de 134; `python -m unittest discover -s tests`, OK; `ruff check .`, sin avisos.
- **L12 (2026-11-09).** Revisión de `bc52380` (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Su única sugerencia queda **pendiente**, sin corregir: una prueba en el repositorio para cuando se descarta desde la ficha la única fila de la última página y el foco va a la última fila de la página anterior (`neighbour()` en `dialogFocus.ts`). La verificación independiente lo comprobó (L10), pero ninguna prueba versionada lo cubre. Tramo 1 cerrado.
- **L13 (2026-11-09).** Tramo 1 integrado en `main` (`e1dd3f5`, `--no-ff`; el contenido es idéntico al de `2411d7e`), con `Tests` en verde en la rama y en `main`. T3 y lo que quedaba de T4:
  - **RED:** cinco pruebas nuevas en `frontend/e2e/navigation.spec.ts`, que fallaban: roles de pestaña y panel, flechas con activación automática y vuelta al principio, una sola parada de `Tab`, y `aria-current` en la navegación lateral y en la móvil.
  - **GREEN:** en `App.vue`, `role="tab"`, `aria-selected`, `aria-controls`, `tabindex` móvil y las flechas. Un único `tabpanel` (`credentials-panel`) envuelve los filtros y la tabla, porque los filtros son comunes a las dos pestañas. La pantalla activa lleva `aria-current="page"`.
  - **Selectores:** 61 selectores de las E2E pasan del rol `button` al rol `tab`, de forma mecánica. Ninguna aserción cambia.
  - **Sin cambio visual:** los estilos calculados de los 20 estados de `css-tokens` dan 0 diferencias frente a `main`, sin contar el contenedor nuevo.
  - **Documentación:** `docs/flujo-usuario.md`, en «Casos y límites relevantes».
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 139 de 139; `python -m unittest discover -s tests`, OK; `ruff check .`, sin avisos. Riesgo: ninguno de los puntos de la lista.
- **L14 (2026-11-09).** Revisión del tramo 2 hasta `a4b5c7d` (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Se aplican sus dos avisos:
  - **`R3-001`, regresión:** las flechas con un modificador quedaban capturadas, y `Alt+←` y `Alt+→` dejaban de ir atrás y adelante en el navegador. Ahora los modificadores se dejan al navegador. Prueba: `leaves arrow keys with a modifier to the browser`, que fallaba.
  - **`R3-002`:** la prueba de la parada única de `Tab` comprueba también que esa parada sigue a la pestaña seleccionada.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 140 de 140; `python -m unittest discover -s tests`, OK; `ruff check .`, sin avisos.
- **L15 (2026-11-09).** Revisión de `a127803` (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Su única sugerencia queda **pendiente**, sin corregir: que la prueba de las flechas con modificador compruebe también que el evento no se cancela (`defaultPrevented`) e incluya `ArrowLeft` y `Meta`. Tramo 2 cerrado.
- **L16 (2026-11-09).** Tramo 2 integrado en `main` (`2db587b`, `--no-ff`; el contenido es idéntico al de `e248de6`), con `Tests` en verde en la rama y en `main`. El usuario elige qué hallazgos de L6 y L8 se arreglan: «Foco tapado (Recomendado), Teclado móvil al abrir (Recomendado)». Se añaden S6, T5 y T6, en un tramo 3.
  - **RED:** cuatro pruebas de `Tab` en `navigation.spec.ts` (registros a 640 × 360 y 360 × 640; ficha a 1280 × 720 y 360 × 640) y una en `dialogs.spec.ts` (pantalla táctil), que fallaban.
  - **GREEN, T5:** `--header-height` y `--nav-height` pasan del contenedor `.shell` a la raíz del documento, y `html` usa `scroll-padding-block` con ellas, así que el navegador deja libre ese espacio al mover el foco. `.dialog-content` reserva 96 px para la barra de «Guardar».
  - **GREEN, T6:** la ficha elige el título como foco inicial cuando `(pointer: coarse)` se cumple. No se ha probado en un móvil real.
  - **Evidencia:** en la auditoría de L6, los controles tapados en las pantallas pasan de 146 a 0, y ninguna de las 36 combinaciones tiene controles tapados ni fuera de pantalla. Los estilos calculados de los 20 estados solo cambian en `scroll-padding-*`.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 145 de 145; `python -m unittest discover -s tests`, OK; `ruff check .`, sin avisos. Riesgo: ninguno de los puntos de la lista.
- **L17 (2026-11-09).** Revisión de `f3fd8f6` (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Se aplican sus dos avisos:
  - **`R3-001`:** las pruebas solo avanzaban con `Tab`, así que no demostraban la reserva bajo la cabecera fija. Nuevas pruebas con `Mayús+Tab`, a 640 × 360 y 360 × 640. Fallan si se quita la reserva superior.
  - **`R3-002`:** la comprobación mira también los bordes del control, no solo su centro. **Eso descubrió un fallo real:** el control quedaba pegado a la barra y su contorno de foco, debajo de ella. La reserva sube 8 px por cada lado.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 147 de 147; `python -m unittest discover -s tests`, OK; `ruff check .`, sin avisos. Auditoría de L6: 0 controles tapados, 0 fuera de pantalla y 0 paradas fuera de los diálogos en las 36 combinaciones.
- **L18 (2026-11-09).** Revisión de `d90fad5` (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Cierre del plan. Sus avisos no bloqueaban nada y quedan **pendientes**, sin corregir, igual que `R3-001` (L12) y la sugerencia de L15:
  - Ninguna prueba comprueba que el contorno de foco queda libre: la comprobación mira dentro del control, y el margen de 8 px no está fijado por ninguna aserción.
  - Las pruebas de `Tab` por la página solo usan tamaños con tarjetas. La tabla de escritorio la cubre la auditoría de L6, que no está en el repositorio.
  - Los 96 px reservados para la barra de «Guardar» son una estimación: no se derivan de su altura real, y se aplican también a los diálogos sin esa barra.
  - **Hallazgos no aprobados, en `docs/pendiente.md`:** H2 (objetivos táctiles de menos de 44 px), H3 (icono de papelera de 16 px) y H4 («Guardar» y «Cancelar» fuera de la vista al abrir en pantallas muy bajas).
  - **Sin probar:** con un lector de pantalla real y con un teclado virtual real.
