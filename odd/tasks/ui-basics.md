# Interfaz: básicos de uso

Ramas encadenadas, una por funcionalidad:
`fix/audit-review-in-place` → `feat/trash` → `feat/centered-editor-compact` → `feat/collapsible-sidebar` → `fix/mobile-single-view` → `feat/row-actions-trash` → `feat/sticky-header` → `feat/centered-compare` → `feat/sticky-stats-sidebar`.

## Specs

- S1. «Revisar» en Auditoría abre la ficha sin salir de Auditoría.
- S2. Papelera = credenciales excluidas de exportación (reversible, sin cambios de backend). Cada fila tiene acción rápida de basura; la ficha tiene «Descartar» con icono de basura; la fusión de copias exactas también manda a la papelera. Sección Papelera con «Restaurar».
- S3. La ficha de edición se abre centrada; tarjetas y tabla más compactas; los checkbox mantienen su tamaño.
- S4. La barra lateral se contrae a iconos y recuerda el estado.

## Tareas

- [x] T1. S1 con test E2E.
- [x] T2. S2 con tests E2E.
- [x] T3. S3 con tests E2E.
- [x] T4. S4 con test E2E (el propio logo contrae y expande).
- [x] T5. En pantallas estrechas solo tarjetas, sin tabla.
- [x] T6. Columna «Acciones» con Comparar + basura de grupo completo.
- [x] T7. Cabecera fija con título y acciones.
- [x] T8. Comparación centrada con registros lado a lado; la ficha se abre encima.
- [x] T9. Estadísticas fijas bajo la cabecera (fila compacta en móvil) y barra lateral fija a la altura de la ventana.

## Registro

- L1. Los E2E usan su propio backend en el puerto 5173: el 8000 puede tener una sesión real cargada.
- L2. PrimeVue fija el padding de celdas con más especificidad (`.p-datatable-tbody>tr>td`); los ajustes compactos de tabla deben igualarla.
- L3. PrimeVue inyecta `.p-datatable{display:block}` en tiempo de ejecución; ocultar la tabla exige `.desktop-table.p-datatable`.
