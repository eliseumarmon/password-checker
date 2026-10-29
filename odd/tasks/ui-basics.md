# Interfaz: básicos de uso

Ramas encadenadas, una por funcionalidad:
`fix/audit-review-in-place` → `feat/trash` → `feat/centered-editor-compact` → `feat/collapsible-sidebar`.

## Specs

- S1. «Revisar» en Auditoría abre la ficha sin salir de Auditoría.
- S2. Papelera = credenciales excluidas de exportación (reversible, sin cambios de backend). Cada fila tiene acción rápida de basura; la ficha tiene «Descartar» con icono de basura; la fusión de copias exactas también manda a la papelera. Sección Papelera con «Restaurar».
- S3. La ficha de edición se abre centrada; tarjetas y tabla más compactas; los checkbox mantienen su tamaño.
- S4. La barra lateral se contrae a iconos y recuerda el estado.

## Tareas

- [x] T1. S1 con test E2E.
- [x] T2. S2 con tests E2E.
- [ ] T3. S3 con tests E2E.
- [ ] T4. S4 con test E2E.

## Registro

- L1. Los E2E usan su propio backend en el puerto 5173: el 8000 puede tener una sesión real cargada.
