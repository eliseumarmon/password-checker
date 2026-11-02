# Ficha sin pérdida de cambios

Que la ficha de edición no descarte en silencio los cambios sin guardar.
Depende del diálogo de confirmación propio (`compare-confirm-dialog`, T3): las ramas de implementación se encadenan tras `feat/t3-confirm-dialog`, o salen de `main` cuando ese trabajo esté integrado. Una rama por tarea; test primero (E2E con Playwright, `npm run e2e` y `npm run typecheck` en `frontend/`); solo credenciales ficticias; sin cambios de backend.

## Specs

- S1. Aviso de cambios sin guardar. Petición literal: «me interesa lo de la pérdida de cambios sin avisar».
  - Hay cambios sin guardar cuando algún campo del formulario (nombre, URL, usuario, contraseña, notas, estado de revisión) difiere del registro cargado. Si se vuelve al valor original, deja de haber cambios.
  - Con cambios, cerrar la ficha con «✕», «Cancelar» o un clic fuera pide confirmación con el diálogo propio. Supuesto de texto: «Hay cambios sin guardar en esta credencial. Si cierras la ficha, se perderán. ¿Continuar?», con el botón «Descartar cambios» en estilo `danger`.
  - Con cambios, «Descartar» (a la papelera) y «Restaurar» desde la ficha también piden confirmación antes de aplicar la acción, que se hace sin guardar los cambios. Supuesto de texto: «Hay cambios sin guardar en esta credencial. Si continúas, se perderán. ¿Continuar?», con el botón de la acción («Mover a la papelera» o «Restaurar»).
  - Cancelar el aviso deja la ficha abierta con los cambios intactos.
  - Sin cambios, todo se comporta como ahora, sin aviso.
- S2. El fondo solo cierra con un clic que empieza y termina en él. Seleccionar texto en un campo y soltar el ratón fuera de la ficha no la cierra ni pide confirmación.

## Tasks

- [x] T1. S2, inline. E2E en rojo: pulsar en «Notas», arrastrar y soltar sobre el fondo deja la ficha abierta con lo escrito. Regresión: un clic normal en el fondo sigue cerrando la ficha sin cambios.
- [ ] T2. S1 (cierre), inline. E2E en rojo: con un cambio, «✕», «Cancelar» y el clic fuera piden confirmación; cancelar conserva los cambios; confirmar cierra la ficha y el registro no cambia en el servidor; volver al valor original cierra sin aviso. Regresión: sin cambios cierra sin aviso; «Guardar cambios» no pide confirmación.
- [ ] T3. S1 («Descartar» y «Restaurar»), inline. E2E en rojo: con un cambio, «Descartar» pide confirmación; cancelar no mueve el registro y conserva los cambios; confirmar lo mueve a la papelera sin guardar los cambios. Lo mismo con «Restaurar» desde una ficha de la papelera. Regresión: sin cambios actúan sin aviso.
- [ ] T4. S1-S2, inline. Documentación: `docs/flujo-usuario.md` y `docs/guia-visual.md`.

## Fuera de alcance

Cerrar diálogos con Esc (decidido: no se añade). Proteger la sesión cifrada de cierres por arrastre: perder la contraseña escrita al cerrarla es intencionado.

## Log

- L1 (2026-11-02). Petición original: «No añadas lo de ESC, pero me interesa lo de la pérdida de cambios sin avisar. Cúando puede pasar eso?», tras el análisis de cuándo la ficha descarta cambios; al proponerlo como tarea nueva: «Sí.»
- L2 (2026-11-02). Análisis: `EditorDialog.vue` edita una copia local (`form`) y solo la envía con «Guardar cambios». Se pierde sin aviso al cerrar con «✕», «Cancelar» o clic fuera (`@click.self` en el fondo); al soltar fuera de la ficha una selección empezada en un campo, porque el navegador envía el clic al ancestro común, que es el fondo (deducido, pendiente de reproducir en T1); y con «Descartar» o «Restaurar», que actúan sobre los datos guardados y cierran la ficha. Cambiar de pantalla, importar o abrir sesión también la cierran, pero no son alcanzables con la ficha abierta porque el fondo tapa la navegación.
- L3. Previsión: unas 150 líneas (lógica de cambios en `EditorDialog.vue`, cierre del fondo, E2E y documentación), por debajo del umbral de 400; estrategia de entrega `ask-on-risk`, una rama por tarea.
- L4 (2026-11-02). Petición: «Integra todo en main y entonces empieza el trabajo en una nueva rama limpia». `compare-confirm-dialog` y este plan integrados en `main` con un merge por rama; `main` verificado: 64 tests de backend, typecheck y 58 E2E. T1 en `feat/t1-editor-backdrop-drag` desde `main`. RED: «keeps the editor open when a text selection ends outside it» cerraba la ficha (el caso deducido en L2 queda reproducido). GREEN: `EditorDialog.vue` solo cierra si el `pointerdown` y el clic son sobre el fondo. Regresión: «closes the editor with a click on the backdrop» (nuevo, en verde antes y después). `npm run typecheck` correcto; `npx playwright test`: 60 pasadas.
