# Revelar, ocultar y copiar secretos

Objetivo: añadir «Ocultar todo» en la cabecera, revelar contraseñas una a una dentro de la comparación y copiar la contraseña desde la ficha con aviso del portapapeles.
Rama: `feat/secret-visibility` desde `main`. Fase 2. No depende de otros planes; `compare-resolution` usa su endpoint y su estado de revelado. Entrega: `ask-on-risk`, previsión ~300 líneas. T2 va en un commit propio por riesgo.
Comprobaciones: `python -m unittest discover -s tests`, `ruff check .`, `npm run build` y `npm run e2e`. Estado: planificado; orden aprobado (n.º 6 de 8, L4); supuestos pendientes, se preguntan al empezar.

## Specs

- **S1 — «Ocultar todo».** `docs/pendiente.md`: «botón «Ocultar todo» en la cabecera».
  - Un único estado compartido registra los secretos revelados (contraseña y código 2FA de la ficha, contraseñas de la comparación). «Ocultar todo» los oculta a la vez.
  - Guía (§7): «Exposición temporal: solo una credencial revelada por decisión del usuario; botón «Ocultar» claro, limpieza en bloqueo de sesión y al salir de ficha.»
  - **Supuesto:** el botón solo aparece cuando hay algo revelado.
- **S2 — Revelar en la comparación.** `docs/pendiente.md`: «revelar contraseñas de forma individual dentro de la comparación».
  - Cada registro de la comparación tiene su propio «Mostrar/Ocultar contraseña». Revelar uno no revela los demás.
  - Un endpoint nuevo devuelve **solo** la contraseña de un registro. No se reutiliza `GET /api/records/{id}`, porque también trae el código 2FA, y `odd/done/safari-support.md` (S4) limita dónde viaja: «Solo viaja en la importación, la ficha de edición, la sesión cifrada y la exportación.»
  - El endpoint tiene las mismas protecciones que el resto de `/api/` (origen, `Cache-Control: no-store`), responde 404 si el registro no existe y nunca escribe la contraseña en un error.
  - La guía (§4) sigue vigente: «No utilizar atajos para revelar contraseñas globalmente.»
- **S3 — Copiar contraseña.** `docs/pendiente.md`, ficha: «botón para copiar la contraseña con aviso de portapapeles».
  - Copia con `navigator.clipboard.writeText` y avisa: la contraseña queda en el portapapeles hasta que se copie otra cosa.
  - **Supuesto:** el portapapeles no se vacía solo. La aplicación no puede comprobar qué contiene sin pedir permiso de lectura, y vaciarlo podría borrar algo que el usuario copió después.
  - Si el navegador no permite copiar, se muestra un error sin la contraseña.

## Tasks

- [ ] T1 — S1: estado compartido de revelado y botón «Ocultar todo»; la ficha lo usa. RED primero en E2E. Ruta: inline.
- [ ] T2 — S2: endpoint de solo contraseña y revelado en la comparación. Ruta: inline.
  - RED primero en las pruebas de API (`tests/test_api.py`): la respuesta solo contiene la contraseña, nunca el código 2FA; lleva las cabeceras de `/api/`; responde 404 si el id no existe; rechaza un origen ajeno.
  - E2E de revelado individual.
  - Riesgo: punto 2 (un endpoint nuevo que entrega secretos). Commit propio y verificación independiente.
- [ ] T3 — S3: copiar contraseña. RED primero en E2E con permiso de portapapeles concedido y denegado. Ruta: inline.
- [ ] T4 — Documentación en `docs/flujo-usuario.md` y en la tabla de 2FA si cambia algo. Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`: `EditorDialog.vue` guarda en estado local la visibilidad de la contraseña y del 2FA; `detail()` (`review_state.py`) es la única respuesta que lleva el código 2FA; la comparación solo recibe resúmenes, sin contraseñas. `127.0.0.1` y `localhost` son contextos seguros, así que la API del portapapeles está disponible. No depende de ninguna decisión pendiente. Ruta: inline.
- **L4 (2026-11-10).** Revisión del plan contra `main` (`af881a5`), tras la Fase 1 y `review-filters`, a petición del usuario: «Planifica el resto de la fase2». Orden aprobado: «Pequeños primero (Recomendado)»; este plan es el n.º 6 de 8. Supuestos: «Justo antes de cada uno (Recomendado)», así que los supuestos y las decisiones pendientes se preguntan al empezar.
  - Nada desfasado: el revelado es estado de cada diálogo (`EditorDialog.vue:31-41`), y `navigator.clipboard` no se usa en ningún sitio.
  - Es el plan de más riesgo de la fase: un endpoint que entrega contraseñas (T2, commit propio y verificador independiente), contraseñas en el DOM de la comparación y el portapapeles.
  - Decisiones pendientes nuevas: dónde vive el estado compartido de revelado (almacén Pinia o módulo); la forma del endpoint; si copiar existe en escritorio y en el móvil; copiar frente a la guía §4 («no atajos para revelar globalmente»).
