# Reliability hardening — guardado, CSV y CI E2E

Objetivo: cerrar tres riesgos de fiabilidad identificados en la revisión del 2026-11-01 tras retirar la CLI. El producto es la GUI local FastAPI + Vue; Python mínimo: 3.12.

Estado: **pendiente**; T3 planificada para empezar primero (L2). Este documento registra trabajo futuro; no acredita que las correcciones o las pruebas se hayan ejecutado.

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

### [ ] T1 — Invariante de ida y vuelta de sesiones (prioridad alta)

**Problema:** el guardado puede devolver un archivo que la restauración rechaza por límites de contenido o por tamaño.

**Áreas:** `application/session_snapshot.py`, `application/workspace.py`, `application/limits.py`, `infrastructure/sessions.py`, `api.py` y tests de sesión/API.

**Aceptación:**
1. Cualquier respuesta HTTP 200 de `/api/session/save` produce un `.pwc` que pasa `decrypt_session()` y `from_payload()` y se restaura sin pérdida de datos; conservar compatibilidad con sesiones v1 existentes.
2. Un estado que rebasa la política de recuperación no debe generar un respaldo aparentemente válido. Definir y aplicar explícitamente qué ocurre al importar/editar datos que desbordarían esa política, para no dejar al usuario sin una vía fiable de respaldo.
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

### [ ] T3 — Ejecutar Playwright en GitHub Actions (prioridad media)

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
