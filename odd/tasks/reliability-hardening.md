# Reliability hardening — guardado, CSV y CI E2E

Objetivo: cerrar tres riesgos de fiabilidad identificados en la revisión del 2026-11-01 tras retirar la CLI. El producto es la GUI local FastAPI + Vue; Python mínimo: 3.12.

Estado: T3 hecha y verificada en GitHub Actions (L5); T1 hecha (L7); T2 pendiente.

## Contexto y alcance

- `application/session_snapshot.py`: `to_payload()` serializa sin comprobar los límites que `from_payload()` exige al restaurar (100 000 registros, 15 archivos, longitud de campos y nombres). `infrastructure/sessions.py` limita a 25 MiB la lectura de un `.pwc`, pero `encrypt_session()` no garantiza ese límite al generar el archivo.
- `infrastructure/csv_reader.py`: `csv.reader(..., strict=True)` puede lanzar `csv.Error`. `api.py:/api/import` captura `ValueError`, `UnicodeError` y `OSError`, pero no `csv.Error`.
- `.github/workflows/tests.yml`: ejecuta tests Python y build/typecheck de Vue, pero no `npm run e2e`. Los tests de Playwright ya existen en `frontend/e2e/`.

No modificar el formato de `.pwc` v1, la criptografía, las reglas de consolidación ni la retirada de la CLI salvo que un hallazgo demostrable lo exija. Mantener los archivos y credenciales ficticios exclusivamente en pruebas.

## Specs / criterios de aceptación globales

- **S1 — Recuperabilidad:** un guardado `.pwc` que devuelve éxito debe poder descifrarse y restaurarse con los validadores y límites vigentes, conservando registros, edición, estado de revisión y metadatos.
- **S2 — Fallo seguro:** una operación rechazada no altera el workspace ni revela contraseñas en errores, respuestas o logs introducidos por la corrección.
- **S3 — Regresión verificable:** cada corrección incluye una prueba que reproduce el problema antes de corregirlo (RED → GREEN cuando sea viable) y ejecuta las suites relevantes.
- **S4 — Contratos coherentes:** los límites y mensajes de error se definen en la capa adecuada, sin duplicaciones innecesarias y sin modificar silenciosamente archivos de entrada.

## Tareas (una rama y una revisión independiente por tarea)

### [x] T1 — Invariante de ida y vuelta de sesiones (prioridad alta)

**Problema:** el guardado puede devolver un archivo que la restauración rechaza por límites de contenido o por tamaño.

**Áreas:** `application/session_snapshot.py`, `application/workspace.py`, `application/limits.py`, `infrastructure/sessions.py`, `api.py` y tests de sesión/API.

**Aceptación:**
1. Cualquier respuesta HTTP 200 de `/api/session/save` produce un `.pwc` que pasa `decrypt_session()` y `from_payload()` y se restaura sin pérdida de datos; conservar compatibilidad con sesiones v1 existentes.
2. Un estado que rebasa la política de recuperación no debe generar un respaldo aparentemente válido. **Decidido (L6): rechazar al entrar.** Importar, editar, mover a la papelera, fusionar y abrir una sesión se rechazan con un error 422 claro si el workspace resultante no se pudiera guardar y volver a abrir (validación de `from_payload` y tamaño real del `.pwc`). Las operaciones son atómicas: si se rechazan, el workspace y el historial de deshacer no cambian. No se descarta ninguna credencial en silencio. Si el workspace ya excede los límites, se aceptan las operaciones que no empeoran el exceso. Los límites se centralizan en `application/limits.py`, incluido el tamaño máximo del `.pwc`. Guardar conserva la validación defensiva y comprueba los bytes reales del archivo.
3. Si una operación no puede completarse, devolver un error controlado y accionable, preservando el workspace anterior; no producir ni ofrecer un `.pwc` no restaurable.
4. Cubrir con pruebas límites de registros y campos, metadatos, y tamaño total cifrado (incluyendo expansión de JSON/base64). No usar credenciales reales ni requerir fixtures desmesurados cuando se pueda inyectar un límite reducido de forma controlada.
5. No cambiar formato, versión o parámetros criptográficos sin una especificación separada.

### [ ] T2 — Traducir errores de lectura CSV a 422 (prioridad media)

**Problema:** un CSV con comillas mal cerradas u otra sintaxis inválida puede lanzar `csv.Error` y provocar un HTTP 500.

**Áreas:** `infrastructure/csv_reader.py`, `api.py`, `tests/test_csv_upload.py` y `tests/test_api.py`.

**Aceptación:**
1. Los errores `csv.Error` tanto en cabecera como en filas se convierten en una respuesta HTTP 422 comprensible (no HTTP 500).
2. No exponer en el mensaje ninguna contraseña, celda completa, ruta sensible ni contenido CSV; mantener diagnósticos útiles sin filtrar datos.
3. La importación múltiple sigue siendo atómica: si falla un CSV, no cambia ningún registro, metadato ni historial del workspace.
4. Añadir al menos un test de CSV con entrecomillado inválido y una prueba de API que compruebe código, ausencia de secretos y estado intacto.
5. Mantener el rechazo de reparaciones ambiguas y la aceptación de CSV válidos (comas y saltos de línea correctamente entrecomillados).

### [x] T3 — Ejecutar Playwright en GitHub Actions (prioridad media)

**Problema:** CI puede quedar verde con un flujo roto de la GUI porque solo compila el frontend.

**Áreas:** `.github/workflows/tests.yml`, `frontend/playwright.config.ts` (solo si es necesario), `frontend/e2e/`.

**Aceptación:**
1. En push y pull request, CI instala Node.js 22, Python 3.12, dependencias backend/frontend y Chromium con las librerías de sistema necesarias, y ejecuta `npm run e2e`.
2. Se ejecutan pruebas reales de importación, revisión/edición, exportación y guardado/restauración de sesión; no basta con compilar ni con que Playwright detecte cero tests.
3. El trabajo falla si falla una prueba; conservar trazas o artefactos de fallos cuando sea práctico, sin incluir contraseñas reales.
4. Usar exclusivamente datos ficticios y un backend local aislado, sin telemetría ni servicios externos. Respetar la ejecución serial del workspace en memoria.
5. Mantener separados y verdes el trabajo Python y el typecheck/build frontend. Documentar localmente cómo reproducir un fallo E2E.

**Implementación prevista (añadida el 2026-11-02, L2):**

- Nuevo job `e2e` en `tests.yml`, separado de `python` y `frontend`: `actions/setup-python@v5` (3.12) e instalación de `backend/requirements.txt`; `actions/setup-node@v4` (22) y `npm ci` en `frontend/`; `npx playwright install --with-deps chromium`; `npm run e2e` con `E2E_PYTHON=python`, que respetan `playwright.config.ts` y `e2e/isolated-welcome.ts`, de modo que no hace falta `.venv` en CI.
- Si falla, se suben `frontend/test-results/` (trazas `retain-on-failure`) con `actions/upload-artifact@v4` y retención corta. Solo contienen datos ficticios de las pruebas.
- `forbidOnly` ya se activa con `CI`. No se cambia `playwright.config.ts` salvo que la primera ejecución en Linux lo exija; cualquier ajuste de pruebas por diferencias de plataforma (fuentes, medidas) se anota en el registro.
- Comprobación de que no pasa con cero pruebas: el registro del job muestra el número de pruebas ejecutadas (hoy 65).
- Documentación: README (quitar «Las pruebas E2E todavía no se ejecutan en CI») y `docs/pendiente.md` (quitar «Ejecutar las pruebas E2E en CI»).
- Verificación: GitHub Actions no se puede ejecutar en local con lo instalado, así que la prueba real es subir la rama y comprobar la ejecución con `gh run`. Subir la rama se pide al usuario en ese momento. Riesgo alto (CI): revisión independiente antes de integrar.

## Orden de ejecución y validación

T3 → T1 → T2 (L2: se adelanta T3). Cada tarea sale de `main` actualizado, con prueba de regresión, revisión independiente y verificación antes de fusionar. No mezclar los tres cambios en un único PR.

**Comandos de referencia:**

```bash
python -m unittest discover -s tests -v
cd frontend && npm run build && npm run e2e
```

## Registro

- **L1 (2026-11-01):** revisión de `main` tras retirar la CLI: tres riesgos detectados; los tests Python y el build frontend habían terminado correctamente en GitHub Actions, pero E2E no estaba incluido en el workflow. Se crea esta especificación, sin implementación.
- **L2 (2026-11-02):** una revisión externa, pegada por el usuario, recomienda integrar Playwright en CI antes de seguir ampliando la interfaz. Petición: «Sí» a planificar E2E en CI. Comprobado: `tests.yml` no ejecuta E2E; T1 y T2 siguen pendientes (`api.py` no captura `csv.Error`). Se adelanta T3 y se detalla su implementación; T1 y T2 no cambian.
- **L3 (2026-11-02):** petición: «Sí» a empezar la implementación. T3 en `ci/e2e-playwright` (encadenada sobre el plan): job `e2e` en `tests.yml` según la implementación prevista; YAML validado con `yaml.safe_load` (jobs `python`, `frontend`, `e2e`). En local, con el `.venv` primero en el `PATH`, `E2E_PYTHON=python` y `CI=1`: 65 pasadas, lo que prueba la resolución por nombre que usará el CI. README y `pendiente.md` actualizados. Pendiente: la primera ejecución real en GitHub Actions (requiere subir la rama) y la revisión independiente.
- **L4 (2026-11-02):** revisión de riesgo alto (cuatro lentes) de `8fd43c0` aprobada. Aplicado: `timeout-minutes` de 20 en el paso E2E (falla el paso y se suben las trazas) y de 30 en el job; línea de estado actualizada. Descartado: añadir `permissions` al job, porque el workflow ya declara `contents: read` para todos; fijar las acciones por SHA, como en los jobs existentes, queda fuera de alcance. El README afirma que el job existe: la rama no se integra hasta que la primera ejecución en GitHub Actions salga en verde.
- **L5 (2026-11-02):** petición: «Correcto» a subir la rama. `ci/e2e-playwright` subida a `origin`; ejecución [41449520998](https://github.com/eliseumarmon/password-checker/actions/runs/41449520998) en verde: `python`, `frontend` y `e2e` correctos, y el registro de `e2e` muestra «65 passed (1.1m)» en Linux, sin ajustes de plataforma. Línea de estado reescrita (la revisión de `9481319` señaló que conservaba la frase de trabajo futuro). No verificado: la subida del artefacto `playwright-traces`, que solo ocurre si falla una prueba.
- **L6 (2026-11-02):** petición: «Sí sigue con t1». Huecos confirmados: el `.pwc` ocupa unas 2,7 veces el CSV (originales y candidatos, JSON y base64), así que un CSV de unos 10 MiB ya supera los 25 MiB de apertura; el lector CSV admite campos de 131 072 caracteres y la apertura 100 000; caben más de 100 000 filas en 20 MiB; `merge_exact` une notas sin límite. Medido: 100 000 registros mínimos son 34 MiB de JSON; la comprobación completa (`to_payload`, JSON y `from_payload`) tarda unos 1,8 s con ese volumen, que ya no cabe, y milisegundos con exportaciones normales. Decisión del usuario, literal: «Selecciona «Rechazar al entrar (Recom.)». Garantizar que las importaciones, fusiones y ediciones sean atómicas y que todas las operaciones aceptadas mantengan el workspace dentro de los límites necesarios para guardar y restaurar una sesión .pwc. Centralizar los límites, comprobar el tamaño real del archivo resultante y conservar la validación defensiva al guardar. No descartar credenciales silenciosamente y permitir operaciones que corrijan un exceso de límites.» Criterio 2 reescrito. Además, la API no traduce `ValueError` en papelera ni en fusionar: se añade. Rama `fix/t1-session-roundtrip` desde `main`.
- **L7 (2026-11-02):** T1 en `fix/t1-session-roundtrip`. RED: `tests/test_session_limits.py` no se podía importar (faltaba `encode_payload`) y las dos pruebas nuevas de `tests/test_api.py` fallaban (guardar sin validar; fusionar rechazada devolvía 500). GREEN: `application/limits.py` reúne todos los límites, incluido `MAX_SESSION_BYTES`, y `session_file_size()` calcula el tamaño exacto del `.pwc` (132 bytes de envoltorio más el base64 del texto cifrado; fijado contra `encrypt_session` por prueba); `session_snapshot.py` añade `encode_payload` y `session_fit`, y lee los límites en el momento; `Workspace` comprueba cada estado nuevo (importar y abrir sesión, estricto; editar, papelera y fusionar, aceptando lo que no empeora un exceso) antes de aplicarlo, sin paso de deshacer si se rechaza; `serialize()` valida con `from_payload`; `encrypt_session` nunca devuelve más de `MAX_SESSION_BYTES`; la API traduce a 422 los rechazos de papelera y fusionar. Mensajes con el campo, el origen y la línea, nunca el valor. `docs/flujo-usuario.md` lo describe. Comprobaciones: 76 tests de backend (12 en las pruebas nuevas y de arquitectura), 65 E2E, `ruff` 81 avisos frente a 82 en `main` (ninguno nuevo). Riesgo alto (sesiones y datos guardados): pendiente de revisión independiente.
- **L8 (2026-11-02):** revisión de `748de86` (lentes de riesgo, resiliencia y fiabilidad, pedidas por tocar sesiones guardadas) aprobada. Aplicado: la regla de «no empeorar» comparaba las tres medidas a la vez y rechazaba, por ejemplo, mover a la papelera (un byte más) cuando solo se superaba el límite de caracteres; ahora cada medida debe quedar dentro de su límite o no crecer si ya lo superaba (RED: «test_operations_that_do_not_touch_the_exceeded_limit_are_allowed»). Añadida la prueba de que abrir una sesión que no se podría volver a guardar se rechaza sin cambios (pasaba ya; prueba de mutación: sin `_ensure_restorable` en `restore()` falla). No aplicado: cada cambio vuelve a serializar todo el workspace con el bloqueo tomado; con exportaciones normales son milisegundos y cerca de 25 MiB alrededor de un segundo. Se acepta como coste de la comprobación completa, sin optimización incremental. 78 tests de backend; `ruff` sin avisos nuevos.
- **L9 (2026-11-02):** revisión de `24da568` aprobada con un aviso: el exceso de texto se medía por número de campos, así que alargar un campo que ya se pasaba, o pasar el exceso a otro campo, se aceptaba. Petición, literal: «Corrige el hallazgo de longitud antes de cerrar T1: mide el exceso total de caracteres, no el número de campos que superan el límite. Añade pruebas que verifiquen el rechazo de modificaciones que aumentan el exceso, la aceptación de las que lo reducen y la ausencia de mutaciones y entradas de deshacer tras un rechazo. Mantén sin cambios la estrategia de rendimiento actual. Ejecuta las pruebas afectadas y deja constancia de los resultados. No integres ni subas la rama todavía.» RED: «test_lengthening_an_already_oversized_field_is_rejected» y «test_moving_the_excess_to_another_field_without_reducing_it_is_rejected» fallaban; «test_changes_that_reduce_the_character_excess_are_accepted» ya pasaba. Las de rechazo comprueban que `_records`, el historial de deshacer y la instantánea no cambian. GREEN: `SessionFit.excess_chars` suma los caracteres que sobran en todos los campos (candidato y original) y sustituye al número de campos en `no_worse_than`; los mensajes no cambian. Rendimiento sin cambios: la comprobación completa sigue igual. Resultados: `tests/test_session_limits.py` 15 pasadas; pruebas afectadas (límites, API, sesiones, instantánea, workspace, contrato y arquitectura) 55 pasadas; backend completo 81 pasadas; `ruff` 81 avisos, ninguno nuevo frente a `main` (82). Sin E2E: el cambio no toca la API ni el frontend. Rama sin integrar ni subir.
