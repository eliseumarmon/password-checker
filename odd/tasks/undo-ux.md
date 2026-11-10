# Deshacer: atajo de teclado y aviso tras guardar

Objetivo: permitir el «Deshacer» de la aplicación con `Ctrl/Cmd+Z` y, al guardar una ficha, mostrar qué cambió con una opción de deshacer.
Rama: `feat/undo-ux` desde `main`. Fase 2. No depende de otros planes; toca `App.vue`, así que conviene hacerlo después de los bloques de la Fase 1 que también lo modifican. Entrega: `ask-on-risk`, previsión ~200 líneas. Solo frontend.
Comprobaciones: `npm run build` y `npm run e2e`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: planificado; orden aprobado (n.º 1 de 8, L4); supuestos pendientes, se preguntan al empezar.

## Specs

- **S1 — Atajo.** `docs/pendiente.md`: «atajo `Ctrl/Cmd+Z` para el «Deshacer» de la aplicación (hoy solo funciona el deshacer nativo dentro de los campos de texto)».
  - `Ctrl+Z` (o `Cmd+Z` en macOS) ejecuta el mismo «Deshacer» que el botón de la cabecera cuando: el foco no está en un campo editable, no hay ningún diálogo abierto, hay algo que deshacer (`can_undo`) y no hay otra operación en curso.
  - Dentro de un campo de texto, el deshacer nativo del navegador sigue funcionando igual.
- **S2 — Aviso tras guardar.** `docs/pendiente.md`, ficha: «aviso de edición con deshacer e indicación de qué cambió».
  - Al guardar una ficha con cambios, un aviso nombra los campos cambiados («Nombre», «URL», «Usuario», «Contraseña», «Código 2FA», «Notas», «Estado de revisión») y nunca sus valores.
  - Incluye un botón «Deshacer» que llama a `/api/undo`.
  - **Supuesto:** como el historial de deshacer es único para toda la aplicación, el botón del aviso se desactiva en cuanto ocurre otra operación que cambia datos; así nunca deshace algo distinto de lo que anuncia.
  - **Supuesto:** el aviso se cierra con «×» o al guardar otra ficha, igual que los avisos actuales.
- **S3 — Sin cambios en el backend.** Se usan `/api/undo` y `can_undo`, que ya existen.

## Tasks

- [ ] T1 — S1: atajo. RED primero en E2E: el atajo deshace fuera de los campos; dentro de un campo se mantiene el deshacer nativo; no hace nada con un diálogo abierto. Ruta: inline.
- [ ] T2 — S2: aviso tras guardar. RED primero en E2E: el aviso nombra los campos y no muestra valores; «Deshacer» restaura el registro; tras otra operación queda desactivado. Ruta: inline.
- [ ] T3 — Documentación en `docs/flujo-usuario.md` (atajo y aviso). Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`: `Workspace.undo()` recupera la última de hasta 30 instantáneas globales; el botón «↶ Deshacer» de `App.vue` llama a `api.undo` y se desactiva sin `can_undo`. No depende de ninguna decisión pendiente. Ruta: inline.
- **L4 (2026-11-10).** Revisión del plan contra `main` (`af881a5`), tras la Fase 1 y `review-filters`, a petición del usuario: «Planifica el resto de la fase2». Orden aprobado: «Pequeños primero (Recomendado)»; este plan es el n.º 1 de 8. Supuestos: «Justo antes de cada uno (Recomendado)», así que los supuestos y las decisiones pendientes se preguntan al empezar.
  - Desfasado: S2 dice «igual que los avisos actuales», pero hoy no hay ningún aviso de confirmación: `NoticeBase.vue:4` solo admite `kind: 'error' | 'warning'`. El aviso tras guardar necesita un tipo nuevo.
  - El atajo de S1 debe saber si hay un diálogo abierto, y la pila de diálogos es privada (`dialogFocus.ts:10`, `openDialogs`); las confirmaciones van aparte (`confirm.ts`, `pendingConfirm`).
  - Guardar sin cambios no crea paso de deshacer (`workspace.py:114-115`): en ese caso el aviso no debe ofrecer «Deshacer».
  - La pila de deshacer es global (hasta 30 instantáneas) y la vacían importar y abrir sesión. Desactivar «Deshacer» tras otra operación (supuesto de S2) se lleva en el frontend, porque el servidor solo da `can_undo`.
  - Decisión pendiente nueva: las acciones rápidas (papelera y restaurar desde la tabla, `App.vue:144-155`) también crean pasos de deshacer y no muestran aviso; ¿deben mostrarlo?
