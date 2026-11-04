# Resolver duplicados desde la comparación

Objetivo: convertir la comparación en un panel de decisión. Muestra cada registro con sus datos originales y permite conservar A, B o ambos, fusionar notas y editar el candidato final en una sola operación reversible.
Rama: `feat/compare-resolution` desde `main`. Fase 2. Depende de: `secret-visibility` (revelado y endpoint de solo contraseña) y `keyboard-accessibility` (foco en diálogos). Entrega: `ask-on-risk`, previsión ~600 líneas, por encima de ~400: se preguntará la estrategia de encadenado. T1 va en un commit propio por riesgo.
Comprobaciones: `python -m unittest discover -s tests`, `ruff check .`, `npm run build` y `npm run e2e`. Estado: planificado, sin empezar.

## Specs

- **S1 — Panel comparativo.** `docs/pendiente.md`: «panel comparativo que muestre de cada registro la URL original, el nombre, el usuario, la contraseña oculta, las notas y el estado, y permita conservar A, B o ambos, fusionar notas y editar el candidato final, distinguiendo los datos originales (inmutables) de la salida editable».
  - Cada registro muestra lo importado (inmutable, de `original`) separado de lo editable (el candidato). La contraseña aparece oculta, con el revelado individual de `secret-visibility`.
  - El código 2FA nunca se muestra en el panel. Si un registro descartado tiene un código 2FA que el conservado no tiene, el panel lo avisa sin mostrarlo.
- **S2 — Comparación de originales.** `docs/pendiente.md`: «una comparación más completa de originales». Limitación conocida: «El comparador muestra coincidencias y procedencia, pero no ofrece una comparación completa de contraseñas y notas originales.» **Supuesto, a concretar en T1:** el endpoint de solo contraseña también permite pedir la contraseña original, con las mismas protecciones; las notas originales se añaden a la respuesta del panel.
- **S3 — Resolución.** Una operación del backend, que cuenta como un único paso de «Deshacer»:
  - **Conservar uno:** los demás miembros pasan a la papelera (`included = false`). Nunca se borran y se pueden restaurar.
  - **Conservar ambos:** todos siguen incluidos. **Supuesto:** quedan como «Revisada», para que el grupo deje de figurar como pendiente sin añadir ningún campo nuevo a la sesión.
  - **Fusionar notas:** el registro conservado recibe las notas con `combine_notes`, como «Fusionar copias exactas».
  - **Editar el candidato final:** las ediciones siguen las reglas de `Workspace.change()`. Si cambian la URL, el usuario, la contraseña o el código 2FA, el registro vuelve a «Pendiente».
  - Se valida todo antes de aplicar nada: los ids existen, el conservado está entre ellos y el resultado cabe en una sesión cifrada (`_ensure_restorable`).
  - No cambia el formato `.pwc`: solo cambian candidatos e inclusión.
- **S4 — Móvil.** `docs/pendiente.md`: «en móvil, acciones «Elegir para exportación», «Conservar ambas» y «Fusionar notas»». «Elegir para exportación» equivale a conservar ese registro.

## Tasks

- [ ] T1 — S2, S3: caso de uso, endpoint y contrato. Ruta: inline.
  - RED primero en `tests/test_workspace.py`: cada tipo de resolución, un solo paso de deshacer, validación sin cambios parciales, el registro vuelve a pendiente al editar un secreto, códigos 2FA que no se pierden (siguen en la papelera).
  - RED primero en `tests/test_api.py` y `tests/test_workspace_contract.py`: cabeceras, errores sin secretos y nada de 2FA en la respuesta.
  - Riesgo: punto 1 (cambia datos en bloque) y punto 2 (amplía qué secretos entrega la API). Commit propio y verificación independiente.
- [ ] T2 — S1: panel de escritorio. RED primero en E2E. Ruta: inline.
- [ ] T3 — S4: acciones en móvil. E2E a 390 px. Ruta: inline.
- [ ] T4 — Documentación en `docs/flujo-usuario.md` (paso 3) y en la guía (§4, panel comparativo). Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`:
  - `detail()` entrega de `original` el nombre, la URL, el usuario, la procedencia y la línea, pero no la contraseña, las notas ni el código 2FA originales.
  - `merge_exact()` ya resuelve grupos en un solo paso con `combine_notes` y `merged_totp`, y sirve de modelo.
  - Nada de esto cambia el formato `.pwc`. No depende de ninguna decisión pendiente; los supuestos de S2 y S3 se confirman al aprobar el plan.
  - Ruta: inline.
