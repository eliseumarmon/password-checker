# Comparación sin cierres y diálogo de confirmación propio

Que la comparación de duplicados siga abierta mientras se descarta o se revisa cada registro, y sustituir `window.confirm` por un diálogo propio con el estilo de la aplicación.
Una rama por tarea desde `main`; test primero (E2E con Playwright, `npm run e2e` y `npm run typecheck` en `frontend/`); solo credenciales ficticias; sin cambios de backend.

## Specs

- S1. Comparación abierta al descartar. Petición literal: «Cuando comparas, descartar una opción concreta cierra el modal y no se puede marcar el estado de la otra.»
  - Descartar un registro desde «Comparar registros» no cierra el modal.
  - El modal mantiene los registros que tenía al abrirse y muestra sus datos actualizados (nombre, usuario, URL, estado de revisión, papelera), aunque el grupo deje de existir porque solo quede un registro activo.
  - El registro descartado sigue visible con la etiqueta «En la papelera» y un botón «Restaurar»; los demás conservan «Ver / editar» y «Descartar».
  - Las marcas de coincidencia (URL, Usuario, Clave) se toman del grupo actual si sigue existiendo; si el grupo ya no existe, no se muestran (supuesto: evita mostrar coincidencias desactualizadas).
- S2. Volver a la comparación al guardar (propuesta aceptada al planificar). Guardar la ficha abierta con «Ver / editar» desde la comparación cierra solo la ficha y deja visible la comparación con los datos actualizados. Abierta desde otro lugar, la ficha se comporta como ahora.
- S3. Diálogo de confirmación propio. Petición literal: «He visto que hay confirm y prefiero un diálogo propio.»
  - Sustituye los seis `window.confirm`: importar con sesión cargada, descartar un grupo, fusionar copias exactas, exportar, abrir otra sesión con cambios en memoria (`App.vue`) y abrir una dirección local en Android (`EditorDialog.vue`).
  - Mantiene los textos actuales de cada aviso.
  - Botones «Cancelar» y uno de confirmación; el de las acciones que envían a la papelera usa el estilo `danger`. Supuesto: el botón de confirmación nombra la acción (por ejemplo «Importar», «Mover a la papelera», «Fusionar», «Generar CSV», «Abrir sesión», «Abrir de todas formas») en vez de un «Aceptar» genérico.
  - Se abre por encima de cualquier otro modal (comparación, ficha, sesión cifrada).
  - Accesible: `role="alertdialog"`, `aria-modal`, nombre y descripción accesibles; el foco empieza en «Cancelar» y vuelve al control que lo abrió al cerrar.
  - Esc y el clic fuera del diálogo cancelan. Cancelar no ejecuta la acción ni cambia el estado.
  - Sin dependencias nuevas; una única instancia en `App.vue` que se usa con una función que devuelve una promesa (`Promise<boolean>`), también desde `EditorDialog.vue`.

## Tasks

- [x] T1. S1, inline. E2E en rojo: en un grupo de dos registros, descartar uno deja abierta la comparación, ese registro aparece «En la papelera» con «Restaurar» y el otro se puede abrir y marcar como revisado. Implementación: guardar los ids de los miembros al abrir (`App.vue`) y obtener los datos de `recById` y las marcas del grupo actual; `quickEdit` deja de cerrar la comparación; `CompareDialog.vue` emite `restore`. Regresión: «Descartar» del grupo completo y «Fusionar copias exactas» siguen cerrando la comparación como hoy.
- [ ] T2. S2, inline. E2E en rojo: abrir «Ver / editar» desde la comparación, cambiar el estado de revisión y guardar → la ficha se cierra, la comparación sigue visible y muestra el estado nuevo. Regresión: guardar la ficha abierta desde «Todas» o Auditoría la cierra como hoy.
- [ ] T3. S3, inline. Componente `ConfirmDialog.vue` y función de confirmación con promesa; reemplazar los seis `window.confirm`; adaptar los E2E que hoy escuchan el evento `dialog` del navegador (`component-events.spec.ts`, `review.spec.ts`) para usar el diálogo propio. E2E: confirmar ejecuta la acción; «Cancelar», Esc y el clic fuera no la ejecutan; el foco empieza en «Cancelar»; abierto desde la comparación o la ficha, queda por encima. Comprobación: `grep -rn "window.confirm" frontend/src` sin resultados.
- [ ] T4. S1-S3, inline. Documentación: `docs/flujo-usuario.md` y `docs/guia-visual.md` (comparación que sigue abierta y diálogo de confirmación).

## Log

- L1 (2026-11-02). Petición original: «Cambios en gui que me parece que harán el uso más sencillo. Cuando comparas, descartar una opción concreta cierra el modal y no se puede marcar el estado de la otra. He visto que hay confirm y prefiero un diálogo propio.»
- L2 (2026-11-02). Análisis: `quickEdit` en `App.vue` pone `selectedGroup = null` tras cualquier edición, y descartar pasa por ahí; `save` hace lo mismo, por lo que guardar la ficha abierta desde la comparación también la cierra. Hay seis `window.confirm` (cinco en `App.vue` y uno en `EditorDialog.vue`). Al responder «Planifícalo desde una nueva rama» se aceptó la propuesta de S1-S3, incluido S2.
- L3. Previsión: unas 250 líneas en total (componente, cambios en `App.vue` y `CompareDialog.vue`, E2E y documentación), por debajo del umbral de 400; estrategia de entrega `ask-on-risk`, una rama por tarea.
- L4 (2026-11-02). T1 en `feat/t1-compare-stays-open` (encadenada sobre `docs/compare-confirm-dialog-tasks`). RED observado: el E2E «keeps the comparison open after discarding one record» fallaba porque la comparación se cerraba. GREEN: `App.vue` guarda los ids al abrir y localiza el grupo actual por pertenencia (su id es el del primer miembro activo y cambia al descartarlo); `quickEdit` ya no cierra la comparación. Sin grupo se muestra «Ya no quedan duplicados activos en este grupo.»; la nota pasa a decir «primer registro activo». Las regresiones de S1 (grupo completo y fusión) no son alcanzables con la comparación abierta y siguen cubiertas por sus E2E. `npm run typecheck` correcto; `npx playwright test`: 51 pasadas.
