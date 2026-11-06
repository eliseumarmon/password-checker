# Tablas nativas en lugar de PrimeVue (D1)

Objetivo: sustituir `DataTable` y `Column` de PrimeVue por tablas HTML nativas con Vue en `RecordsTable`, `GroupsTable` y `TrashView`. Deben conservar su comportamiento, ser accesibles desde el principio y permitir retirar PrimeVue (`primevue`, `@primeuix/themes` y su configuración).
Rama: `refactor/native-tables` desde `main`, después de integrar `css-tokens`, porque los estilos de la tabla usan sus variables. Entrega: `ask-on-risk`. La previsión es de ~550 líneas cambiadas sin contar `package-lock.json`, por encima de ~400, así que antes del commit que lo supere se pregunta la estrategia de encadenado. T4 (dependencias) va en un commit propio.
Comprobaciones por tarea: `npm run build` y `npm run e2e` en `frontend/`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: en curso desde el 2026-11-06 (L9); tramo 1 (T1) integrado en `main` (`abf8c3a`); T2 (`23aead4`) y T3 hechas (L16-L17); tramo 2 pendiente de revisión e integración.

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
  - **Confirmado por el usuario (L13):** si una acción quita del listado la fila que tiene el foco (mover a la papelera, restaurar), el foco pasa a la misma acción de la fila siguiente, o de la anterior si era la última, o al título de la sección si no quedan filas. Hoy el foco se pierde.
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
- **S8 — La ordenación se conserva al cambiar de pantalla (L8).** Del usuario: «El orden que ya te lo he mencionado.»
  - Cada tabla conserva su columna y su dirección de ordenación al salir de su pantalla y volver. La paginación también se conserva mientras siga siendo válida.
  - Hoy se pierde porque `App.vue` cambia de pantalla con `v-if` y cada tabla se desmonta. El estado de orden tiene que vivir fuera del componente; por ejemplo, en el módulo de lógica de S4.
  - Conservarla también al recargar la página es `review-filters` (S3), en la Fase 2.

## Tasks

- [x] T1 — S2, S5, S6: línea base y caracterización sobre PrimeVue. Ruta: inline. Evidencia en L10-L15. Commits `79cd412`, `0f86c4f`, `267d79b` y el de L15. Tramo 1 (L14).
  - Medición del bundle y capturas de referencia.
  - E2E de caracterización en verde sobre `main`: orden inicial; ciclo de orden en una columna de texto y en `count`; comparación con mayúsculas, acentos y números («a2» frente a «a10»); paginador solo con más de 30 filas; cada control de paginación; página actual al filtrar, al ordenar y al vaciar la última página.
  - Los selectores de tabla y paginador se agrupan en un helper de E2E, para que en T2 solo cambie el helper.
  - Excepción a RED: estas pruebas fijan un comportamiento que ya existe; se documenta.
- [x] T2 — S2-S5: módulo de lógica, cabecera ordenable, paginador y `RecordsTable` nativa, con su CSS basado en las variables de `css-tokens`. Ruta: inline. Evidencia en L16.
  - RED primero en las pruebas nuevas de teclado y accesibilidad: `aria-sort` solo en la columna ordenada, nombres del paginador en español, foco tras ordenar y tras paginar, y el supuesto de S3.
  - La caracterización de T1 sigue en verde.
- [x] T3 — S2-S5: `GroupsTable` y `TrashView` nativas, reutilizando lo de T2, con sus pruebas de teclado. Ruta: inline. Evidencia en L17.
- [ ] T4 — S6: retirada de PrimeVue. Ruta: inline.
  - Cambios en `main.ts`, `package.json` y `package-lock.json` (con `npm uninstall`); se quitan los selectores `.p-*` y la clase `app-dark` si queda sin uso.
  - Medición posterior y comparación con T1 en el Log; capturas finales (S5).
  - Riesgo: punto 5 (dependencias). Commit propio y verificación independiente.
- [ ] T5 — Coherencia del plan de dependencias. Ruta: inline.
  - P12 es un paso propio de esta fase, [frontend-major-updates](frontend-major-updates.md) (L7). Al integrar T4, se anota en su Log (su T4) que `primevue` y `@primeuix/themes` ya se retiraron, y en `docs/auditoria-dependencias.md`, que ya no son dependencias.
  - Depende de: T4. `docs/close-dependency-hardening`, que modificaba esos dos archivos, ya está integrada en `main` (L6).
- [ ] T6 — S8: continuidad de la ordenación y la paginación al cambiar de pantalla, en las tres tablas. RED primero en E2E: ordenar, cambiar de pantalla y volver. Depende de: T3. Ruta: inline.

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
  - `odd/done/ui-basics.md` (L2 y L3) documenta por qué `style.css` tiene selectores `.p-datatable…`: igualar el padding y ocultar la tabla en móvil.
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
- **L7 (2026-11-04).** `dependency-hardening` pasa a `odd/done`, y P12 sale de él a un paso propio de esta fase, [frontend-major-updates](frontend-major-updates.md). T5 anota allí la retirada de PrimeVue. Encargo en `odd/done/roadmap-horizons.md`, L1.
- **L8 (2026-11-04).** Anotaciones del usuario sobre una conversación externa, pegada en la sesión, para añadirlas a la hoja de ruta. Se añaden S8 y T6: la ordenación de cada tabla se conserva al cambiar de pantalla. La conversación la situaba aquí («Fase 1 · native-tables»), y la continuidad tras recargar, en `review-filters`.
- **L9 (2026-11-06).** El usuario aprueba empezar: «Comprobar la accesibilidad sí me parece interesante. Lo dejamos anotado y seguimos con native-tables y pon css-tokens como hecho.» `css-tokens` está integrado en `main` (`3f6aea3`) y su plan está en `odd/done` (`8ea75e7`). Rama `refactor/native-tables` creada desde `8ea75e7`.
- **L10 (2026-11-06).** T1, línea base sobre PrimeVue 4.5.5.
  - **Caracterización:** `frontend/e2e/tables.spec.ts`, con 9 pruebas, en verde sin tocar el código de la aplicación. Excepción a RED: fijan un comportamiento que ya existe. Los selectores de tabla, cabecera y paginador están en `frontend/e2e/tables.ts`; `review.spec.ts` ya no usa clases `.p-*` directamente, así que en T2 solo cambia ese módulo.
  - **Comportamiento observado,** que coincide con el código de PrimeVue (`sortSingle`, `onColumnHeaderClick` y `sort` de `@primeuix/utils`):
    - El texto se compara con `Intl.Collator(undefined, { numeric: true })`: «a2» va antes que «a10», los acentos no separan («Álamo» antes que «alpha») y, entre mayúsculas y minúsculas, la minúscula va primero («beta» antes que «Beta»). Los números se comparan como números. Los valores nulos van siempre al final. La ordenación es estable.
    - Se ordena por el valor guardado: `unknown` va después de `firefox`, aunque su etiqueta, «Desconocido», iría antes.
    - La tercera pulsación deja las filas en el orden en que llegan, no en el orden inicial por nombre.
    - Ordenar vuelve a la página 1.
    - Si un filtro deja menos páginas que la actual, se muestra la última que queda. Si la página actual sigue existiendo, se queda en ella, también al quitar el filtro. Si la última página se vacía (por ejemplo, al mover su única fila a la papelera), se pasa a la anterior.
    - El paginador tiene «primera», «anterior», los números, «siguiente» y «última». En la página 1, «primera» y «anterior» están deshabilitados; en la última, «siguiente» y «última». Muestra como mucho cinco números, centrados en la página actual siempre que se pueda.
    - No se detectó ningún comportamiento defectuoso (S2).
  - **Bundle** (`npm run build`, gzip de nivel 9 con `zlib` de Node): `index-*.js`, 751 412 bytes (172 592 con gzip); `index-*.css`, 15 670 bytes (4006 con gzip). Vite avisa de un chunk de más de 500 kB.
  - **Capturas de referencia** fuera del repositorio, en 1440 × 900, 1280 × 720 y 390 × 844: Duplicados, Todas (con paginador), Todas ordenada por usuario y Papelera. En ninguna hay desplazamiento horizontal. La tabla de escritorio se ve en 1440 y 1280, y no en 390, donde se muestran las tarjetas. Detalles de PrimeVue que no se conservarán tal cual: el botón de la página actual usa el verde del tema Aura, y los iconos de orden son los de PrimeVue.
  - Comprobaciones: `npm run build` correcto; `npm run e2e`, 99 de 99.
- **L11 (2026-11-06).** Revisión de T1 (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Se aplican sus tres sugerencias, que no bloqueaban nada:
  - `tables.spec.ts` fija el idioma del navegador en `es-ES`, porque el orden del texto depende de él (`Intl.Collator` sin idioma explícito). Con él, las pruebas definen también lo que debe igualar el comparador nativo de T2.
  - El helper `seed` documenta que solo es seguro porque las E2E se ejecutan en serie contra un único backend.
  - Fechas de `css-tokens`: la integración fue el 2026-11-04 y el cierre del plan, el 2026-11-06. Se aclara en su L8 y en la hoja de ruta.
- **L12 (2026-11-06).** Segunda revisión de T1 (`review-reliability`, con el consentimiento del usuario), sobre el tramo hasta `0f86c4f`: aprobada y confirmada. Se aplican sus cuatro sugerencias, que no bloqueaban nada:
  - **Tercera pulsación en `Copias`:** ahora también se comprueba. Los grupos llegan ordenados por nombre, así que los datos se eligieron para que ese orden (3, 10, 2) no coincida ni con el ascendente ni con el descendente. Con los nombres anteriores, el orden de llegada coincidía con el descendente y la prueba no distinguía los dos casos.
  - **Valores vacíos:** PrimeVue considera vacío tanto el nulo como la cadena vacía (`isEmpty` de `@primeuix/utils`), y los deja al final en las dos direcciones. Ahora lo fija una prueba con un usuario vacío. Los nulos no llegan a la tabla, porque la API devuelve cadenas y números.
  - **Papelera:** una prueba fija su orden inicial y el ciclo de ordenación. Su paginación ya la cubría `review.spec.ts`.
  - **Evidencia tras fijar el idioma:** `npm run build` es correcto y `npm run e2e` pasa 101 de 101, con `tables.spec.ts` en 11 pruebas.
- **L13 (2026-11-06).** El usuario confirma el supuesto de foco de S3: «Sí, el funcionamiento del foco me parece concreto.» S3 pasa de supuesto a requisito.
- **L14 (2026-11-06).** Estrategia de entrega, elegida por el usuario: «Por tramos a main (Recomendado)». Cada tramo se integra en `main` cuando pasa la CI y el usuario lo aprueba:
  1. T1, solo pruebas, en `refactor/native-tables` (desde `79cd412` hasta el commit de L15).
  2. T2 y T3, las tablas nativas.
  3. T4 y T5, la retirada de PrimeVue (riesgo de dependencias, aparte).
  4. T6, el orden al cambiar de pantalla.
  Cada tramo siguiente parte de `main` con el anterior ya integrado.
- **L15 (2026-11-06).** Tercera revisión de T1 (`review-reliability`, con el consentimiento del usuario), sobre el tramo hasta `267d79b`: aprobada y confirmada. Su sugerencia, que no bloqueaba nada: fijar que la ordenación es estable. Se añade una prueba con dos filas empatadas. En el descendente conservan su orden de llegada, así que un orden nativo que invirtiera el ascendente fallaría.
  - Comprobaciones: `npm run build` correcto. La primera ejecución completa de `npm run e2e` dio 100 de 102, con dos fallos ajenos a este cambio: un servidor aislado que no llegó a arrancar y un cierre del editor. Duró 5,2 minutos en lugar de unos 2, así que parece lentitud de la máquina. Las dos pasaron al repetirlas, y una segunda ejecución completa pasó 102 de 102 (3,0 minutos). `tables.spec.ts` tiene 12 pruebas.
- **L16 (2026-11-06).** Tramo 1 integrado en `main` (`abf8c3a`, `--no-ff`; el contenido es idéntico al de `5f14d22`), con la CI en verde en la rama y en `main`. La rama sigue desde `abf8c3a` para el tramo 2. T2:
  - **RED:** cinco pruebas nuevas en `tables.spec.ts` (`accessible records table`): `aria-sort` solo en la columna ordenada; ordenar con `Enter` y `Espacio` sin perder el foco; el paginador como `<nav>` «Paginación», con sus botones en español y `aria-current="page"`; el foco se queda en el paginador cuando el control usado queda deshabilitado; y el foco tras mover una fila a la papelera, según S3 (L13). Las cinco fallaban con PrimeVue.
  - **GREEN:**
    - `src/tableState.ts`: comparación, orden estable, ciclo de orden, ventana de cinco páginas, el composable `useTable` y `useRemovalFocus`.
    - `SortHeader.vue` y `TablePaginator.vue`.
    - `RecordsTable.vue` con tabla nativa, dentro de un `div.desktop-table`, como antes.
    - `style.css`: estilos de la tabla nativa con las variables de `css-tokens`. El relleno general de las celdas pasa de 7 px a 6 px, el que ya imponía PrimeVue.
  - **Selectores de las pruebas:** `e2e/tables.ts` acepta durante T2 la tabla nativa y la de PrimeVue, porque `GroupsTable` y `TrashView` siguen con PrimeVue. T3 quita la parte de PrimeVue.
  - ~~**Diferencia con PrimeVue:** al quitar un filtro que dejaba 30 filas o menos, la tabla nativa se quedaba en la página 1.~~ Corregida en L20: ahora vuelve a la página anterior, como PrimeVue.
  - **Filas alternas (S2):** con PrimeVue no se veían, porque `style.css` fija el fondo de todas las celdas. La tabla nativa conserva ese aspecto y tampoco las muestra.
  - **Capturas** frente a la línea base: la misma disposición, sin desplazamiento horizontal y con la tabla oculta en 390 px. Cambian los iconos de orden (flechas de texto) y el paginador: botones con borde, y la página actual con fondo `--surface-selected` y borde `--accent`, en lugar del verde de Aura.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 107 de 107.
- **L17 (2026-11-06).** T3:
  - **RED:** dos pruebas nuevas en `tables.spec.ts` (`accessible groups and trash tables`), que fallaban con PrimeVue:
    - ordenar los grupos por `Copias` con el teclado, y que el foco pase al grupo vecino tras moverlo a la papelera, confirmando el diálogo;
    - restaurar con el teclado, con el foco en la fila vecina y, al vaciarse la papelera, en su título.
  - **GREEN:** `GroupsTable.vue` y `TrashView.vue` con tabla nativa, que reutilizan `useTable`, `useRemovalFocus`, `SortHeader` y `TablePaginator`. Las tablas se llaman «Grupos de duplicados» y «Credenciales descartadas». `e2e/tables.ts` ya solo selecciona por rol y nombre: no queda ninguna clase `.p-*` en las E2E.
  - **PrimeVue** solo queda en `main.ts`, `package.json` y los selectores `.p-*` de `style.css`; se retira en T4 (tramo 3).
  - **Capturas** de las tres tablas en 1440 × 900, 1280 × 720 y 390 × 844: la misma disposición, sin desplazamiento horizontal y con las tarjetas en 390 px. Las únicas diferencias son las de L16: iconos de orden y paginador.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 109 de 109.
- **L18 (2026-11-06).** La revisión del tramo 2 (`review-reliability`, con el consentimiento del usuario) pidió una corrección. Hallazgo `R3-stale-removal-focus`, crítico: `useRemovalFocus` recordaba la fila antes de confirmar la acción y no lo olvidaba si se cancelaba o fallaba. Un filtro posterior que ocultara la fila se tomaba por la eliminación y movía el foco fuera del buscador.
  - RED: prueba `leaves focus alone when a cancelled removal is followed by a filter that hides the row` (cancelar la confirmación de un grupo y escribir en el buscador). Fallaba.
  - GREEN: el foco solo se mueve si la eliminación lo dejó en `<body>`, tras actualizar el DOM, y la página tampoco cambia en otro caso.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 110 de 110.
- **L19 (2026-11-06).** La validación de la corrección de L18 la aprobó, y la revisión del tramo 2 queda aprobada y confirmada. Avisos que no bloqueaban nada:
  - **`R3-table-overflow`:** la tabla nativa no tenía contenedor con desplazamiento. Prueba nueva `scrolls a wide table inside itself instead of widening the page`, con 900 px de ancho y un usuario de 125 caracteres. Pasa con PrimeVue en `main` (`abf8c3a`, ejecutada con el código de `main` en el directorio de trabajo) y fallaba con la tabla nativa: la página se ensanchaba 656 px. Corregido con `overflow-x:auto` en `.desktop-table`.
  - **`R3-sort-persists-empty`:** en `GroupsTable` y `TrashView`, el orden elegido se conserva cuando la lista queda vacía y vuelve a tener filas, porque `useTable` vive en el componente y no en la tabla, que se desmonta. Con PrimeVue volvía al orden inicial. Es **intencionado**: es inofensivo y va en la dirección de S8 (T6).
  - Comprobaciones: `npm run e2e`, 111 de 111.
- **L20 (2026-11-06).** Revisión de `7e382dc` (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Se aplican sus cuatro avisos, que no bloqueaban nada. Dos eran regresiones frente a PrimeVue: sus pruebas pasan con el código de `main` (`abf8c3a`) y fallaban con la tabla nativa.
  - **Cabecera:** pulsar cualquier punto de la celda ordena, como con PrimeVue. El botón ocupa toda la celda (`th.sortable` sin relleno) y su contorno de foco queda dentro (`outline-offset:-3px`), para que el desplazamiento horizontal del contenedor no lo recorte. Prueba: `sorts when any part of the header cell is clicked`.
  - **Página tras un filtro:** `useTable` guarda la página pedida aparte de la mostrada y solo la ajusta mientras el paginador está visible. Así, al quitar un filtro que había ocultado el paginador, vuelve la página anterior. Prueba: `returns to the earlier page when a filter that hid the paginator is cleared`.
  - **Eliminación recordada:** las tablas reciben la acción como una prop que devuelve una promesa (`onTrash`, `onRestore`), en lugar de un evento. `useRemovalFocus.run` solo recuerda la fila mientras la acción está en curso, así que una acción cancelada o fallida se olvida al terminar. La comprobación del foco en `<body>` de L18 se mantiene. `App.vue` no cambia: `@trash` y `@restore` se asignan a esas props.
  - **Foco con varias páginas:** prueba `moves focus to the previous row when moving the only row of the last page to the trash` (31 filas). Ya pasaba.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 114 de 114.
- **L21 (2026-11-06).** Revisión de `bb6d4eb` (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Se aplican sus dos avisos, que no bloqueaban nada:
  - **`R3-removal-clobbers-remembered-page`:** al mover el foco tras eliminar una fila, `useRemovalFocus` solo cambia de página si hay paginador. Sin paginador, todas las filas están en pantalla, y cambiar la página borraba la que se había pedido. Prueba: `keeps the earlier page when a row is removed while a filter hides the paginator`. Fallaba.
  - **`R3-header-click-area-not-full-height`:** si la fila de cabecera es más alta que el botón, pulsar en el resto de la celda también ordena (`@click.self` en el `th`). El teclado sigue usando el botón. Prueba: `sorts when a taller header cell is clicked outside its button`. Fallaba.
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 116 de 116.
- **L22 (2026-11-06).** Revisión de `9af61c2` (`review-reliability`, con el consentimiento del usuario): aprobada y confirmada. Avisos, que no bloqueaban nada:
  - **`R3-pending-dropped-by-unrelated-update`:** la vigilancia de las filas olvidaba la eliminación pendiente con cualquier cambio de la lista, aunque la fila siguiera allí, por ejemplo al reordenar mientras la acción estaba en curso. Ahora solo la olvida cuando la fila desaparece; si la acción termina sin quitarla, la olvida `run`. No tiene prueba propia, porque hace falta una actualización intermedia durante la petición. Las pruebas de foco existentes siguen pasando.
  - **`R3-page-survives-empty-groups`:** en `GroupsTable` y `TrashView`, la página pedida también se conserva cuando la lista queda vacía y vuelve. Es **intencionado**, por la misma razón que el orden (L19).
  - Comprobaciones: `npm run typecheck` correcto; `npm run e2e`, 116 de 116.
