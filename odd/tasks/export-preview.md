# Ventana de exportación con vista previa

Objetivo: sustituir la confirmación de exportación con recuentos por una ventana que muestre qué se incluye, qué se excluye, los conflictos pendientes y el destino, antes de generar el CSV.
Rama: `feat/export-preview` desde `main`. Fase 2. Depende de: `keyboard-accessibility` (gestión del foco en diálogos) y, para las listas largas, `native-tables`. Entrega: `ask-on-risk`, previsión ~250 líneas. Solo frontend.
Comprobaciones: `npm run build` y `npm run e2e`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: planificado; orden aprobado (n.º 4 de 8, L4); supuestos pendientes, se preguntan al empezar.

## Specs

- **S1 — Contenido.** `docs/pendiente.md`: «modal con resultados incluidos y excluidos, conflictos pendientes, destino y formato Bitwarden, en lugar de la confirmación actual con recuentos; resumen y vista previa antes de exportar». Limitación conocida: «No hay una vista previa detallada de la exportación.»
  - Resumen: credenciales incluidas, en la papelera (excluidas), grupos con contraseñas diferentes sin resolver y registros pendientes de revisión.
  - Vista previa: listas de incluidas y excluidas con nombre, URL y usuario. **Nunca** contraseñas ni códigos 2FA.
  - Destino y formato: «Bitwarden (csv)», con los avisos actuales (Bitwarden no elimina duplicados; el CSV lleva contraseñas y 2FA en texto plano).
  - Botones «Cancelar» y «Generar CSV». Cancelar no hace nada.
- **S2 — Sin cambios en el backend.** Todo se calcula con el estado que ya recibe el frontend; la descarga sigue usando `GET /api/export`.
- **S3 — Listas largas.** Con 500 o más credenciales (guía, §8), las listas usan la paginación de `native-tables`.

## Tasks

- [ ] T1 — S1, S2: ventana de exportación. Ruta: inline.
  - RED primero en E2E: los recuentos coinciden con el estado; ninguna contraseña ni código 2FA aparece en el DOM de la ventana; «Cancelar» no descarga nada; «Generar CSV» descarga el mismo archivo que hoy.
- [ ] T2 — S3: paginación de las listas. E2E con más de 30 filas. Ruta: inline.
- [ ] T3 — Documentación en `docs/flujo-usuario.md` (paso 7) y en la guía (§6, componente 9). Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`: `exportNow()` (`App.vue`) pide confirmación con `confirmAction` y un texto con recuentos; `records` y `groups` traen inclusión, revisión y tipo de grupo, sin contraseñas. No depende de ninguna decisión pendiente. Ruta: inline.
- **L4 (2026-11-10).** Revisión del plan contra `main` (`af881a5`), tras la Fase 1 y `review-filters`, a petición del usuario: «Planifica el resto de la fase2». Orden aprobado: «Pequeños primero (Recomendado)»; este plan es el n.º 4 de 8. Supuestos: «Justo antes de cada uno (Recomendado)», así que los supuestos y las decisiones pendientes se preguntan al empezar.
  - Las tablas de `native-tables` guardan su orden por una clave cerrada (`TableKey` en `tableState.ts`) y, desde `review-filters`, lo recuerdan en `localStorage` (`pc.tableSort.<tabla>`). Las listas de esta ventana necesitan claves nuevas, con su orden recordado, o ser listas sin orden recordado: decisión de diseño al empezar.
  - «Conflictos pendientes» cuenta hoy los grupos `conflict` (`App.vue:163`), aunque estén revisados: hay que definirlo.
  - El texto de «Ajustes» que dice «Confirma antes de descargar» (`SettingsView.vue:8`) también cambia.
