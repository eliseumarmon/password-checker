# E2E con Playwright

Rama: `feat/e2e-playwright` (encadenada sobre `fix/ui-table-contrast-drawer`).

## Specs

- S1. `npm run e2e` compila el frontend, arranca `python app.py` en 127.0.0.1:8000 y ejecuta Chromium sin interfaz.
- S2. Solo CSV ficticios generados en memoria por los tests; nunca exportaciones reales.
- S3. Primer recorrido: importar, ver duplicados, contraste legible en la tabla, panel con acciones visibles, guardar, fusionar.

## Tareas

- [x] T1. Instalar `@playwright/test`, configuración y script `e2e`.
- [x] T2. Tests de importación, contraste, panel y fusión.
- [x] T3. Documentar en README.

## Registro

- L1. En Windows `webServer.command` corre en cmd: `/` se lee como opción; ruta con `path.join` y `cwd` en la raíz.
- L2. El backend solo acepta orígenes en los puertos 8000/5173: los E2E usan 8000 y necesitan el puerto libre.
- L3. RED verificado: con los estilos de main fallan contraste (1,66:1) y panel (Guardar fuera de pantalla); con el arreglo pasan 5/5.
