# Ficha móvil y acciones rápidas de revisión

Objetivo: mostrar la ficha a pantalla completa en el móvil con navegación entre pendientes, añadir las acciones «Marcar revisada» y «Acceso verificado», y el botón «Buscar en tienda» para registros Android.
Rama: `feat/mobile-record-detail` desde `main`. Fase 2. Depende de: `keyboard-accessibility` (foco en la ficha). Entrega: `ask-on-risk`, previsión ~350-400 líneas (L4). Solo frontend.
Comprobaciones: `npm run build` y `npm run e2e`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: planificado; orden aprobado (n.º 5 de 8, L4); supuestos pendientes, se preguntan al empezar.

## Specs

- **S1 — Ficha a pantalla completa.** `docs/pendiente.md`: «en móvil, detalle a pantalla completa con navegación «Anterior / Siguiente pendiente»».
  - Por debajo del ancho móvil actual, la ficha ocupa toda la pantalla.
  - «Anterior pendiente» y «Siguiente pendiente» recorren los registros pendientes en el orden y con los filtros de la lista visible.
  - Si hay cambios sin guardar, se pide confirmación antes de cambiar de registro, igual que al cerrar la ficha.
  - Guía (§8): «Móvil 360 px con teclado abierto | Guardar/cancelar siempre accesible».
- **S2 — Acciones rápidas.** `docs/pendiente.md`: «acciones «Marcar revisada» y «Acceso verificado» separadas».
  - Dos botones que guardan el estado «Revisada» o «Verificada».
  - **Supuesto:** solo están activos sin cambios pendientes, porque guardar a la vez una edición de URL, usuario, contraseña o código 2FA devuelve el registro a «Pendiente» (regla de `Workspace.change()`).
  - La «fecha local al confirmar manualmente» de esa misma línea del trabajo pendiente no entra aquí: hay que guardarla en la sesión y pertenece a la Fase 3, bloqueada por D8 y D3.
- **S3 — Android.** `docs/pendiente.md`: «en el teléfono, «Abrir aplicación (si existe mecanismo compatible)», «Buscar en tienda» y «Marcar verificada»».
  - «Buscar en tienda» abre la ficha de Google Play del paquete en una pestaña nueva, solo tras un clic, con `noopener noreferrer`.
  - «Marcar verificada» es la acción «Acceso verificado» de S2.
  - «Abrir aplicación» no se incluye, porque no existe un mecanismo compatible garantizado. Limitación conocida: «El identificador de paquete Android no garantiza un enlace para abrir la aplicación.»
  - **Supuesto:** «Buscar en tienda» aparece en todos los dispositivos cuando el registro es Android.

## Tasks

- [ ] T1 — S2: acciones rápidas. RED primero en E2E: estado guardado y botones desactivados con cambios pendientes. Ruta: inline.
- [ ] T2 — S1: ficha a pantalla completa y navegación entre pendientes. RED primero en E2E a 360 y 390 px, incluida la confirmación con cambios pendientes. Ruta: inline.
- [ ] T3 — S3: «Buscar en tienda». RED primero en E2E: la URL abierta y que no aparece en registros web. Ruta: inline.
- [ ] T4 — Documentación en `docs/flujo-usuario.md`, en la guía (§5) y en `docs/pendiente.md` (quitar lo hecho de «Ideas de diseño sin implementar»). Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`:
  - `EditorDialog.vue` es un diálogo centrado y elige el estado de revisión con un `select`.
  - `Workspace.change()` devuelve a pendiente cualquier edición de URL, usuario, contraseña o código 2FA.
  - `safeWebUrl()` solo abre URL `http(s)`.
  - No depende de ninguna decisión pendiente. Ruta: inline.
- **L4 (2026-11-10).** Revisión del plan contra `main` (`af881a5`), tras la Fase 1 y `review-filters`, a petición del usuario: «Planifica el resto de la fase2». Orden aprobado: «Pequeños primero (Recomendado)»; este plan es el n.º 5 de 8. Supuestos: «Justo antes de cada uno (Recomendado)», así que los supuestos y las decisiones pendientes se preguntan al empezar.
  - S1 pide que anterior y siguiente sigan «el orden y los filtros de la lista visible». Desde `review-filters`, ese orden vive dentro de cada tabla (`useTable` en `tableState.ts`, llamado desde `RecordsTable.vue`), y `App.vue` solo tiene la lista filtrada, sin ordenar. Hay que exponer el orden.
  - La ficha también se abre desde «Auditoría» y desde la comparación, que no tienen orden de lista. Decisión pendiente nueva: qué recorre «Siguiente pendiente» desde ahí.
  - El paquete para «Buscar en tienda» es el `host` de las URI `android://…@paquete/` y `androidapp://paquete` (`domain/urls.py`).
  - «Abrir sitio» abre ahora el origen y la ruta (D9); no afecta a este plan.
  - Previsión: sube a ~350-400 líneas por exponer el orden.
