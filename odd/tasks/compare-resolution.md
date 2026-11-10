# Resolver duplicados desde la comparación

Objetivo: que la comparación se entienda y permita decidir, en dos etapas (L4).
- **Etapa A, comprensión:** agrupar por sitio y usuario, identificar las versiones de contraseña sin mostrarlas, y retirar los chips que comparan cada registro con el primero (S5-S7).
- **Etapa B, resolución:** convertir la comparación en un panel de decisión. Muestra cada registro con sus datos originales y permite conservar A, B o ambos, fusionar notas y editar el candidato final en una sola operación reversible (S1-S4).

La Etapa A va primero y no mezcla la legibilidad con las operaciones delicadas sobre credenciales.
Ramas: `feat/compare-resolution-a` (Etapa A) y `feat/compare-resolution-b` (Etapa B), cada una desde `main` (L5). Fase 2. Depende de: `keyboard-accessibility` (foco en diálogos); la Etapa B, además, de `secret-visibility` (revelado y endpoint de solo contraseña). Entrega: `ask-on-risk`, previsión ~600 líneas, por encima de ~400: se preguntará la estrategia de encadenado. T1 va en un commit propio por riesgo.
Comprobaciones: `python -m unittest discover -s tests`, `ruff check .`, `npm run build` y `npm run e2e`. Estado: planificado; orden aprobado (n.º 7 (Etapa A) y 8 (Etapa B) de 8, L5); supuestos pendientes, se preguntan al empezar.

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
- **S5 — Etapa A: agrupar cuentas en lugar de comparar con el primero (L4).**
  - **Hoy** (`CompareDialog.vue`): cada miembro lleva los chips «URL ✓/≠», «Usuario ✓/≠» y «Clave ✓/≠». La propia interfaz avisa: «Las coincidencias se comparan respecto al primer registro activo del grupo.» Con varios usuarios en un grupo resulta confuso. El backend ya clasifica cada grupo como `exact`, `conflict` o `multiple-accounts`.
  - **Requisitos**, tal como los fijó la conversación del usuario:

    | Requisito | Comportamiento esperado |
    |---|---|
    | Agrupación visual | Sitio → Usuario → Registros |
    | Contraseñas | Identificadores A/B/C por contraseña diferente dentro de cada cuenta |
    | Coincidencias | Varios navegadores con la misma contraseña muestran la misma letra |
    | Conflictos | Se destacan cuando una misma cuenta tiene contraseñas distintas |
    | Cuentas diferentes | No se presentan como conflictos entre sí |
    | Procedencia | Se conserva navegador, archivo y línea de importación |
    | Comparación detallada | Permite comparar variantes sin revelar contraseñas automáticamente |
    | Móvil | Secciones por usuario, potencialmente desplegables |
    | Seguridad | No exponer contraseñas ni códigos TOTP en los resúmenes |

  - **Requisito técnico:** «las equivalencias entre contraseñas deben calcularse en el backend y comunicarse mediante identificadores opacos de grupo, sin enviar contraseñas ni hashes al resumen del frontend».
  - **Sin cambios de reglas:** se mantienen las reglas actuales de detección de duplicados y de tratamiento de TOTP. «Agrupar visualmente no debe significar fusionar registros automáticamente.»
  - **Solo identidades conocidas:** se agrupa por las que ya existen, sin deducir que dos dominios de una misma organización son intercambiables (véase D5).
  - Ni el modelo de datos ni el formato `.pwc` cambian.
- **S6 — Notas en la comparación (L4).** Del usuario: «Mostrar la nota en la comparación ¿por ejemplo con un chip de nota que muestre la nota en el :hover?»
  - Un indicador «Tiene nota» que se activa al pulsarlo o con el teclado, no al pasar el ratón. Es accesible, funciona en móvil y no revela notas por un movimiento accidental.
  - `CredentialSummary` no incluye notas, y no se añaden a todas las respuestas de `/api/workspace`. Tampoco se piden contraseñas ni TOTP solo para mostrar una nota: si hace falta, una consulta específica y explícita.
- **S7 — Estado en una línea (L4).** Del usuario: «En la comparación cuando descartas un registro su estado indica "en la papelera" y ocupa dos líneas de texto quiero que ocupe solo una.» El estado (`<span class="status">`) no se parte en dos líneas y no desborda en móvil.

## Tasks

Etapa A (va primero):

- [ ] T5 — S5: equivalencias de contraseña calculadas en el backend, como identificadores opacos por cuenta dentro de cada grupo. Sustituyen a `match_url`, `match_username` y `match_password` de `GroupMember`. RED primero en `tests/test_workspace.py` y `tests/test_workspace_contract.py`: misma contraseña da la misma letra; ni contraseñas ni hashes en la respuesta. Ruta: inline. Riesgo: punto 2 (información derivada de secretos en la API) y punto 3 (cambia el contrato de `/api/workspace`). Commit propio y verificación independiente.
- [ ] T6 — S5-S7: presentación Sitio → Usuario → Registros en escritorio y en móvil, sin los chips; indicador «Tiene nota»; estado en una línea. RED primero en E2E. Ruta: inline.
- [ ] T7 — Documentación de la Etapa A en `docs/flujo-usuario.md` (paso 3) y en la guía. Ruta: inline.

Etapa B:

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
- **L4 (2026-11-04).** Anotaciones del usuario sobre una conversación externa, pegada en la sesión, para añadirlas a la hoja de ruta. La conversación recomendaba: «actualizar compare-resolution.md con estos criterios antes de aprobar su implementación», con una «Etapa A — Comprensión de los datos» y una «Etapa B — Resolución de conflictos». Se añaden S5-S7 y T5-T7 (Etapa A, va primero); T1-T4 pasan a ser la Etapa B. Las capturas de la conversación tenían identificadores reales; no se copian. Comprobado en `main` (`ec8d167`): los chips y el aviso citados en S5, `CredentialSummary` sin notas y `<span class="status">` con «En la papelera».
- **L5 (2026-11-10).** Revisión del plan contra `main` (`af881a5`), tras la Fase 1 y `review-filters`, a petición del usuario: «Planifica el resto de la fase2». Orden aprobado: «Pequeños primero (Recomendado)»; este plan es el n.º 7 (Etapa A) y 8 (Etapa B) de 8. Supuestos: «Justo antes de cada uno (Recomendado)», así que los supuestos y las decisiones pendientes se preguntan al empezar.
  - Etapa A: T5 sustituye `match_url`, `match_username` y `match_password` (`review_state.py:69-71`, `GroupMember` en `types.ts`), lo que cambia la respuesta de `/api/workspace`. Las pruebas de la comparación sobre `.compare-flags` (`e2e/review.spec.ts:542`, `:553` y `:580`) se reescriben, no solo se amplían, y cambia el componente 2 de la guía («Chip de coincidencia»). Lo demás de S5-S7 sigue siendo cierto.
  - Decisiones pendientes nuevas de la Etapa A: cómo se muestra un 2FA distinto; qué significan las letras A/B/C cuando un sitio tiene varios usuarios; las secciones desplegables del móvil frente a «no esconder la razón del conflicto» (`docs/guia-visual.md:95`).
  - Entrega: cada etapa en su rama, `feat/compare-resolution-a` y `feat/compare-resolution-b`; la Etapa A, ~250-300 líneas.
