# Dividir App.vue

Rama: `refactor/split-app-vue` (desde `main`; no toca el backend).

## Specs

- S1. `App.vue` es el contenedor: estado, llamadas a la API y confirmaciones. Las pantallas y diálogos son componentes de presentación con props y eventos.
- S2. Sin repeticiones: etiquetas (revisión, tipo de grupo, Web/Android) y la lista de pantallas viven en un solo sitio; la barra lateral y la de móvil salen de la misma lista; las tres listas de auditoría usan un componente.
- S3. Mismo DOM y clases: los estilos globales y los E2E no cambian.

## Tareas

- [x] T1. `labels.ts` con etiquetas y pantallas; barra lateral y móvil desde la misma lista.
- [x] T2. E2E de guardar y abrir sesión cifrada (red de seguridad); diálogos de comparar, editar y sesión como componentes.
- [ ] T3. Pantallas (grupos, todas, auditoría, papelera, ajustes) como componentes; un solo selector de archivos.

## Registro

- L1. La tarjeta móvil de «Todas» mostraba el tipo en minúsculas (`web`); ahora usa la misma etiqueta que la tabla (`Web`).
- L2. Playwright guarda las descargas sin extensión; el E2E de sesión vuelve a subir el archivo con su nombre sugerido (`.pwc`), que el backend exige.
- L3. Las contraseñas de sesión viven solo en `SessionDialog` y desaparecen al cerrarlo; se eliminó la variable `note` sin uso.
