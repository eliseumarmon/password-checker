# Filtros y orden de la revisión

Objetivo: añadir el filtro por estado y el selector de orden junto a la búsqueda, ordenar «Todas» por riesgo y por URL, y conservar los filtros entre visitas.
Rama: `feat/review-filters` desde `main`. Fase 2. Depende de: `native-tables` (reutiliza su módulo de ordenación). Entrega: `single-pr`, una sola integración a `main` al final, con un commit por tarea (L12); previsión ~580 líneas. Solo frontend.
Comprobaciones: `npm run build` y `npm run e2e`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: en curso.

## Specs

- **S1 — Filtro por estado.** `docs/pendiente.md`: «filtro por estado y selector de orden junto a la búsqueda».
  - Un selector con «Todos los estados» (L13), «Pendiente», «Revisada», «Verificada» y «No funciona» (las etiquetas de `labelReview`), junto a la búsqueda y al filtro de tipo.
  - En «Duplicados», un grupo cumple el filtro si alguno de sus miembros tiene ese estado. Hoy «Solo pendientes» ya funciona así con `pending`.
  - **Confirmado (L7):** el selector sustituye la casilla «Solo pendientes»; elegir «Pendiente» equivale a marcarla.
- **S2 — Orden único.** `docs/pendiente.md`: «en «Todas», orden por riesgo y por URL, con los grupos de una misma URL contiguos».
  - **Confirmado (L6):** cada tabla tiene un solo orden, que se cambia desde dos sitios: el selector de orden junto a la búsqueda y las cabeceras de las columnas. El selector muestra siempre el orden actual, y pulsar una cabecera lo cambia también.
  - Las cabeceras siguen como hoy: cada pulsación pasa por ascendente, descendente y el orden de importación.
  - El selector ofrece el orden de importación, cada columna de la tabla activa en las dos direcciones y, en «Todas», también «Riesgo» y «URL». **Decisión de diseño:** un solo selector cuyas opciones nombran la dirección, para que un lector de pantalla lea el orden completo en un único control.
  - Las tarjetas del móvil siguen el mismo orden que la tabla. Hoy salen en el orden de importación (`RecordsTable.vue:46`, `GroupsTable.vue:47`, `TrashView.vue:44`). La papelera también tiene selector, encima de su tabla (**confirmado, L18**), y sus tarjetas también siguen el orden de su tabla.
  - Riesgo (**confirmado, L8**): cada registro suma una alerta por cada lista de «Auditoría» en la que aparece (reutilizada, poco segura, incompleta), según `audit` de la respuesta. Primero, más alertas; a igualdad, por nombre. Nunca se usa la contraseña en el navegador para calcularlo. No cuentan la URL `http` sin cifrar ni el usuario y la contraseña dentro de la URL (ver S5).
  - URL: por `host` y después por la URL completa, de modo que los registros de una misma URL quedan contiguos. En Android, `host` es el paquete (`backend/password_checker/domain/urls.py:38-46`). Las URL vacías van al final, como cualquier valor vacío.
- **S3 — Continuidad.** `docs/pendiente.md`: «continuidad de filtros».
  - **Confirmado (L9):** el tipo, el estado y el orden de cada tabla se recuerdan entre recargas en `localStorage`, con el mismo tratamiento de errores que la barra lateral contraída (`App.vue`): si el navegador no deja guardar, la aplicación funciona igual y no recuerda nada.
  - **Ampliado en L4:** también se recuerda la ordenación de columna de cada tabla, que `native-tables` (S8) ya conserva al cambiar de pantalla.
  - **Confirmado (L9):** el texto de búsqueda no se guarda, porque puede contener usuarios y la guía (`docs/guia-visual.md`, §7) pide: «No guardar credenciales en `localStorage`, `sessionStorage`, `IndexedDB` ni cachés del navegador».
- **S4 — Sin cambios en el backend.** Todo se calcula con el estado que ya recibe el frontend (`records`, `groups`, `audit`).
- **S5 — Alertas de URL, pendientes (L8).** Anotar en `docs/pendiente.md` que «Auditoría» debe mostrar la URL `http` sin cifrar y el usuario y la contraseña dentro de la URL (`http` y `embedded_auth` de cada registro), y que, cuando se muestren, entrarán en el riesgo. No se implementa en esta rama.

## Tasks

- [x] T1 — S1: filtro por estado. RED primero en E2E (cada estado en «Todas» y en «Duplicados»). Ruta: inline. RED: las 3 pruebas de `e2e/filters.spec.ts` fallan esperando el selector «Filtrar estado»; GREEN: 3 de 3, y la suite entera 150 de 150 (L13). Commit `9be6d70`; evaluación de revisión: riesgo medio, `under_budget`. Revisada como tramo propio antes de T2 (lente de fiabilidad): aprobada y confirmada (L15).
- [x] T2 — S2: orden único entre el selector y las cabeceras, con las columnas actuales, y tarjetas del móvil en el mismo orden. RED primero en E2E. Ruta: inline. RED y GREEN en L14. Commit `d479515`. Verificador independiente: S2 y S4 PASS, suite 160 de 160 en copia limpia (L16). Evaluación: riesgo alto (punto 3 elevado a mano), revisión debida.
- [ ] T2b — S2: selector de orden en la papelera, y el estado «sin orden» como constante compartida (L17, L18). RED primero en E2E. Ruta: inline. RED y GREEN en L19.
- [ ] T3 — S2: orden por riesgo y por URL en «Todas», reutilizando el comparador de `native-tables`. RED primero en E2E con datos ficticios de riesgo conocido. Ruta: inline.
- [ ] T4 — S3: continuidad. RED primero en E2E (recargar conserva tipo, estado y orden, pero no la búsqueda), con almacenamiento no disponible incluido. Riesgo: posible punto 2, por guardar datos en el navegador; commit propio. Ruta: inline.
- [ ] T5 — Documentación: `docs/flujo-usuario.md`, `docs/pendiente.md` (S5 y lo que esta rama resuelve) y `docs/hoja-de-ruta.md`. Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`: los filtros viven en `App.vue` (`filterType`, `query`, `pendingOnly`) y se aplican con `matches()`; `audit` ya trae los ids de reutilizadas, poco seguras e incompletas. No depende de ninguna decisión pendiente. Ruta: inline.
- **L4 (2026-11-04).** Anotaciones del usuario sobre una conversación externa, pegada en la sesión, para añadirlas a la hoja de ruta. S3 se amplía con la ordenación de columna de cada tabla. La conversación lo proponía así: «La continuidad después de recargar la página podría completarse en review-filters.md, que ya contempla guardar preferencias en localStorage.» T3 cubre también este caso.
- **L5 (2026-11-10).** Inicio aprobado: «Sí, estoy de acuerdo. Antes de empezar limpieza de ramas». Antes de crear la rama se borraron las ramas ya integradas en `main`, locales y remotas.
- **L6 (2026-11-10).** El plan es anterior a `native-tables`, que añadió cabeceras ordenables; con el selector del plan habría dos mandos para el mismo orden. Se propone un orden único por tabla, controlado desde el selector y desde las cabeceras. Respuesta: «Claro, orden único.» Hallazgo del análisis: las tarjetas del móvil no siguen ningún orden.
- **L7 (2026-11-10).** Sobre sustituir la casilla «Solo pendientes» por el selector: «Sí, el selector refleja mejor los estados reales».
- **L8 (2026-11-10).** Sobre el riesgo, el usuario pregunta: «cuando ves el registro desde fuera no se ve pero si entras si sí que se ve la url no?». Comprobado: la URL se ve en la ficha (`EditorDialog.vue:100`) y bajo el nombre en la tabla de escritorio (`RecordsTable.vue:35`), no en las tarjetas del móvil; lo que no se ve en ningún sitio es un aviso de `http` o de usuario y contraseña dentro de la URL. Propuesta: contar solo las tres alertas de «Auditoría» y anotar las dos de URL como pendientes. Respuesta: «De acuerdo». Origen de S5.
- **L9 (2026-11-10).** Sobre guardar tipo, estado y orden, pero no la búsqueda, y funcionar sin almacenamiento: «Si».
- **L10 (2026-11-10).** Análisis en `main` (`39805fd`): el orden vive en `tableState.ts` (`memory`, una entrada por tabla), y su valor inicial se pasa desde cada componente; para que el selector lo lea antes de montar la tabla, el orden inicial pasa a `tableState.ts`. `CredentialSummary` trae `host`. `e2e/review.spec.ts` usa la casilla «Solo pendientes» una vez. La sesión sobrevive a la recarga (`e2e/import-warnings.spec.ts`), así que recargar sí conserva los datos.
- **L11 (2026-11-10).** Previsión por tarea: T1 ~80, T2 ~200, T3 ~120, T4 ~140 y T5 ~40 líneas, unas 580 en total. Supera las 400, así que `ask-on-risk` pide elegir la estrategia de cadena antes del primer commit.
- **L12 (2026-11-10).** Estrategia de entrega: «Hazlo entero se pasa por poco el límite». Se entrega con `single-pr`: una sola integración a `main` al final, manteniendo un commit por tarea en la rama.
- **L13 (2026-11-10).** T1 hecho. La primera opción se llama «Todos los estados» en vez de «Todos», porque con el desplegable cerrado «Todos» no dice de qué. El grupo se muestra si algún miembro tiene el estado elegido; con «Pendiente» da lo mismo que la casilla, porque el servidor calcula `pending` con los mismos miembros (`review_state.py:73`). La casilla era la única de la aplicación: se quitan las reglas `.check` de `style.css`, que ya no usa nadie, y la comprobación de su tamaño en `e2e/review.spec.ts` («uses compact cards and rows»). Riesgo: ninguno.
- **L14 (2026-11-10).** T2. RED: 8 pruebas nuevas de `e2e/filters.spec.ts` fallan (no existe el selector «Ordenar»; las tarjetas del móvil salen en el orden de llegada). GREEN: 11 de 11 en el archivo, y la suite entera 158 de 158. Diseño:
  - `tableState.ts` guarda las columnas ordenables de cada tabla (`SORT_COLUMNS`), que leen las cabeceras y el selector, y el orden inicial, que antes pasaba cada componente. `setTableSort()` es la única forma de cambiar el orden, y vuelve a la página 1 venga de donde venga.
  - Las opciones dicen «(ascendente)» y «(descendente)» en vez de «A → Z», porque «Copias» es un número y «Origen» deja «Desconocido» al final.
  - La opción sin orden se llama «Orden de importación» en registros y papelera, y «Contraseñas diferentes primero» en grupos, porque el servidor manda los grupos ordenados así (`review_state.py:75-76`).
  - Capturas a 1440, 1280, 414, 390 y 320 px. A 320, «Ordenar» medía 268 px en un hueco de 260 y se salía del margen; a 390, repartir la fila a partes iguales cortaba «Todos los estados». En el móvil, los desplegables parten de su anchura natural (`flex:1 1 auto;min-width:0`): comparten fila solo si caben enteros (414 px) y si no ocupan la fila entera (390 y 320). El escritorio mide igual que antes.
  - Prueba de la barra de filtros a 320 y 390 px: ningún control se sale del panel. Sin la regla del móvil falla a 320 («Expected: <= 290, Received: 298»); con ella, 13 de 13 en el archivo.
  - Riesgo: punto 3, porque cambia `useTable`, que usan las tres tablas (orden inicial centralizado; las cabeceras ordenan a través de `setTableSort`). Lleva verificador independiente y revisión propia. Antes se cierra el tramo de T1 con su revisión.
- **L15 (2026-11-10).** Revisión de T1 (`9be6d70`, lente de fiabilidad), con consentimiento del usuario («Revisar este cambio»): aprobada y confirmada; el punto de partida de la siguiente revisión pasa a `9be6d70`. Dos observaciones informativas:
  - Aviso: podría quedar otra casilla con la clase `.check`. Comprobado: fuera de `style.css` no hay ninguna casilla ni la clase `check` en `frontend/src` ni en `index.html`. Sin efecto.
  - Sugerencia: el nuevo desplegable no tiene prueba de tamaño. Atendida en T2 con la prueba de la barra de filtros (L14).
  - La herramienta pidió decidir sobre `SortSelect.vue`, de T2 y aún sin seguimiento: quedó fuera con `--untracked-scope exclude` y el inventario que devolvió `status`.
- **L16 (2026-11-10).** Verificador independiente de T2 (`d479515` contra `9be6d70`, copias limpias con `git archive`): sin fallos ni regresiones.
  - `vue-tsc` y la compilación pasan, y la suite da 160 de 160: las 158 de L14 más las 2 pruebas de la barra de filtros añadidas después.
  - En escritorio, 59 estados de las tres tablas son idénticos antes y después: orden de filas, `aria-sort`, página, y orden conservado al cambiar de pantalla y de pestaña. En el móvil solo cambia el orden de las tarjetas, que es lo pedido.
  - Observaciones menores: el recuento de L14 estaba desfasado (corregido aquí), y su comprobación del orden en el móvil era débil para registros y papelera porque sus datos ya llegaban ordenados. Eso lo cubren las pruebas de `e2e/filters.spec.ts`, que importan Charlie, Alpha, Bravo.
  - El aviso de fin de turno propuso revisar la rama entera desde `39805fd`; no se lanzó, porque T1 ya estaba revisada y T2 se revisa sola desde `9be6d70`, después del verificador.
- **L17 (2026-11-10).** Revisión de T2 (`d479515`, lentes de legibilidad y fiabilidad), con consentimiento del usuario («Revisar este cambio»): aprobada y confirmada; el punto de partida de la siguiente revisión pasa a `d479515`. Observaciones informativas:
  - Aviso, de las dos lentes: la papelera no tiene selector, así que en el móvil su orden queda fijo (por nombre, o el último elegido en escritorio). Además, el comentario de `SortSelect.vue` dice que el selector es la única forma de ordenar en el móvil, y `UNSORTED_LABEL.trash` no lo lee nadie. Antes de T2 tampoco se podía ordenar, pero salía en el orden de importación.
  - Sugerencia: el estado «sin orden» (`{ field: null, direction: 'ascending' }`) está escrito en `SortSelect.vue` y en `nextSort`; mejor una constante compartida en `tableState.ts`.
- **L18 (2026-11-10).** Sobre el aviso de L17, se propone añadir el selector a la papelera, porque «el móvil puede ordenar con el selector» (L6) y la papelera era la única pantalla del móvil sin forma de ordenar. Respuesta: «Sí papelera también». Nueva tarea T2b, que incluye también la constante de la sugerencia.
- **L19 (2026-11-10).** T2b.
  - RED: la prueba del móvil de la papelera, ampliada para elegir el orden en su propio selector, falla esperando el selector «Ordenar».
  - GREEN: `TrashView.vue` muestra `SortSelect` en una barra `.filters` encima de la tabla, y `NO_SORT` (congelada) en `tableState.ts` es el estado «sin orden» que devuelven `nextSort` y el selector. `vue-tsc` pasa; `filters.spec.ts` y `tables.spec.ts` dan 45 de 45, y la suite entera 160 de 160.
  - Capturas a 1280, 390 y 320 px: en escritorio el selector va encima de la tabla con su anchura natural; en el móvil ocupa la fila, sin salirse a 320 px.
  - Riesgo: punto 3, porque `nextSort`, que usan todas las cabeceras, devuelve ahora la constante compartida.
