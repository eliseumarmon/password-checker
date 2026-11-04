# Tamaño del bundle del frontend

Objetivo: retirar la dependencia que no se usa (`vue-router`) y, después de `native-tables`, analizar si sigue el aviso de Vite por un chunk de más de 500 kB. Solo si sigue, se valora dividir el código.
Ramas:
- T1 en `chore/remove-vue-router` desde `main`. No depende de otros bloques y puede ir en cualquier momento.
- T2 y T3 en `perf/frontend-bundle` desde `main`, después de integrar `native-tables` (y `keyboard-accessibility` si T3 llega a cargar diálogos bajo demanda).

Entrega: `ask-on-risk`, previsión ~10 líneas en T1 (sin contar `package-lock.json`) y ~60 en T3 si se necesita. Comprobaciones por tarea: `npm run build` y `npm run e2e` en `frontend/`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: planificado, sin empezar.

## Specs

- **S1 — Origen.** `docs/pendiente.md`, «Trabajo pendiente»: «Optimización del bundle frontend: analizar el aviso de Vite por un chunk superior a 500 kB; valorar división de código y carga diferida sin ocultar el aviso aumentando únicamente el umbral.» Aceptación transversal: no se añade `build.chunkSizeWarningLimit` (hoy no existe en `vite.config.ts`) ni otra opción que solo silencie el aviso.
- **S2 — Dependencia sin uso.** `vue-router` (4.6.4) no tiene ningún import en `frontend/src` y se retira de `package.json` y `package-lock.json`. Viene del bloque de bundle de la Fase 1, autorizado en L2. Aceptación: `npm ls vue-router` no lo muestra; `npm run build` y `npm run e2e` siguen en verde.
- **S3 — Análisis tras `native-tables`.** Se mide con el mismo procedimiento que `native-tables` (S6): tamaño sin comprimir y con gzip de cada archivo de `frontend/dist/assets`, y si Vite avisa.
  - Si ningún chunk pasa de 500 kB y Vite no avisa, el bloque se cierra con esa evidencia y sin dividir el código.
  - Si el aviso sigue, se presentan al usuario las opciones de división con sus tamaños medidos, y el usuario decide antes de implementar (T3).
- **S4 — Carga diferida, solo si S3 la justifica y el usuario la aprueba.**
  - Candidatos: lo que no se ve al arrancar (diálogos de comparación, ficha y sesión; pantallas de Auditoría, Papelera y Ajustes), con `defineAsyncComponent`.
  - Aceptación: ningún chunk pasa de 500 kB; todos los recursos se siguen sirviendo desde el propio origen, sin cambiar la CSP (`script-src 'self'`); las E2E pasan, incluidas las de foco de `keyboard-accessibility`, porque un diálogo que se carga bajo demanda no debe perder el foco inicial.
- **S5 — Coherencia del plan de dependencias.** En `odd/tasks/dependency-hardening.md`, P12 deja de incluir `vue-router` 5.

## Tasks

- [ ] T1 — S2: retirar `vue-router` con `npm uninstall`. Ruta: inline.
  - Excepción a RED: no hay comportamiento que probar, porque la dependencia no se usa. La comprobación es el build y las E2E en verde.
  - Riesgo: punto 5 (dependencias). Commit propio y verificación independiente.
- [ ] T2 — S1, S3: medición tras `native-tables` y decisión, registradas en el Log. Ruta: inline. Sin código si no hay aviso.
- [ ] T3 — S4: carga diferida, solo si T2 la justifica y el usuario la aprueba. Ruta: inline.
- [ ] T4 — S5: P12 ya prevé retirar `vue-router` (L26 de `dependency-hardening.md`, en `docs/close-dependency-hardening`); al integrar T1, se anota que se retiró. Si coincide en el tiempo, se hace junto con `native-tables` T5. Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-03).** Decisión D1 y encargo de la Fase 1. Texto completo en `odd/tasks/native-tables.md`, L2. Fragmentos que afectan a este bloque: «mantener toda una biblioteca de componentes no parece justificado, especialmente cuando queremos mejorar la accesibilidad, incorporar temas y optimizar el frontend.» «5. Medir antes y después: comparar el tamaño del bundle y retirar completamente PrimeVue y sus estilos cuando ya no se utilicen.» «Mantendría las tareas pequeñas e independientes y el flujo habitual de implementación, revisión y aceptación antes de integrar en `main`.» «Con D1 resuelta, puede preparar las tareas de la Fase 1 en `odd/tasks/`, incluyendo dependencias, criterios de aceptación y pruebas, sin comenzar todavía la implementación.» Y: «No implementes nada.»
- **L3 (2026-11-03).** Análisis en `main` (`27734ba`):
  - Un `frontend/dist` compilado hoy tiene un solo `index-*.js` de 751 401 bytes y un CSS de 13 470 bytes. No se ha medido con el procedimiento de S3 ni se sabe de qué commit salió; la medición válida es la de `native-tables` T1.
  - `vue-router` 4.6.4 tiene 0 imports.
  - La mayor parte del peso probablemente venga de PrimeVue y del tema Aura, que se carga entero en `main.ts`, pero no se ha medido; por eso T2 espera a `native-tables`.
  - Ruta: inline.
