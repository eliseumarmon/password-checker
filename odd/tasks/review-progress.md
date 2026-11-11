# Progreso de revisión, estados y grupos «Varias cuentas»

Objetivo: que la barra «Revisadas» cuente también lo descartado, que los grupos «Varias cuentas» se resuelvan al revisarlos y dejar tres estados de revisión.
Rama: `fix/review-progress` desde `main`. Entrega: `single-pr`, un commit por tarea; previsión ~250 líneas.
Comprobaciones: `.venv/Scripts/python.exe -m unittest discover -s tests` y `ruff check .`; en las tareas con frontend, `npm run build` y `npm run e2e` en `frontend/`.

## Specs

- **S1 — Barra de progreso.** «El progreso de revisados contempla, registros revisados, verificados y descartados (aunque no cambie su estado).»
  - **Confirmado (L5):** una credencial cuenta si está en la papelera, sea cual sea su estado, o si está activa y «Revisada». No cuentan «Pendiente» ni «No funciona». El divisor sigue siendo el total, papelera incluida.
- **S2 — Grupos «Varias cuentas».** «Los duplicados de varias cuentas tampoco se resuelven al marcarlos como revisados o verificados o descartar registros hasta que solo queda uno y sigue mostrándose como duplicado.»
  - **Confirmado (L5):** un grupo «Varias cuentas» sale de la lista y del contador cuando todas sus credenciales activas están «Revisada». Una en «No funciona» o «Pendiente» lo mantiene abierto.
  - «Contraseñas diferentes» y «Copia exacta» no cambian: siguen resolviéndose al descartar o fusionar hasta que queda una.
  - El diálogo de comparar deja de decir «Ya no quedan duplicados activos en este grupo.» cuando el grupo se resuelve por revisión, porque las credenciales siguen activas.
- **S3 — Estados.** «La verdad es que no funciona y verificada son dos matices de revisada no? es necesario mantenerlos?» y «Puede tener utilidad para el estado personal, esta la marco como no funciona, y luego lo "verifico"».
  - **Confirmado (L5):** quedan «Pendiente», «Revisada» y «No funciona». «Verificada» se fusiona con «Revisada».
  - Una sesión `.pwc` guardada antes con `verified` se sigue abriendo y esas credenciales quedan «Revisada».
- **S4 — Contador `verified`.** «Qué hacemos con el verified que no se usa para nada?» **Confirmado (L5):** se elimina de `stats`.
- **S5 — Documentación.** `docs/flujo-usuario.md`, `docs/pendiente.md` y `README.md` describen los tres estados, la barra y la resolución de grupos.

## Tasks

- [x] T1 — S3, S4: tres estados y sin `verified`, backend y frontend, con la conversión al abrir sesiones. RED primero en `unittest`. Riesgo: punto 1 (lectura de sesiones guardadas). Ruta: inline. RED y GREEN en L6.
- [x] T2 — S1: barra de progreso. RED primero en `unittest`. Ruta: inline. RED y GREEN en L8.
- [ ] T3 — S2: grupos «Varias cuentas» resueltos por revisión y texto del diálogo. RED primero en `unittest` y E2E. Ruta: inline.
- [ ] T4 — S5: documentación. Ruta: inline.

## Log

- **L1 (2026-11-10).** Informe del usuario: «Cuando hay duplicados parece que cuando los resuelves no se descuentan. ni en revisado ni en veridicado. Cuando lo mandas a la papelera tampoco.» Reproducido con el `Workspace` real: `stats` cuenta también la papelera y una credencial pendiente descartada nunca cuenta como revisada.
- **L2 (2026-11-10).** «Me interesa simplificar esto.» Reproducido: un grupo «Varias cuentas» de tres sigue con las tres verificadas y con una descartada; solo desaparece cuando queda una activa (`review_state.py`, `detect_groups`).
- **L3 (2026-11-10).** Hallazgo: `review` no tiene ningún efecto salvo la etiqueta, el color y el filtro; la exportación solo mira `included` (`workspace.py:196`). `stats.verified` no se muestra en la interfaz.
- **L4 (2026-11-11).** «Puede tener utilidad para el estado personal, esta la marco como no funciona, y luego lo "verifico"». Se mantiene «No funciona» como marca de trabajo pendiente.
- **L5 (2026-11-11).** Propuesta: tres estados, «No funciona» no cuenta en la barra ni resuelve grupos, `verified` eliminado y convertido en «Revisada» al abrir sesiones antiguas. Respuesta: «Sí, creo que estará bien así.» Rama `fix/review-progress` creada desde `main`.
- **L6 (2026-11-11).** T1. RED: `test_review_states_are_pending_reviewed_and_incorrect` (no rechaza `verified`) y `test_session_saved_with_the_retired_verified_state_opens_as_reviewed` fallan. GREEN: `unittest` 186 de 186, `ruff check .` limpio, E2E 193 de 193 (`filters.spec.ts` ajustado para conservar un filtro sin grupos). Las pruebas que usaban `verified` como estado cualquiera pasan a `reviewed`, o a `incorrect` cuando necesitan dos cambios distintos seguidos. «Revisada» toma el verde de «Verificada» y el editor la muestra sin «(sin verificar acceso)».
- **L7 (2026-11-11).** T1, commit `8b4c2cc`. Evaluación: riesgo alto (punto 1 elevado a mano: la carga de sesiones convierte `verified`). Verificador independiente en copia aislada: S3 y S4 PASS, `unittest` 186 de 186, `ruff` limpio; `restore` probado con los tres estados, `verified` y valores no válidos (lista, `None`, número, texto desconocido), sin cambios en el espacio anterior al rechazar. Revisión con riesgo y fiabilidad: aprobada y confirmada. Sugerencias sin bloqueo, para más adelante: probar `PATCH /api/records` con `verified` y abrir un `.pwc` cifrado con `verified` por la API.
- **L8 (2026-11-11).** T2. RED: `test_progress_counts_reviewed_and_trashed_records_but_not_incorrect_ones` falla (`2 != 1`: «No funciona» contaba). GREEN: `unittest` 187 de 187, `ruff` limpio; E2E nueva `counts reviewed and trashed records in the progress, but not those marked as not working` y suite completa 194 de 194.
