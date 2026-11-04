# Tablas nativas en lugar de PrimeVue (D1)

Objetivo: sustituir `DataTable` y `Column` de PrimeVue por tablas HTML nativas con Vue en `RecordsTable`, `GroupsTable` y `TrashView`. Deben conservar su comportamiento, ser accesibles desde el principio y permitir retirar PrimeVue (`primevue`, `@primeuix/themes` y su configuración).
Rama: `refactor/native-tables` desde `main`, después de integrar `css-tokens`, porque los estilos de la tabla usan sus variables. Entrega: `ask-on-risk`. La previsión es de ~550 líneas cambiadas sin contar `package-lock.json`, por encima de ~400, así que antes del commit que lo supere se pregunta la estrategia de encadenado. T4 (dependencias) va en un commit propio.
Comprobaciones por tarea: `npm run build` y `npm run e2e` en `frontend/`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: planificado, sin empezar.

## Specs

- **S1 — Decisión y alcance.** «Decisión D1: sustituir PrimeVue por una tabla propia y eliminar la dependencia.» «Eso sí, no construiría un componente de tabla genérico y complejo. Utilizaría una tabla HTML nativa con Vue, adaptada exclusivamente a las necesidades de Password Checker.»
  - Alcance: las tres tablas de escritorio (`.desktop-table`) de `RecordsTable.vue`, `GroupsTable.vue` y `TrashView.vue`. Las tarjetas móviles (`.mobile-cards`) ya son HTML propio y no cambian.
- **S2 — Comportamiento que se conserva.** «1. Conservar las funcionalidades existentes: ordenación, paginación, búsqueda, selección y acciones sobre registros, según corresponda.» Inventario en `main` (`27734ba`):
  - **Ordenación:**
    - Inicial por `name`, ascendente (`sortField="name"`, `:sortOrder="1"`).
    - Todas las columnas son ordenables salvo «Acciones».
    - Con `removableSort`, cada clic en una cabecera avanza: ascendente → descendente → sin orden.
    - Se ordena por el valor del campo: `review`, `type`, `source` y `kind` por su valor interno, no por la etiqueta; `count` como número.
    - El comparador exacto, la estabilidad y el orden «sin ordenar» se fijan con las pruebas de caracterización de T1, antes de sustituir nada.
  - **Paginación:** 30 filas por página (`PAGE_SIZE`). El paginador solo aparece con más de 30 filas y tiene controles de primera página, anterior, números de página, siguiente y última. T1 fija qué pasa con la página actual al filtrar, al ordenar y al vaciar la última página.
  - **Búsqueda y filtros:** viven en `App.vue`, fuera de la tabla, y no cambian.
  - **Selección:** hoy ninguna tabla permite seleccionar filas (no usan `selection` ni `selectionMode`), y no se añade.
  - **Acciones:** los mismos botones por fila con los mismos nombres accesibles («Editar», «Mover a la papelera», «Comparar», «Mover grupo a la papelera», «Restaurar»), deshabilitados igual que hoy mientras `busy`. Se mantienen las filas alternas (`stripedRows`).
  - La guía (§4) pide una tabla «con encabezado fijo»; hoy la cabecera de la tabla no es fija y esta rama no lo añade.
  - Si T1 descubre que un comportamiento actual es defectuoso (por ejemplo, una página vacía), se anota en el Log y se decide con el usuario. No se corrige ni se reproduce sin avisar.
- **S3 — Accesibilidad.** «2. Accesibilidad desde el principio: HTML semántico, `aria-sort`, navegación por teclado y gestión correcta del foco.»
  - `<table>` con nombre accesible, `<thead>`/`<tbody>` y `<th scope="col">`.
  - La ordenación se activa con un `<button>` dentro de la cabecera, operable con `Tab`, `Enter` y `Espacio`. Solo la columna ordenada lleva `aria-sort` (`ascending` o `descending`), según el patrón de tabla ordenable de WAI-ARIA APG.
  - El paginador es un `<nav>` con nombre accesible. Sus botones tienen nombres en español («Primera página», «Página anterior», «Página N», «Página siguiente», «Última página») y la página actual lleva `aria-current="page"`.
  - Foco: tras ordenar, sigue en el botón de la cabecera. Tras activar un control de paginación, nunca cae en `<body>`, tampoco cuando ese control queda deshabilitado al llegar al principio o al final.
  - **Supuesto, a confirmar al aprobar el plan:** si una acción quita del listado la fila que tiene el foco (mover a la papelera, restaurar), el foco pasa a la misma acción de la fila siguiente, o de la anterior si era la última, o al título de la sección si no quedan filas. Hoy el foco se pierde.
- **S4 — Reutilización.** «3. Reutilización: separar la lógica de ordenación y paginación de la representación visual, sin introducir abstracciones innecesarias.»
  - La lógica vive en un único módulo TypeScript sin plantilla, usado por las tres tablas: estado de orden, ciclo ascendente/descendente/sin orden, comparación, corte por páginas y ajuste de la página cuando cambian las filas.
  - De la presentación solo se comparten el botón de cabecera ordenable y el paginador. Cada tabla conserva su propio marcado de columnas. No se crea un componente `DataTable` genérico ni una configuración de columnas.
- **S5 — Sin regresiones.** «4. Sin regresiones: mantener los E2E existentes, añadir pruebas de teclado y comprobar la equivalencia visual y funcional.»
  - Los E2E existentes siguen pasando. Lo único que puede cambiar en ellos son los selectores de clases de PrimeVue (`.p-paginator` y `.p-paginator-next`, en `frontend/e2e/review.spec.ts:56-59`), que pasan a seleccionar por rol; las aserciones no cambian.
  - Pruebas de teclado nuevas para la ordenación, la paginación y las acciones de fila (S3).
  - Equivalencia funcional: las pruebas de caracterización de T1 pasan igual con PrimeVue y con la tabla nativa.
  - Equivalencia visual: capturas de `main` y de la rama en 1440 × 900, 1280 × 720 y 390 × 844, con los mismos datos ficticios. No pueden ser idénticas, porque los estilos de PrimeVue se sustituyen por otros propios; las diferencias se describen en el Log y el usuario las acepta. La página no debe desplazarse en horizontal y el cambio a tarjetas en pantallas pequeñas debe ocurrir en el mismo punto. El script vive fuera del repositorio y no se versiona.
- **S6 — Medición y retirada.** «5. Medir antes y después: comparar el tamaño del bundle y retirar completamente PrimeVue y sus estilos cuando ya no se utilicen.»
  - Antes (T1) y después (T4) se mide con `npm run build` cada archivo de `frontend/dist/assets`, sin comprimir y con gzip, y se anota si Vite avisa de algún chunk de más de 500 kB. Como referencia, sin haberla medido con este procedimiento: `index-*.js` de 751 401 bytes.
  - La retirada debe ser completa:
    - `primevue` y `@primeuix/themes` salen de `package.json` y de `package-lock.json`, junto con los paquetes que solo ellos traían;
    - no queda ningún import de `primevue` ni de `@primeuix`;
    - `main.ts` ya no llama a `app.use(PrimeVue…)`;
    - `style.css` no tiene selectores `.p-*` (hoy son tres: `.p-datatable-table`, `.desktop-table.p-datatable` y `.p-datatable-thead`/`.p-datatable-tbody`);
    - `index.html` pierde la clase `app-dark` si nada más la usa (hoy solo la lee el `darkModeSelector` de PrimeVue).
- **S7 — Flujo.** «Mantendría las tareas pequeñas e independientes y el flujo habitual de implementación, revisión y aceptación antes de integrar en `main`.» Nada se integra en `main` sin la aprobación del usuario.

## Tasks

- [ ] T1 — S2, S5, S6: línea base y caracterización sobre PrimeVue. Ruta: inline.
  - Medición del bundle y capturas de referencia.
  - E2E de caracterización en verde sobre `main`: orden inicial; ciclo de orden en una columna de texto y en `count`; comparación con mayúsculas, acentos y números («a2» frente a «a10»); paginador solo con más de 30 filas; cada control de paginación; página actual al filtrar, al ordenar y al vaciar la última página.
  - Los selectores de tabla y paginador se agrupan en un helper de E2E, para que en T2 solo cambie el helper.
  - Excepción a RED: estas pruebas fijan un comportamiento que ya existe; se documenta.
- [ ] T2 — S2-S5: módulo de lógica, cabecera ordenable, paginador y `RecordsTable` nativa, con su CSS basado en las variables de `css-tokens`. Ruta: inline.
  - RED primero en las pruebas nuevas de teclado y accesibilidad: `aria-sort` solo en la columna ordenada, nombres del paginador en español, foco tras ordenar y tras paginar, y el supuesto de S3.
  - La caracterización de T1 sigue en verde.
- [ ] T3 — S2-S5: `GroupsTable` y `TrashView` nativas, reutilizando lo de T2, con sus pruebas de teclado. Ruta: inline.
- [ ] T4 — S6: retirada de PrimeVue. Ruta: inline.
  - Cambios en `main.ts`, `package.json` y `package-lock.json` (con `npm uninstall`); se quitan los selectores `.p-*` y la clase `app-dark` si queda sin uso.
  - Medición posterior y comparación con T1 en el Log; capturas finales (S5).
  - Riesgo: punto 5 (dependencias). Commit propio y verificación independiente.
- [ ] T5 — Coherencia del plan de dependencias. Ruta: inline.
  - P12 ya está vinculada a esta fase (L5). Al integrar T4, se anota en P12 de `odd/tasks/dependency-hardening.md` que `primevue` y `@primeuix/themes` ya se retiraron, y en `docs/auditoria-dependencias.md`, que ya no son dependencias.
  - Depende de: T4. `docs/close-dependency-hardening`, que modificaba esos dos archivos, ya está integrada en `main` (L6).

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-03).** Decisión del usuario, literal:

  > Decisión D1: sustituir PrimeVue por una tabla propia y eliminar la dependencia.
  >
  > Estoy de acuerdo con la recomendación del informe. Si únicamente utilizamos `DataTable` y `Column`, mantener toda una biblioteca de componentes no parece justificado, especialmente cuando queremos mejorar la accesibilidad, incorporar temas y optimizar el frontend.
  >
  > Eso sí, no construiría un componente de tabla genérico y complejo. Utilizaría una tabla HTML nativa con Vue, adaptada exclusivamente a las necesidades de Password Checker.
  >
  > ### Condiciones para aprobar D1
  >
  > 1. Conservar las funcionalidades existentes: ordenación, paginación, búsqueda, selección y acciones sobre registros, según corresponda.
  > 2. Accesibilidad desde el principio: HTML semántico, `aria-sort`, navegación por teclado y gestión correcta del foco.
  > 3. Reutilización: separar la lógica de ordenación y paginación de la representación visual, sin introducir abstracciones innecesarias.
  > 4. Sin regresiones: mantener los E2E existentes, añadir pruebas de teclado y comprobar la equivalencia visual y funcional.
  > 5. Medir antes y después: comparar el tamaño del bundle y retirar completamente PrimeVue y sus estilos cuando ya no se utilicen.
  >
  > ### Sobre la planificación
  >
  > Mantendría las tareas pequeñas e independientes y el flujo habitual de implementación, revisión y aceptación antes de integrar en `main`.
  >
  > También pediría al agente que actualice el estado de la Fase 0 antes de generar el plan, porque el informe puede haber quedado desfasado respecto al endurecimiento de dependencias que ya hemos integrado.
  >
  > Con D1 resuelta, puede preparar las tareas de la Fase 1 en `odd/tasks/`, incluyendo dependencias, criterios de aceptación y pruebas, sin comenzar todavía la implementación.
  >
  > No hace falta resolver D2–D7 para planificar los bloques de la Fase 1 que no dependen de esas decisiones.

  Y: «No implementes nada.»
- **L3 (2026-11-03).** Estado de la Fase 0 (endurecimiento de dependencias, `odd/tasks/dependency-hardening.md`):
  - **En `main`:** `main` = `origin/main` = `27734ba`, comprobado con `git ls-remote`. Integra P2, P3, P3b, P4, P5 y P6 (hallazgos H1, H2, H4, H7 y H8).
  - **P8 (auditoría automática), sin integrar:** está en `ci/dependency-audit`, siete commits por delante de `main` (`bd5b726` … `2686219`). La revisión nativa aprobó el contenido hasta `28c138e`; `48a3b85`, `f47d708` y `2686219` llegaron después y no los cubre. La ejecución manual del workflow queda para después de integrar. `test/dependency-audit-negative` es una rama de pruebas negativas marcada «never merge».
  - **Pendientes:** P7 (alertas de Dependabot, un ajuste del repositorio) y P9, P10, P11 y P13 (prioridad baja).
  - **P12 tras D1:** dejan de aplicar `primevue` 5 y `@primeuix/themes` 3 (T5); con `frontend-bundle` T1, tampoco `vue-router` 5. Quedan `pinia` 4, `vite` 8 y `typescript` 7.
  - Conclusión: el endurecimiento integrado en `main` llega hasta H4; P8 todavía no está en `main`.
- **L4 (2026-11-03).** Análisis en `main`:
  - PrimeVue solo se usa en tres componentes (`DataTable` y `Column`) y en `main.ts` (`PrimeVue` y el tema `Aura`). Versiones: `primevue` 4.5.5, `@primevue/core` 4.5.5, `@primeuix/themes` 1.2.5, `@primeuix/styled` 0.7.4.
  - Los E2E dependen de PrimeVue solo por `.p-paginator` y `.p-paginator-next` (`review.spec.ts:56-59`); todo lo demás usa `.desktop-table`, `getByRole('row', …)` y `.desktop-table tbody tr`, que la tabla nativa debe conservar.
  - `ui-basics.md` (L2 y L3) documenta por qué `style.css` tiene selectores `.p-datatable…`: igualar el padding y ocultar la tabla en móvil.
  - Ruta: inline en todas las tareas. No aplica el disparador de escritor: las unidades se suceden y comparten archivos (`style.css`, el módulo de lógica y los E2E).
- **L5 (2026-11-04).** Fase 0 cerrada; actualiza L3:
  - P8 está integrada en `main` (`cf3f089`) y P7 está activada (`vulnerability-alerts` devuelve 204).
  - En la rama `docs/close-dependency-hardening`, sin integrar todavía, la otra sesión cerró la fase (L25 de `dependency-hardening.md`) y vinculó P12 a esta fase (L26): `primevue`, `@primeuix/themes` y `vue-router` se retiran en lugar de actualizarse. T5 queda reducida a anotar la retirada cuando ocurra.
  - Hoja de ruta completa en `docs/hoja-de-ruta.md`.
- **L6 (2026-11-04).** Petición: «Se ha actualizado la documentación en el otro worktree echa un vistazo y traete los cambios y soluciona los conflictos.» Se integra `origin/main` (`eb719fe`) en `docs/roadmap` sin conflictos de texto. Cambia el estado de L3 y L5:
  - `docs/close-dependency-hardening` está integrada (`883cab3`).
  - P9 (`httpx2`, `ea9dde3`) y P11 (Python 3.12 y 3.14, Node 24 en `frontend/.nvmrc`, `eb719fe`) están completadas.
  - Del plan de dependencias quedan las opcionales P10 y P13, y P12 vinculada a esta fase.
  - T5 ya no espera a otra rama, solo a T4.
