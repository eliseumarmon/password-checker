# Dependencias y cadena de suministro: auditoría y plan de endurecimiento

Objetivo: diagnosticar riesgos de dependencias, reproducibilidad y CI, y proponer un plan proporcionado. Diagnóstico completo en [auditoria-dependencias](../../docs/auditoria-dependencias.md).
Rama de la auditoría: `docs/dependency-audit` desde `main` (solo documentación). **Estado: fase prioritaria cerrada (L25).** P2-P8 integradas en `main`. P9 y P11 completadas (L28-L29). Quedan solo las opcionales P10 y P13, y P12, vinculada a la Fase 1 del frontend (L26). Nada se integra en `main` sin aprobación del usuario. Pruebas de cada tarea: `python -m unittest discover -s tests`, `ruff check .`, `npm run build`, `npm run e2e`.

## Specs

Fase de auditoría (autorizada):

- **S1 — Inventario y diagnóstico.** «Examina el estado real del repositorio, tanto backend (Python/FastAPI) como frontend (Vue/Vite)». «Ejecuta `pip-audit` y `npm audit`, distinguiendo dependencias de producción y desarrollo.» «Determina si las instalaciones son reproducibles entre desarrollo y CI.» «No instales ni ejecutes herramientas adicionales sin valorar antes su procedencia y seguridad.»
- **S2 — Análisis de riesgos.** Por hallazgo: «Dependencia o componente afectado.», «Versión instalada y versiones vulnerables, cuando corresponda.», «Vulnerabilidad identificada y referencias (CVE/GHSA).», «Severidad y explotabilidad real en Password Checker.», «Si afecta a producción, desarrollo o CI.», «Posible impacto sobre credenciales, TOTP, cifrado, sesiones `.pwc` y archivos importados.», «Corrección recomendada y riesgos de compatibilidad.» «No equipares automáticamente la severidad publicada de una vulnerabilidad con su riesgo real en nuestra aplicación.» «Distingue los hallazgos confirmados, los riesgos potenciales y las cuestiones que no hayan podido verificarse.»
- **S3 — Reproducibilidad y política de versiones.** «No implementes todavía ninguna alternativa. Recomienda la más adecuada para el tamaño y arquitectura actuales del proyecto, evitando complejidad innecesaria.»
- **S4 — Plan de actuación.** «Prepara un plan siguiendo el flujo ODD existente, con tareas pequeñas, independientes y verificables.» Por tarea: «Prioridad según riesgo e impacto.», «Dependencias entre tareas.», «Archivos previsiblemente afectados.», «Criterios de aceptación verificables.», «Pruebas necesarias.», «Riesgos de regresión.», «Necesidad de revisión independiente.» «Distingue entre correcciones urgentes, mejoras de mantenimiento y medidas opcionales.»
- **S5 — Límites.** «No actualices paquetes.» «No modifiques el código ni la configuración de CI.» «No introduzcas nuevas herramientas permanentes.» «No alteres el cifrado, el formato `.pwc` ni las reglas de consolidación.» «No recuperes la CLI eliminada.» «No utilices credenciales reales.»
- **S6 — Entrega.** «Presenta primero un resumen ejecutivo de los hallazgos y sus prioridades.» «No dupliques información en `docs/pendiente.md`; utiliza referencias a los documentos específicos.» «Solicita una **revisión independiente del diagnóstico y del plan**, centrada en seguridad, exactitud de los hallazgos, proporcionalidad de las soluciones y posibles omisiones.» «No implementes ninguna corrección, no integres cambios en `main` y no modifiques dependencias hasta que apruebe el plan.»

Fase `fix/cryptography-50` (aprobada en L4):

- **S7 — Sin compatibilidad histórica.** «Actualmente no existen sesiones `.pwc` que debamos conservar generadas con esa versión.» «Elimina H3 del alcance de esta tarea como requisito de compatibilidad histórica.» «No crees fixtures históricas ni pruebas de migración entre versiones de `cryptography`.» «Mantén las pruebas normales de cifrado, descifrado, integridad, contraseñas incorrectas y manipulación de archivos.» «No cambies innecesariamente el formato `.pwc` ni los parámetros criptográficos.»
- **S8 — H2 antes de actualizar.** «Las pruebas obligatorias de cifrado y API no deben saltarse silenciosamente cuando faltan dependencias o se producen errores de importación.» «Deben fallar explícitamente para evitar falsos positivos en CI.» «Añade las pruebas necesarias para verificar este comportamiento, sin introducir complejidad innecesaria.»
- **S9 — Actualizar `cryptography`.** «Actualiza a `cryptography` 50.0.2, previa comprobación de que sigue siendo una versión adecuada y corregida.» «Ajusta el rango permitido para excluir versiones vulnerables.» Rango final (L8): «Quita el techo `<51` y deja `cryptography>=50.0.2`.» «Comprueba compatibilidad con Python 3.12 y 3.14.» «Ejecuta las pruebas completas del backend y las E2E relevantes.»
- **S10 — `pip-audit` en el `.venv`.** «Puedes instalar `pip-audit` directamente en el `.venv` existente.» «Ejecútalo sobre las dependencias efectivamente instaladas.» «Registra las versiones auditadas, los resultados y los posibles hallazgos pendientes.» «Distingue los problemas reales de los falsos positivos o vulnerabilidades que no afectan al uso actual.» «Valora si conviene incorporarlo a `requirements-dev.txt` en la tarea posterior de automatización, pero no amplíes ahora el alcance.»
- **S12 — P8, auditoría automática (L19).** «Implementa un workflow independiente para:» «Ejecutar `pip-audit` sobre las dependencias Python fijadas en `backend/constraints.txt`.» «Ejecutar `npm audit` sobre las dependencias del frontend, distinguiendo producción y desarrollo.» «Utilizar versiones controladas de las herramientas de auditoría.» «Permitir ejecución manual y periódica.» «Presentar resultados comprensibles, con las vulnerabilidades y paquetes afectados.» «Evitar que los PR ajenos a dependencias queden bloqueados por nuevas vulnerabilidades detectadas externamente o problemas temporales de los servicios de auditoría.» «Comprueba que el workflow detecta realmente las vulnerabilidades y no devuelve falsos resultados satisfactorios cuando falla una herramienta o no se analizan dependencias.» «No añadas `pip-audit` a `requirements-dev.txt` ni modifiques las 24 restricciones de H4 para incluir sus dependencias.» «Mantén separada P7 (alertas de Dependabot)». «No amplíes el alcance a actualizaciones de dependencias, hashes ni otros pendientes.»
- **S13 — P9 y P11 (L27).** «Me interesa tener ahora cerrado P9 y P11. Pytest se quitó y nos quedamos con unittest pip-audit se ha usado en el hardening, pero de momento ya no es necesario.» Decisión de P11: «3.12+3.14 y Node 24»: el job `python` de la CI prueba Python 3.12 (mínimo) y 3.14; Node 24 pasa a ser la única referencia mediante `frontend/.nvmrc`, que usan la CI y el README, y el mínimo sube de 22 a 24.
- **S11 — Revisión y CI.** «Solicita una revisión independiente centrada en seguridad, compatibilidad con las versiones de Python utilizadas, cobertura de pruebas y posibles regresiones.» «Comprueba que Ruff no introduce avisos nuevos y que la CI termina correctamente.» Límites: «No implementes todavía H4 ni H5.» «Puedes subir y actualizar la rama remota para ejecutar CI, pero **no la integres en `main` sin mi aprobación**.»

## Tasks

Auditoría:

- [x] A1 — S1, S2, S3, S5: diagnóstico en `docs/auditoria-dependencias.md` y referencia en `docs/pendiente.md`. Ruta: inline. Commit: el de «add dependency and supply-chain audit».
- [x] A2 — S4: esta propuesta de tareas. Ruta: inline. Mismo commit.
- [x] A3 — S6: revisión independiente del diagnóstico y del plan. Ruta: un revisor independiente de solo lectura (L3). La revisión nativa de gentle-ai también aprobó el commit, pero solo con comprobaciones estructurales. Correcciones en el commit «apply independent review».

Plan de endurecimiento (**aprobado en L4**; cada rama se integra solo con la aprobación del usuario). Cada bloque es una funcionalidad con su propia rama desde `main`, para respetar «una funcionalidad por rama». H/R remiten a los hallazgos de la auditoría.

**Correcciones urgentes: rama `fix/cryptography-50`** (P2 es la red de seguridad de P3; en la misma rama, un commit cada uno).

- [x] ~~P1 — Prueba de compatibilidad del formato `.pwc` (H3).~~ **Retirada** por S7 (L4): no hay sesiones `.pwc` de 46.0.7 que conservar ni requisito de compatibilidad histórica. Se mantienen las pruebas de ida y vuelta, contraseña incorrecta, manipulación y límites existentes.
- [x] P2 — Que las pruebas de cifrado y API no se salten en silencio (H2). Commit `9fcb31f` (L5). Prioridad: urgente, previa a P3. Depende de: nada. Ruta: inline.
  - Archivos: `tests/test_sessions.py`, `tests/test_session_limits.py`, `tests/test_api.py` y una prueba nueva, `tests/test_required_dependencies.py`.
  - Aceptación: sin `try/except ImportError` ni `skipUnless` por dependencias obligatorias. La prueba nueva carga cada módulo afectado en un subproceso con una dependencia obligatoria bloqueada (`sys.modules[...] = None`) y exige errores y cero saltos. RED antes del cambio, GREEN después. Suite sin pruebas saltadas.
  - Pruebas: la prueba nueva y la suite completa.
  - Regresión: quien ejecute las pruebas sin instalar `requirements-dev.txt` verá errores en lugar de saltos. Es el comportamiento buscado.
  - Revisión independiente: con P3 (S11).
- [x] P3 — `cryptography>=50.0.2`, sin techo (H1). Commits `1e3775d` (L5) y el de «drop the cryptography upper bound» (L8); CI con Python 3.12 en L6 y L8. Prioridad: urgente. Depende de: P2. Ruta: inline.
  - Archivos: `backend/requirements.txt`.
  - Aceptación: 50.0.2 sigue siendo la última versión y OSV no tiene avisos para ella. `pip-audit` sin avisos para `cryptography`. Suite, `ruff check .` y E2E en verde en local (Python 3.14) y en CI (3.12). Sin cambios en `sessions.py` ni en el formato `.pwc`.
  - Pruebas: suite completa, E2E y CI.
  - Regresión: wheels con OpenSSL 4.0.x. Desde 49.0.0 no hay wheels de Windows de 32 bits ni de macOS x86_64: un Mac Intel tendría que compilar con Rust. Documentarlo si afecta a alguien.
  - Revisión independiente: **sí** (seguridad y dependencias: elementos 2 y 5 de alto riesgo).
- [x] P3b — `pip-audit` sobre el `.venv`, antes y después de P3 (S10). Resultados en L5. Ruta: inline. Sin cambios en `requirements*.txt`; los resultados se registran en el Log y en la auditoría.

**Mantenimiento: rama `chore/reproducible-installs`.**

- [x] P4 — Restricciones de Python con todas las versiones fijadas y límites inferiores seguros (H4, R1). Commits `40a1c7c` y `ebb11e4` (CI), L12. Prioridad: alta. Depende de: P3 (para no fijar una `cryptography` vulnerable).
  - Archivos: `backend/constraints.txt` (nuevo), `backend/requirements.txt`, `backend/requirements-dev.txt`, `.github/workflows/tests.yml` (jobs `python` y `e2e`: `-c backend/constraints.txt`) y `README.md` (instalación, pruebas y cómo regenerar).
  - Aceptación:
    - `constraints.txt` fija con `==` todas las dependencias de `requirements-dev.txt` y sus transitivas. **Corregido en L11:** la versión inicial son exactamente las que instaló la CI de `main` (run `41650001412`, Linux con Python 3.12), sin `pytest` y sus dependencias, para no actualizar nada en esta rama. Para regenerarlo se usa `pip freeze` en un entorno limpio.
    - **Corregido en L12:** colorama solo la pedía `pytest` en Windows; `click` 8.5.0 no tiene dependencias. Al retirar `pytest`, el conjunto es idéntico en Linux y Windows y en Python 3.12 y 3.14, así que no hace falta ningún marcador de plataforma.
    - En la CI, un paso del job `python` falla si algún paquete instalado no está fijado en `constraints.txt` o tiene otra versión (L11). Las líneas `Successfully installed` del job `e2e` son un subconjunto.
    - Límite inferior `python-multipart>=0.0.31`. Ninguna versión conocida de FastAPI ni de uvicorn exige `starlette>=1.3.1` ni `h11>=0.16` (FastAPI 0.162.0 pide `starlette>=0.46.0`; uvicorn, `h11>=0.8`), así que esos mínimos se fijan en `constraints.txt`.
  - Pruebas: suite, Ruff, build y E2E en CI. Instalación en limpio en local con `-c` y Python 3.14.
  - Regresión:
    - Un `pip install` sin `-c` sigue funcionando con los rangos. Si los rangos y las restricciones discrepan, pip falla con un error explícito.
    - Las restricciones generadas con 3.12 se usan también con 3.14 en local. Hoy funciona, pero una regeneración futura podría fijar un paquete sin wheel para cp314.
  - Revisión independiente: **sí** (CI y dependencias: elemento 5).
- [x] P5 — README con `npm ci` (H7). Commit `40a1c7c`, L12. Prioridad: media. Depende de: nada.
  - Archivos: `README.md`.
  - Aceptación: la instalación usa `npm ci` y el README explica cuándo regenerar el lockfile (`npm install` deliberado).
  - Pruebas: ninguna ejecutable; revisar el texto.
  - Regresión: ninguna.
  - Revisión independiente: no.
- [x] P6 — Retirar `pytest` (H8). Commit `522dc94`, L12. **Decidido en L11:** se retira y `unittest` queda como único ejecutor oficial, en local y en CI. Prioridad: baja.
  - Archivos: `backend/requirements-dev.txt`, `backend/constraints.txt` y `README.md` (si hace falta).
  - Aceptación: ninguna prueba, configuración ni herramienta depende de `pytest`; se retira de `requirements-dev.txt` y no entra en las restricciones; la CI sigue en verde con `unittest`. Las pruebas existentes no cambian.
  - Pruebas: suite.
  - Regresión: el IDE configurado con pytest dejaría de encontrarlo.
  - Revisión independiente: no.

**Mantenimiento: detección, rama `ci/dependency-audit`.**

- [x] P7 — Activar las alertas de Dependabot (H5). Activadas por el usuario; `vulnerability-alerts` devuelve 204 desde el 2026-11-03 (L23). Prioridad: alta e inmediata. Depende de: nada.
  - Archivos: ninguno. Es un ajuste del repositorio que **solo puede activar el propietario** (Settings → Advanced Security → Dependabot alerts).
  - Aceptación: `gh api repos/eliseumarmon/password-checker/vulnerability-alerts -i` devuelve 204.
  - No verificado: que GitHub detecte `cryptography` con requisitos que solo tienen rangos. Para Python, las alertas probablemente solo cubran dependencias directas, así que la red real es P8.
  - Pruebas y regresión: ninguna.
  - Revisión independiente: no.
- [x] P8 — Workflow de auditoría separado (H5). Commits `26b1553`, `334b631`, `28c138e`, `48a3b85` (L20), `2686219` (L21) y el de L22. Integrada en `cf3f089`; run manual en verde en `main` (L24). Prioridad: media. Depende de: P3 y P4. **Ajustado en L19 (S12):**
  - Además de `schedule`, `workflow_dispatch` y `pull_request`, se dispara con `push` limitado a los mismos `paths`, para poder verificarlo antes de integrar.
  - `pip-audit` y sus dependencias van fijados en `.github/audit-requirements.txt`.
  - Un script versionado (`.github/scripts/dependency_audit.py`), con pruebas unitarias, interpreta los JSON. Falla ante vulnerabilidades, ante un error de la herramienta y cuando se analizan menos paquetes de los fijados.
  - El run manual en verde se comprueba después de integrar.
  - Archivos: `.github/workflows/dependency-audit.yml` (nuevo) y la sección de excepciones de `docs/auditoria-dependencias.md`.
  - Diseño: `schedule` semanal, `workflow_dispatch` y `pull_request` con `paths` de los archivos de dependencias. `pip-audit==2.10.1` (instalado solo en ese job) con `-r backend/constraints.txt --no-deps --disable-pip`. `npm audit` (basta con el lockfile), y `npm ci --ignore-scripts --no-fund` seguido de `npm audit signatures`, que necesita los paquetes instalados. `permissions: contents: read`.
  - Limitaciones (documentarlas en la auditoría):
    - GitHub desactiva el cron tras 60 días sin actividad.
    - El aviso de un fallo programado solo lo recibe quien modificó el cron por última vez.
    - Sin protección de `main`, el job informa pero no bloquea. Exigirlo sería una medida aparte, que decide el propietario.
  - Aceptación: un run manual en verde. Con una versión vulnerable en una rama de prueba (sin integrar), el job falla. Un PR que no toca dependencias no lo ejecuta. Cada `--ignore-vuln` tiene su justificación y su fecha en la auditoría.
  - Pruebas: los runs de CI descritos.
  - Regresión: falsos positivos en los runs programados (gestionados con excepciones justificadas). `tests.yml` no cambia.
  - Revisión independiente: **sí** (CI: elemento 5).
- [x] P9 — Migrar las pruebas de API de `httpx` a `httpx2` (H6). Commit `810db17` (L28). **Adelantada por el usuario (L27, S13).** Rama `chore/httpx2`, encadenada sobre `docs/close-dependency-hardening`. Depende de: P4.
  - Archivos: `backend/requirements-dev.txt`, `backend/constraints.txt` y, si cambia la importación, `tests/test_api.py`.
  - Aceptación: sin `StarletteDeprecationWarning` en la CI y con la suite en verde. Procedencia de `httpx2` revisada de nuevo (sus archivos no tenían atestación PEP 740 el 2026-11-03).
  - Pruebas: suite.
  - Regresión: diferencias de comportamiento del cliente en `TestClient`.
  - Revisión independiente: no.

**Medidas opcionales** (cada una en su propia rama si se aprueba):

- [ ] P10 — Acciones de GitHub fijadas por SHA con comentario de versión, y `dependabot.yml` solo para `github-actions` (H9). Prioridad: baja. Archivos: `.github/workflows/*.yml`, `.github/dependabot.yml`. Aceptación: cada `uses:` apunta a un SHA de 40 caracteres que coincide con su etiqueta (`gh api repos/<acción>/git/ref/tags/<v>`), y la CI está en verde. Si se aprueba, se puede imponer activando `sha_pinning_required` en los permisos de Actions del repositorio (hoy `false`). Regresión: ninguna funcional. Revisión: sí (CI).
- [x] P11 — Alinear los entornos (H4). Commit `07e786d` (L29). **Decidido en L27 (S13):** matriz de Python 3.12 y 3.14 en el job `python`; Node 24 como única referencia mediante `frontend/.nvmrc`. Rama `ci/align-runtimes`, encadenada sobre `chore/httpx2`.
  - Archivos: `.github/workflows/tests.yml`, `.github/workflows/dependency-audit.yml`, `frontend/.nvmrc` (nuevo) y `README.md`.
  - Aceptación: la CI prueba Python 3.12 y 3.14 (unitarias, Ruff y comprobación de restricciones) y usa Node 24 desde `.nvmrc` en todos los jobs. El README documenta las versiones de referencia. Revisión: sí, porque toca la CI.
- [ ] P12 — Actualizaciones mayores del frontend (H10). **Vinculada a la Fase 1 del frontend (L26):**
  - `primevue` y `@primeuix/themes` no se actualizarán: la Fase 1 retira PrimeVue (decisión D1).
  - `vue-router`, que no se usa, también se retira en la Fase 1.
  - Quedan `pinia` 4, `vite` 8 y `typescript` 7. Siguen siendo opcionales y fuera de este plan: cada una, si se aborda, es una funcionalidad con su propio documento ODD y sus pruebas E2E.
- [ ] P13 — Bloqueo con hashes (uv con `--universal --generate-hashes`) si el modelo de amenazas crece con la bóveda persistente. Fuera de alcance por ahora.

Orden recomendado: P7 (inmediata, sin código) → P2 → P3 → P4, P5 → P8 → resto según la política de actualización. Previsión: P2-P3 unas 100 líneas, P4-P6 unas 80 más el archivo generado y P8 unas 60; cada rama por debajo de las ~400 líneas, con un PR por rama.

## Log

- **L1 (2026-11-03):** petición, literal:

  > Quiero realizar una **auditoría de dependencias y cadena de suministro de Password Checker**, antes de seguir ampliando sus funcionalidades.
  >
  > El objetivo es identificar riesgos, evaluar la reproducibilidad de las instalaciones y preparar un plan de endurecimiento. **En esta fase no debes modificar dependencias, configuración ni código.**
  >
  > ### 1. Inventario y diagnóstico
  >
  > Examina el estado real del repositorio, tanto backend (Python/FastAPI) como frontend (Vue/Vite):
  >
  > - Identifica dependencias directas, transitivas y de desarrollo.
  > - Ejecuta `pip-audit` y `npm audit`, distinguiendo dependencias de producción y desarrollo.
  > - Comprueba versiones instaladas, rangos permitidos y actualizaciones disponibles.
  > - Examina `requirements.txt`, `requirements-dev.txt`, `package.json` y los archivos de bloqueo existentes.
  > - Determina si las instalaciones son reproducibles entre desarrollo y CI.
  > - Identifica dependencias abandonadas, poco mantenidas o de procedencia cuestionable.
  > - Revisa scripts de instalación, dependencias de build y acciones de GitHub Actions.
  >
  > No instales ni ejecutes herramientas adicionales sin valorar antes su procedencia y seguridad.
  >
  > ### 2. Análisis de riesgos
  >
  > Para cada hallazgo, documenta:
  >
  > - Dependencia o componente afectado.
  > - Versión instalada y versiones vulnerables, cuando corresponda.
  > - Vulnerabilidad identificada y referencias (CVE/GHSA).
  > - Severidad y explotabilidad real en Password Checker.
  > - Si afecta a producción, desarrollo o CI.
  > - Posible impacto sobre credenciales, TOTP, cifrado, sesiones `.pwc` y archivos importados.
  > - Corrección recomendada y riesgos de compatibilidad.
  >
  > No equipares automáticamente la severidad publicada de una vulnerabilidad con su riesgo real en nuestra aplicación.
  >
  > Distingue los hallazgos confirmados, los riesgos potenciales y las cuestiones que no hayan podido verificarse.
  >
  > ### 3. Reproducibilidad y política de versiones
  >
  > Analiza las alternativas para:
  >
  > - Fijar versiones de dependencias Python y sus transitivas sin dificultar el mantenimiento.
  > - Mantener instalaciones reproducibles con `npm ci`.
  > - Separar correctamente dependencias de producción, desarrollo y pruebas.
  > - Establecer una política razonable de actualización.
  > - Detectar vulnerabilidades nuevas mediante CI sin introducir fallos por resultados no verificados o cambios externos inesperados.
  >
  > No implementes todavía ninguna alternativa. Recomienda la más adecuada para el tamaño y arquitectura actuales del proyecto, evitando complejidad innecesaria.
  >
  > ### 4. Plan de actuación
  >
  > Prepara un plan siguiendo el flujo ODD existente, con tareas pequeñas, independientes y verificables.
  >
  > Para cada tarea indica:
  >
  > - Prioridad según riesgo e impacto.
  > - Dependencias entre tareas.
  > - Archivos previsiblemente afectados.
  > - Criterios de aceptación verificables.
  > - Pruebas necesarias.
  > - Riesgos de regresión.
  > - Necesidad de revisión independiente.
  >
  > Distingue entre correcciones urgentes, mejoras de mantenimiento y medidas opcionales.
  >
  > ### 5. Límites de esta auditoría
  >
  > - No actualices paquetes.
  > - No modifiques el código ni la configuración de CI.
  > - No introduzcas nuevas herramientas permanentes.
  > - No alteres el cifrado, el formato `.pwc` ni las reglas de consolidación.
  > - No recuperes la CLI eliminada.
  > - No utilices credenciales reales.
  > - No confundas esta auditoría de dependencias con una auditoría completa de seguridad de la aplicación.
  >
  > Puedes utilizar herramientas de análisis en modo lectura. Si alguna instalación temporal es imprescindible, justifícala antes.
  >
  > ### 6. Entrega
  >
  > Presenta primero un resumen ejecutivo de los hallazgos y sus prioridades.
  >
  > Después, crea un documento de auditoría y una propuesta de tareas siguiendo la organización documental existente. No dupliques información en `docs/pendiente.md`; utiliza referencias a los documentos específicos.
  >
  > Solicita una **revisión independiente del diagnóstico y del plan**, centrada en seguridad, exactitud de los hallazgos, proporcionalidad de las soluciones y posibles omisiones.
  >
  > No implementes ninguna corrección, no integres cambios en `main` y no modifiques dependencias hasta que apruebe el plan.
  >
  > **Importante:** no quiero una lista genérica de buenas prácticas. Quiero un diagnóstico basado en el código, las dependencias y la configuración reales de Password Checker, con evidencias reproducibles y un plan proporcionado a los riesgos encontrados.

- **L2 (2026-11-03):** A1-A2.
  - **Diagnóstico:** solo con herramientas ya instaladas y APIs públicas de lectura (OSV, PyPI, registro npm, `gh api`).
  - **`pip-audit`:** no se instaló. Su fuente de datos (OSV) se consultó directamente con las versiones exactas, y la instalación temporal queda pendiente de que el usuario la autorice.
  - **Resultados:** `npm audit` 0/0 y 119 firmas verificadas. En Python, solo `cryptography` 46.0.7 tiene avisos (4: GHSA-537c-gmf6-5ccf, GHSA-g6cj-pr64-35w5, GHSA-jwv3-5hgf-82ww y GHSA-m2h6-j472-rp4c), ninguno alcanzable porque solo se usa `AESGCM`. Su rango `<47` excluye todas las versiones corregidas.
  - **Otros hallazgos:** pruebas que se saltan en silencio, ninguna prueba de compatibilidad de `.pwc`, ningún bloqueo de Python, Python y Node distintos en local y CI, alertas de Dependabot desactivadas en un repositorio público, `httpx` obsoleto para `TestClient` y límites inferiores que admiten versiones vulnerables de `python-multipart`, Starlette y h11.
  - **Sin cambios:** dependencias, código y CI. Suite local: 138 OK.
  - **Ruta:** inline; solo documentación, sin escritores delegados.
  - **Siguiente paso:** A3.
- **L3 (2026-11-03):** A3, revisión independiente.
  - **Revisión nativa de gentle-ai:** con lentes la rechazó («an agent lens selection needs a medium or high risk review»), porque el commit es pasivo (`non_executable_only`). El START indicado por el hook la cerró como `approved` sin lentes y quedó reconocida (`authority: burned`). Solo hizo comprobaciones estructurales.
  - **Revisor independiente:** de solo lectura y sin mis conclusiones como premisa. Volvió a comprobar versiones, avisos OSV, el aviso de OpenSSL, el registro de CI, el uso de la API criptográfica, el alcance de `origin_guard` y el estado de Dependabot: todo confirmado. Ningún hallazgo bloqueante.
  - **Correcciones aplicadas:**
    - P8: `npm audit signatures` necesita `npm ci` antes; reproducido: `found no dependencies to audit` solo con el lockfile.
    - P7: la aceptación queda solo en el 204; que GitHub detecte `cryptography` con rangos no está verificado.
    - P4: la línea de `e2e` es un subconjunto; colorama se añade a mano; ninguna versión de FastAPI ni de uvicorn exige `starlette>=1.3.1` ni `h11>=0.16`, así que van en `constraints.txt`; riesgo de wheels cp314.
    - R1: se añade el límite inferior de `cryptography`.
    - H1: «urgente por el rango, no por los avisos».
    - `main` sin protección y `sha_pinning_required: false` se incorporan a la auditoría y a P8 y P10.
    - P1: el vector se genera con sal y nonce fijos sin tocar `encrypt_session`; la comprobación manual incluye el `AAD`.
  - **Sin verificar:** el grafo de dependencias y los archivos de restricciones, las sumas de Playwright, `cryptography` 50.0.2 en 3.14 y 3.12, y el exploit UNC.
  - **Siguiente paso:** aprobación del plan por el usuario.
- **L4 (2026-11-03):** aprobación y ajustes, literal:

  > Apruebo el plan de auditoría de dependencias. Puedes comenzar por la rama `fix/cryptography-50`, siguiendo el flujo ODD y las revisiones independientes habituales.
  >
  > ### Aclaraciones y ajustes
  >
  > **1. No necesitamos compatibilidad histórica con cryptography 46.0.7**
  >
  > Actualmente no existen sesiones `.pwc` que debamos conservar generadas con esa versión. Ya habíamos decidido que, en esta fase del proyecto, no era necesario garantizar compatibilidad hacia atrás.
  >
  > Por tanto:
  > - Elimina H3 del alcance de esta tarea como requisito de compatibilidad histórica.
  > - No crees fixtures históricas ni pruebas de migración entre versiones de `cryptography`.
  > - Mantén las pruebas normales de cifrado, descifrado, integridad, contraseñas incorrectas y manipulación de archivos.
  > - No cambies innecesariamente el formato `.pwc` ni los parámetros criptográficos.
  >
  > **2. Corrige H2 antes de actualizar**
  >
  > Las pruebas obligatorias de cifrado y API no deben saltarse silenciosamente cuando faltan dependencias o se producen errores de importación.
  >
  > Deben fallar explícitamente para evitar falsos positivos en CI.
  >
  > Añade las pruebas necesarias para verificar este comportamiento, sin introducir complejidad innecesaria.
  >
  > **3. Actualiza cryptography**
  >
  > - Actualiza a `cryptography` 50.0.2, previa comprobación de que sigue siendo una versión adecuada y corregida.
  > - Ajusta el rango permitido para excluir versiones vulnerables.
  > - Comprueba compatibilidad con Python 3.12 y 3.14.
  > - Ejecuta las pruebas completas del backend y las E2E relevantes.
  >
  > **4. Instala pip-audit en el entorno virtual del proyecto**
  >
  > Puedes instalar `pip-audit` directamente en el `.venv` existente. No es necesario crear un entorno temporal aislado.
  >
  > - Ejecútalo sobre las dependencias efectivamente instaladas.
  > - Registra las versiones auditadas, los resultados y los posibles hallazgos pendientes.
  > - Distingue los problemas reales de los falsos positivos o vulnerabilidades que no afectan al uso actual.
  > - Valora si conviene incorporarlo a `requirements-dev.txt` en la tarea posterior de automatización, pero no amplíes ahora el alcance.
  >
  > **5. Revisión independiente**
  >
  > Solicita una revisión independiente centrada en seguridad, compatibilidad con las versiones de Python utilizadas, cobertura de pruebas y posibles regresiones.
  >
  > Comprueba que Ruff no introduce avisos nuevos y que la CI termina correctamente.
  >
  > ### Límites
  >
  > - Respeta el alcance de la tarea aprobada.
  > - No implementes todavía H4 ni H5.
  > - No introduzcas cambios en la arquitectura de la futura bóveda.
  > - No recuperes la CLI eliminada.
  > - Utiliza únicamente credenciales ficticias en las pruebas.
  > - Registra los resultados y decisiones en la documentación ODD existente.
  >
  > Puedes subir y actualizar la rama remota para ejecutar CI, pero **no la integres en `main` sin mi aprobación**.
  >
  > Una vez completada y revisada, presenta los resultados y cualquier hallazgo relevante antes de integrar.

  Cambios derivados: S7-S11 añadidos; P1 retirada; P2 incluye una prueba versionada; P3 depende solo de P2; P3b nueva. Rama `fix/cryptography-50` encadenada sobre `docs/dependency-audit`, porque el documento ODD solo existe ahí.
- **L5 (2026-11-03):** P2, P3 y P3b en local (Python 3.14.7, Windows).
  - **P2 (S8):** `tests/test_required_dependencies.py` descubre cada módulo, como la CI, en un subproceso con una dependencia obligatoria bloqueada (`sys.modules[...] = None`), y exige errores y cero saltos.
    - **RED:** 4 fallos. Sin `cryptography` o sin `argon2`, `test_sessions` daba 5 saltos; sin `cryptography`, `test_session_limits` daba 2; sin `fastapi`, `test_api` daba 29.
    - **`httpx`:** ya fallaba de forma visible, porque Starlette lanza `RuntimeError` y no `ImportError`. Se mantiene como caso de regresión.
    - El primer probe usaba `loadTestsFromName`, que solo convierte `ImportError` en un error de prueba; se cambió a `discover` para reproducir la CI.
    - **GREEN:** se retiran las guardas `try/except ImportError` y `skipUnless` de `test_sessions.py`, `test_session_limits.py` y `test_api.py`. Suite 139 OK sin saltos; Ruff sin avisos.
    - Las pruebas de ida y vuelta, contraseña incorrecta, manipulación y límites no cambian (S7).
  - **P3b, antes (S10):** `pip-audit` 2.10.1 instalado en `.venv` junto con 22 dependencias propias (requests, rich, cyclonedx-python-lib, CacheControl, etc.). `pip-audit` sobre el entorno instalado: 54 paquetes, ninguno omitido. Solo `cryptography` 46.0.7 tiene avisos: 7 entradas que son los 4 avisos de H1 con sus alias PYSEC y GHSA, idénticos a lo obtenido con OSV. Ningún falso positivo; ninguno era alcanzable (H1).
  - **P3 (S9):**
    - 50.0.2 es la última versión publicada, no está retirada y OSV no tiene avisos para 50.0.0 ni para 50.0.2. Sus wheels llevan OpenSSL 4.0.3.
    - Rango `cryptography>=50.0.2,<51`. `pip install -r backend/requirements-dev.txt` la actualizó y `pip check` no encuentra problemas.
    - pip dejó en `site-packages/~ryptography` el `_rust.pyd` antiguo, probablemente bloqueado por un proceso Python abierto; se inspeccionó y se borró.
    - Python 3.14.7 con OpenSSL 4.0.3: suite 139 OK, Ruff sin avisos y E2E 88/88. Las E2E incluyen guardar y abrir un `.pwc` y usar una contraseña incorrecta.
    - `sessions.py`, el formato `.pwc` y los parámetros criptográficos no cambian.
  - **P3b, después:** 54 paquetes, «No known vulnerabilities found».
  - **¿`pip-audit` en `requirements-dev.txt`? Recomendación: no.**
    - Añadiría 22 paquetes a cada instalación de desarrollo y de CI.
    - Al auditar el entorno donde está instalado, se audita también a sí mismo y añade ruido.
    - Para P8 basta con instalar `pip-audit==2.10.1` solo en el job de auditoría y auditar `constraints.txt` con `--no-deps --disable-pip`.
    - Sigue instalado en el `.venv` local, sin declararse en ningún requisito.
  - **Riesgo detectado sobre la aprobación:** el techo `<51` reproduce el problema estructural de H1. `cryptography` no publica correcciones para versiones mayores anteriores y en 2026 ha sacado una mayor al mes (47.0.0 el 2026-04-24 y 50.0.0 el 2026-07-31). Se mantiene el rango aprobado; la detección (P7 y P8) debe avisar cuando una corrección solo exista en la 51 o posterior. Decisión para el usuario: quitar el techo o mantenerlo.
- **L6 (2026-11-03):** CI y revisión.
  - **CI:** run `41646649195` sobre `155dcce`. Los jobs `python`, `frontend` y `e2e` terminan en verde con Python 3.12.15 y `cryptography` 50.0.2 instalada en `python` y en `e2e`. Unitarias: 139 OK, sin saltos. El paso «Lint with Ruff» pasa. E2E: 88 superadas.
  - **Compatibilidad:** Python 3.12 verificado en CI y 3.14 en local (L5).
  - **Evaluación de riesgo:** la nativa daba `medium` (`under_budget`) y se escaló a `high` con el elemento 5 (actualización mayor de la dependencia que cifra los `.pwc`).
  - **Revisión nativa:** lentes de riesgo y fiabilidad sobre `67a4fbf..155dcce`, con consentimiento del usuario («Review this change»). Aprobada y reconocida (`review-cbba2b329493fdea`, `authority: burned`).
    - **Riesgo:** sin hallazgos. Confirma que el techo `<51` es un riesgo de mantenimiento ya registrado y no una vulnerabilidad alcanzable, que el probe no tiene superficie de inyección y que las credenciales son ficticias.
    - **Fiabilidad:** una sugerencia no bloqueante (`R3-error-attribution`): la prueba no comprueba que el error se deba al paquete bloqueado.
  - **Aplicada:** el probe devuelve el texto de cada error y la prueba exige que todos mencionen el paquete bloqueado. Comprobado a mano que discrimina: con `argon2` bloqueado, el error menciona `argon2` y no `cryptography`. Suite 139 OK y Ruff sin avisos.
  - **Pendiente:** integrar en `main` (cuando el usuario lo apruebe, después de `docs/dependency-audit`), decidir sobre el techo `<51`, y reiniciar cualquier proceso de la aplicación abierto durante la actualización.
- **L7 (2026-11-03):** revisión de la rama completa y ajustes finales.
  - **CI:** run `41647236624` sobre `89f7c1d`, en verde en `python`, `frontend` y `e2e`.
  - **Revisión de la rama:** el hook de gentle-ai pidió revisar toda la rama respecto a `main` (`review-83395f75c6ba9063`, lente de fiabilidad). El usuario aceptó («Review this change»), y se aprobó y reconoció (`authority: burned`). Dos sugerencias no bloqueantes, aplicadas:
    - **`R3-error-attribution-substring`:** buscar el nombre del paquete en todo el traceback era una comprobación débil. Ahora la excepción final de cada error debe ser del tipo esperado y nombrar el paquete como palabra completa: `ModuleNotFoundError` con `cryptography`, `argon2` o `fastapi`; `RuntimeError` con `httpx2` en el caso de `httpx`. Al aplicarlo se vio que el mensaje real depende del `import` (`No module named 'cryptography.exceptions'; 'cryptography' is not a package`) y que el de Starlette ocupa varias líneas, así que se toma la última línea con forma `<Tipo>Error: `. Con `argon2` bloqueado, la excepción final no nombra `cryptography`.
    - **`R3-plan-status-inconsistent`:** `docs/pendiente.md`, el inicio de la auditoría y el bloque de tareas decían «pendiente de aprobación» o «no está aprobado»; ahora reflejan la aprobación de L4.
  - **Verificación:** suite 139 OK y Ruff sin avisos.
- **L8 (2026-11-03):** decisión sobre el techo e integración, literal:

  > Quita el techo `<51` y deja `cryptography>=50.0.2`.
  >
  > La política de versiones de `cryptography` incrementa el número mayor frecuentemente sin implicar necesariamente incompatibilidades. No queremos volver a bloquear futuras correcciones de seguridad por un límite arbitrario.
  >
  > La reproducibilidad se abordará en H4 mediante `constraints.txt`, y la detección de vulnerabilidades en H5.
  >
  > Tras el cambio:
  > - Ejecuta las pruebas correspondientes.
  > - Comprueba que Ruff y CI siguen en verde.
  > - Registra la decisión en el plan existente.
  > - Solicita revisión independiente si corresponde.
  >
  > Después, integra primero `docs/dependency-audit` en `main` y verifica la integración. A continuación, integra `fix/cryptography-50`, comprobando que contiene únicamente los cambios aprobados y que la CI de `main` queda en verde.
  >
  > No empieces H4 todavía.

  - **Evidencia de la premisa:** 47.0.0, 48.0.0, 49.0.0 y 50.0.0 se publicaron entre el 2026-04-24 y el 2026-07-31. Sus rupturas (OpenSSL 1.1, Python 3.8, wheels de 32 bits y de macOS x86_64, curvas binarias, X.509 y DH) no afectan a `AESGCM`, `InvalidTag` ni Argon2id.
  - **Cambio:** `backend/requirements.txt` pasa a `cryptography>=50.0.2`. La auditoría (H1) registra la corrección aplicada.
  - **Riesgo aceptado:** una versión 51 o posterior podría romper la API usada. Hasta H4, cada instalación nueva tomará la última versión publicada. La CI (unitarias de `.pwc` y E2E) es la red frente a esa rotura, y P2 garantiza que un fallo de importación no se convierta en un salto.
  - **Local:** `pip check` sin problemas, suite 139 OK y Ruff sin avisos.
- **L9 (2026-11-03):** integraciones en `main`, ambas con `--no-ff` y aprobadas por el usuario en L8.
  - **`9fbd786` — Merge `docs/dependency-audit`:** solo los 3 documentos (`docs/auditoria-dependencias.md`, `docs/pendiente.md` y este plan). En local: suite y Ruff en verde. CI de `main`: run `41649641545`, en verde en `python`, `frontend` y `e2e`.
  - **`2bd5a23` — Merge `fix/cryptography-50`:** comprobado antes de integrar que el diff con `main` solo contenía lo aprobado: 8 archivos (`requirements.txt`, las guardas retiradas en tres pruebas, `tests/test_required_dependencies.py` y la documentación), sin código de producción ni CI. En local: suite 139 OK, Ruff sin avisos y `pip check` limpio. CI de `main`: run `41650001412`, en verde con Python 3.12.15, 139 pruebas, Ruff, 88 E2E y `cryptography` 50.0.2.
  - **Ramas borradas:** después de comprobar que no tenían commits fuera de `main`, se eliminaron `docs/dependency-audit` (solo existía en local) y `fix/cryptography-50` (en local y en remoto).
- **L10 (2026-11-03):** H4, petición literal:

  > Continúa con **H4 — Instalaciones reproducibles**, siguiendo el plan aprobado en `odd/tasks/dependency-hardening.md` y el flujo ODD habitual.
  >
  > ### 1. Preparación
  >
  > - Parte de `main` actualizado y crea la rama `chore/reproducible-installs`.
  > - Registra como L9 las integraciones anteriores (`9fbd786` y `2bd5a23`) y sus verificaciones.
  > - Elimina las ramas `docs/dependency-audit` y `fix/cryptography-50`, tanto locales como remotas, después de verificar que están completamente integradas.
  > - Revisa las especificaciones y criterios de aceptación de H4 antes de implementar. Si detectas contradicciones o decisiones pendientes, informa antes de continuar.
  >
  > ### 2. Dependencias reproducibles de Python
  >
  > Implementa la estrategia de `backend/constraints.txt` acordada en el plan.
  >
  > - Fija las versiones de las dependencias directas y transitivas.
  > - Conserva `backend/requirements.txt` como declaración de dependencias compatibles, incluida `cryptography>=50.0.2`.
  > - No introduzcas nuevas herramientas permanentes si no son necesarias.
  > - Asegúrate de que las instalaciones locales y de CI utilizan las restricciones.
  > - Revisa los jobs Python y E2E de GitHub Actions.
  > - Comprueba la resolución e instalación con Python 3.12 y 3.14.
  > - Si existen diferencias entre versiones de Python o plataformas, utiliza una solución explícita y mantenible. No fuerces una falsa reproducibilidad.
  > - Documenta el procedimiento para actualizar las restricciones sin convertirlas en un bloqueo indefinido de actualizaciones de seguridad.
  >
  > ### 3. Frontend
  >
  > - Conserva `package-lock.json` como fuente de versiones resueltas.
  > - Sustituye `npm install` por `npm ci` en las instrucciones destinadas a instalaciones reproducibles.
  > - Comprueba que el desarrollo local y CI utilizan correctamente el lockfile.
  > - No actualices dependencias del frontend salvo que sea imprescindible para completar H4.
  >
  > ### 4. Pruebas y verificación
  >
  > Comprueba como mínimo:
  >
  > - Instalación limpia de dependencias Python respetando las restricciones.
  > - Compatibilidad con Python 3.12 y 3.14.
  > - `pip check` sin conflictos.
  > - Las 139 pruebas del backend.
  > - Ruff sin avisos.
  > - Typecheck y build del frontend.
  > - Las 88 pruebas E2E.
  > - Ejecución correcta de CI.
  >
  > Usa esos recuentos únicamente como referencia inicial; si han cambiado legítimamente, documenta la diferencia.
  >
  > Solicita una revisión independiente centrada en reproducibilidad, mantenimiento, seguridad de dependencias y posibles regresiones.
  >
  > ### 5. Límites
  >
  > - No implementes todavía P8 ni el workflow de auditoría.
  > - No introduzcas hashes ni gestores de dependencias adicionales sin una justificación clara.
  > - No cambies el código de producción, el cifrado ni el formato `.pwc`.
  > - No recuperes la CLI eliminada.
  > - No aproveches esta rama para actualizar dependencias ajenas a H4.
  > - Respeta la organización documental actual y evita duplicar información.
  >
  > ### 6. Entrega
  >
  > Documenta las decisiones técnicas, los resultados de las pruebas y cualquier riesgo residual en el plan existente.
  >
  > Puedes subir la rama para ejecutar CI, pero **no la integres en `main` sin mi aprobación**.
  >
  > Cuando H4 esté terminada y revisada, presenta un resumen de los cambios, las verificaciones realizadas y las posibles observaciones pendientes.

  El usuario indica además que activará las alertas de Dependabot (P7). A 2026-11-03, `vulnerability-alerts` sigue devolviendo 404.
  - **Revisión de las specs de H4 antes de implementar:**
    - **Discrepancia 1 (colorama):** en Windows, colorama la requieren tanto `click` (`platform_system == "Windows"`) como `pytest` (`sys_platform == "win32"`), no solo `click`. El resto de marcadores del cierre de dependencias no cambia el conjunto entre 3.12 y 3.14: `exceptiongroup` y `tomli` solo se instalan con Python < 3.11; `typing_extensions` se instala en ambas versiones (anyio la pide en < 3.15); `argon2-cffi-bindings` pide `cffi>=1.0.1` en < 3.14 y `cffi>=2` en ≥ 3.14, y `cffi` 2.1.1 cumple las dos.
    - **Discrepancia 2 (Python 3.12 en local):** P4 dice «se genera con `pip freeze` en un entorno limpio con Python 3.12», pero en esta máquina solo hay Python 3.14 y 3.11 (`py -0`). En 3.12 solo se puede verificar en la CI (Linux).
    - **Decisión pendiente (P6):** si `pytest` se conserva, `pytest` y sus dependencias (iniconfig, packaging, pluggy, Pygments y colorama en Windows) entran en `constraints.txt`.
  - Implementación en pausa hasta la respuesta del usuario.
- **L11 (2026-11-03):** decisión sobre `pytest`, literal:

  > Retira `pytest` de `requirements-dev.txt` y mantén `unittest` como único ejecutor oficial de pruebas, tanto en local como en CI.
  >
  > Antes, comprueba que ninguna prueba, configuración o herramienta del proyecto depende realmente de `pytest`.
  >
  > Actualiza las restricciones y la documentación correspondiente, sin modificar innecesariamente las pruebas existentes.
  >
  > Continúa con H4 según el plan aprobado, incluyendo la verificación de instalaciones reproducibles en Python 3.12 y 3.14.
  >
  > Mantén el flujo de revisión independiente y no integres en `main` sin mi aprobación.

  - **Ninguna dependencia de `pytest` (comprobado):**
    - `git grep` solo encuentra `pytest` en `backend/requirements-dev.txt`, en `.pytest_cache/` de `.gitignore` y en el comentario `# flake8-pytest-style` de `ruff.toml`.
    - Las reglas `PT` de `ruff.toml` son análisis estático: no necesitan `pytest` instalado y forman parte del conjunto por defecto de Ruff 0.17.3 que reproduce `select`, así que se mantienen.
    - No hay `conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg` ni `tox.ini`.
    - Todas las clases de prueba heredan de `unittest.TestCase`, sin fixtures de pytest.
    - `.vscode/settings.json` (sin versionar) no configura ningún ejecutor de pruebas.
  - **Decisiones de implementación** (anunciadas al usuario antes de L11 y no objetadas):
    - Las versiones iniciales de `constraints.txt` son las de la CI de `main`, sin actualizar nada.
    - Python 3.14 se verifica con una instalación limpia en Windows; Python 3.12, en la CI (Linux), porque no está instalado en local.
    - Un paso de CI comprueba que todo lo instalado está fijado: evita que un paquete nuevo en una versión de Python o en una plataforma se instale sin fijar (falsa reproducibilidad).
    - `python-multipart>=0.0.31` en `requirements.txt` (R1).
- **L12 (2026-11-03):** P4, P5 y P6 en local.
  - **P6 (`522dc94`):** se retira `pytest>=8,<10` de `requirements-dev.txt`. Las pruebas no cambian.
  - **Corrección (error propio en L10 y L11):** colorama no la pedía `click`. `importlib.metadata.requires('click')` devuelve `None` en `click` 8.5.0, y en el entorno limpio ningún paquete la declara. Solo la pedía `pytest` (`sys_platform == "win32"`). Sin `pytest`, el conjunto de paquetes es el mismo en Windows y Linux, y con Python 3.12 y 3.14. Ya no hace falta ningún marcador. La auditoría (inventario) queda corregida.
  - **P4 (`40a1c7c`, `ebb11e4`):**
    - `backend/constraints.txt`: 24 versiones exactas, las mismas que instaló la CI de `main` (run `41650001412`) menos `pytest`, iniconfig, packaging, pluggy y Pygments. Nombres en el formato de `pip freeze` (`pydantic_core`, `typing_extensions`). Ninguna dependencia se actualiza.
    - `requirements.txt` conserva los rangos (`cryptography>=50.0.2`) y sube `python-multipart` a `>=0.0.31` (R1); la versión instalada sigue siendo 0.0.33.
    - CI:
      - Los jobs `python` y `e2e` instalan con `-c backend/constraints.txt`.
      - El job `python` tiene un paso nuevo, en Python estándar y sin dependencias: falla si algún paquete instalado, salvo `pip`, no está en `constraints.txt` o tiene otra versión, comparando nombres canónicos.
      - Solo está en `python` porque ese job instala el superconjunto de `e2e` con las mismas restricciones.
      - Probado en local:
        - Pasa en el entorno limpio («All installed packages match backend/constraints.txt (24 pins)»).
        - Falla en el `.venv` del proyecto, que tiene `pytest` y `pip-audit` sin fijar.
        - Ruff no da avisos sobre el script extraído (corregido un SIM115 inicial).
    - README:
      - Instalación con `-c` y `npm ci`.
      - `unittest` como único ejecutor.
      - «Actualizar Ruff» también cambia `constraints.txt`.
      - Sección nueva «Dependencias»: renovación mensual o ante un aviso de seguridad, procedimiento con un entorno limpio y `pip freeze`, actualización de un solo paquete, marcadores si aparecen diferencias de plataforma y actualización deliberada del lockfile.
  - **P5:** el README usa `npm ci` en la instalación (antes `npm install`); las E2E ya lo usaban.
  - **Verificación local (Windows, Python 3.14.7, entorno temporal limpio fuera del repositorio):**
    - La instalación con `-r requirements-dev.txt -c constraints.txt` deja exactamente 24 paquetes, idénticos a las restricciones; `pip check` sin conflictos.
    - Suite: 139 OK, igual que antes; P6 no cambia ninguna prueba.
    - Ruff 0.17.3 sin avisos.
    - `npm ci` reinstala 119 paquetes sin modificar `package-lock.json`. Typecheck limpio y build correcto (el aviso del chunk de más de 500 kB ya estaba en `docs/pendiente.md`).
    - E2E 88/88 con `E2E_PYTHON` apuntando al entorno limpio.
  - **Python 3.12:** se verifica en la CI (L13).
  - **Riesgo residual:**
    - Windows con Python 3.12 no se prueba en ningún sitio: la CI es Linux con 3.12 y en local solo hay 3.14.
    - El paso de CI solo detecta paquetes sin fijar en Linux con 3.12. Si en el futuro aparece un paquete solo para Windows o para otra versión de Python, se instalaría sin fijar hasta que alguien lo añada; el README indica cómo.
    - El `.venv` local del usuario no se ha recreado: sigue con `pytest` y `pip-audit`, sin efecto en el proyecto.
- **L13 (2026-11-03):** CI y revisión de H4.
  - **CI con Python 3.12:** run `41654245223` sobre `ef2ad24`, en verde en `python`, `frontend` y `e2e`, con Python 3.12.15.
    - El paso nuevo imprime «All installed packages match backend/constraints.txt (24 pins)».
    - Lo instalado por el job `python` coincide exactamente con `constraints.txt` (comparado con nombres canónicos), y los 20 paquetes de `e2e` son un subconjunto sin ninguno ajeno.
    - Unitarias: 139. E2E: 88.
  - **Revisión nativa** `review-4f64e338641dfb49` (riesgo escalado a alto por el elemento 5; lentes de riesgo, legibilidad y fiabilidad; consentimiento del usuario): aprobada y reconocida (`authority: burned`). Ningún hallazgo bloqueante.
    - **Aplicado:**
      - **`R2-constraints-dangling-readme-ref` y `R3-002`:** la cabecera de `constraints.txt` citaba una sección «Actualizar dependencias» que no existe; ahora cita «Dependencias».
      - **`R2-ci-check-message-mismatch`:** el mensaje de error cubre los dos casos, falta en las restricciones o versión distinta.
      - **`R2-readme-windows-paths-partial`:** el procedimiento de renovación incluye las rutas de Windows (`$env:TEMP\pwc-deps\Scripts\python.exe`).
    - **Sin cambios, con motivo:**
      - **`R3-001`** (el runner podría traer paquetes base además de `pip`): la CI real con 3.12 lo refuta, porque el paso pasó con 24 paquetes fijados y sin ningún paquete ajeno.
      - **`R1-hashless-pins`:** el usuario excluyó los hashes sin una justificación clara (L10); siguen como P13 opcional, con la justificación de la auditoría (PyPI no permite reemplazar los archivos de una versión publicada).
  - **Tras los ajustes:** el script del paso, extraído del YAML, pasa en el entorno limpio de 3.14 y falla en el `.venv` con el mensaje nuevo; Ruff no da avisos; la resolución con `-c` en seco no encuentra conflictos. CI en L14.
- **L14 (2026-11-03):** CI tras los ajustes de la revisión.
  - **CI:** run `41655317572` sobre `27c324e`, en verde en `python`, `frontend` y `e2e` (Python 3.12). Restricciones: 24, todas coinciden. Unitarias: 139. E2E: 88.
  - **H4 completa** en la rama, pendiente de la aprobación del usuario para integrarla.
  - **P7:** `vulnerability-alerts` sigue devolviendo 404 y `dependabot_security_updates`, `disabled`. El usuario indicó en L10 que activaría las alertas.
- **L15 (2026-11-03):** revisión de la rama completa respecto a `main`, pedida por el contrato (STATUS sin selectores) porque los ajustes de L13 formaban un candidato nuevo.
  - **Revisión** `review-af19b0263e862da5`: 4 lentes, consentimiento del usuario («Review this change»), aprobada y reconocida (`authority: burned`). Sin bloqueos.
  - **Aplicado:**
    - **`R2-ci-check-markers-collapse` (aviso) y `R4-marker-duplicate-pins-overwrite`:** un paquete repetido con distintos marcadores se colapsaba en silencio. Ahora el paso falla con «`<paquete>` appears twice…; keep one line per package», y el README indica que cada paquete va en una sola línea con `==`.
    - **`R4-ci-constraints-parser-brittle`:** el análisis es estricto. Ignora los comentarios al final de línea y rechaza cualquier línea que no sea `name==version` (con marcador opcional) con un mensaje claro en lugar de un traceback.
    - **`R3-constraint-check-skips-unit-tests`:** el paso se ejecuta después de las pruebas y de Ruff, con `if: ${{ !cancelled() }}` como Ruff, así que cada problema se informa por separado.
  - **Sin cambios:** `R1-001` (hashes), por decisión del usuario (P13).
  - **Comprobado en local con copias temporales de `constraints.txt`:**

    | Caso | Resultado |
    | --- | --- |
    | Archivo real | Pasa (24 pins) |
    | Comentario al final de línea | Pasa |
    | Paquete duplicado con marcador | Falla con el mensaje de duplicado |
    | `foo>=1.0` | Falla con «Unsupported line» |
    | Marcador de un paquete no instalado (`tomli`, Python < 3.11) | Pasa (25 pins) |

    Ruff no da avisos sobre el script extraído.
- **L16 (2026-11-03):** CI tras L15.
  - **CI:** run `41656482013` sobre `1fca6b0`, en verde en `python`, `frontend` y `e2e`.
  - **Job `python`, en este orden:** unitarias (139), Ruff y comprobación de restricciones («24 pins»), los tres correctos. E2E: 88.
  - **H4 terminada:** pendiente de la aprobación del usuario para integrarla en `main`.
- **L17 (2026-11-03):** última revisión de H4.
  - **Revisión** `review-47330554336fcc51`: toda la rama respecto a `main`, 4 lentes, consentimiento del usuario. Aprobada y reconocida (`authority: burned`) sobre `713d296`, con la CI de la rama en verde. Cinco sugerencias no bloqueantes, sin aplicar para no abrir otra revisión completa de la rama.
  - **Decisión del usuario** (L18): conservar solo las que sigan siendo pertinentes, como mantenimiento opcional y sin prioridad.
    - **Se conservan como opcionales:**
      - marcar el inventario de la auditoría (`docs/auditoria-dependencias.md`, líneas 57-58: 29 paquetes, transitivas de `pytest`, sin bloqueo) como la foto anterior a H4;
      - que el paso de restricciones avise también de versiones fijadas que ya no se instalan (sin contar las líneas con marcador).
    - **Se descartan:**
      - renombrar la variable `unpinned`, por ser cosmético;
      - proteger el paso frente a distribuciones sin nombre en sus metadatos, porque solo ocurre con un entorno corrupto y la CI usa un runner limpio.
    - **Hashes:** siguen como P13.
- **L18 (2026-11-03):** integración de H4, petición literal:

  > Apruebo integrar `chore/reproducible-installs` en `main`.
  >
  > Antes de integrar, comprueba que el diff sigue limitado a H4 y que `main` no ha avanzado inesperadamente.
  >
  > Integra la rama y verifica la CI de `main`. Si termina correctamente, elimina la rama local y remota, comprobando previamente que no quedan commits exclusivos.
  >
  > Da H4 por completada. Registra L17 y la integración en el plan, preferiblemente en la siguiente rama de trabajo para evitar commits directos de documentación en `main`.
  >
  > Las cinco observaciones menores no bloquean la integración. Conserva únicamente las mejoras que sigan siendo pertinentes como mantenimiento opcional, sin convertirlas automáticamente en nuevas tareas prioritarias.
  >
  > No comiences P8 hasta que confirmemos que la integración ha terminado correctamente.

  - **Antes de integrar:**
    - `main` local y remoto seguían en `2bd5a23`, que era la base de la rama, y la rama local coincidía con la remota (`713d296`).
    - El diff con `origin/main` solo tocaba los 7 archivos de H4, sin código de producción, pruebas ni frontend. En dependencias, solo la retirada de `pytest` y `python-multipart>=0.0.31`.
  - **`27734ba` — Merge `chore/reproducible-installs`** (`--no-ff`): suite y Ruff locales en verde.
  - **CI de `main`:** run `41658726069`, en verde en `python`, `frontend` y `e2e`, con Python 3.12.15. Restricciones: 24, todas coinciden. Unitarias: 139. E2E: 88.
  - **Rama borrada:** `chore/reproducible-installs`, en local y en remoto, sin commits exclusivos.
  - **Estado:** H4 completada. P7 sigue sin activar (`vulnerability-alerts` devuelve 404).
- **L19 (2026-11-03):** P8, petición literal:

  > Continúa con **P8 — Automatización de la auditoría de dependencias**, siguiendo `odd/tasks/dependency-hardening.md` y el flujo ODD habitual.
  >
  > Parte de `main` actualizado y crea una rama independiente.
  >
  > Antes de implementar:
  > - Registra L17 y L18, incluyendo la integración de H4 (`27734ba`) y su CI.
  > - Revisa los criterios de aceptación de P8 y respeta las decisiones ya aprobadas.
  >
  > Implementa un workflow independiente para:
  > - Ejecutar `pip-audit` sobre las dependencias Python fijadas en `backend/constraints.txt`.
  > - Ejecutar `npm audit` sobre las dependencias del frontend, distinguiendo producción y desarrollo.
  > - Utilizar versiones controladas de las herramientas de auditoría.
  > - Permitir ejecución manual y periódica.
  > - Presentar resultados comprensibles, con las vulnerabilidades y paquetes afectados.
  > - Evitar que los PR ajenos a dependencias queden bloqueados por nuevas vulnerabilidades detectadas externamente o problemas temporales de los servicios de auditoría.
  >
  > Comprueba que el workflow detecta realmente las vulnerabilidades y no devuelve falsos resultados satisfactorios cuando falla una herramienta o no se analizan dependencias.
  >
  > No añadas `pip-audit` a `requirements-dev.txt` ni modifiques las 24 restricciones de H4 para incluir sus dependencias.
  >
  > Mantén separada P7 (alertas de Dependabot), que requiere configuración del repositorio.
  >
  > Solicita revisión independiente centrada en seguridad, fiabilidad del workflow y detección de falsos negativos.
  >
  > Registra las pruebas y decisiones en el plan. Puedes subir la rama para verificar GitHub Actions, pero no integrarla en `main` sin mi aprobación.
  >
  > No amplíes el alcance a actualizaciones de dependencias, hashes ni otros pendientes.

  - **Rama:** `ci/dependency-audit`, desde `main` en `27734ba`.
  - **Comportamiento real de las herramientas** (salidas capturadas en local, `pip-audit` 2.10.1 y npm 11.3.0):
    - **`pip-audit` con una entrada sin dependencias:** termina con código 0, «No known vulnerabilities found» y `dependencies: []`. Es un **falso resultado satisfactorio** si solo se mira el código de salida.
    - **`pip-audit` con un archivo inexistente:** código 1 y ningún JSON.
    - **`pip-audit` con `cryptography==46.0.7`:** código 1 y 7 entradas, IDs repetidos con alias, para 4 avisos.
    - **`npm audit` sin conexión al registro:** código 1 y un JSON con `error`, sin `auditReportVersion`.
    - **`npm audit` en un proyecto vacío:** código 0 y `metadata.dependencies.total` 0.
    - **`npm audit` en el frontend:** `total` es 119, igual que el número de paquetes de `package-lock.json`.
    - **`npm audit --omit=dev`:** solo lista los avisos de producción. Con `lodash` 4.17.20 en producción y `minimist` 1.2.5 en desarrollo, el informe completo trae los dos y el de producción solo `lodash`.
  - **Contradicción en P8:** el criterio «un run manual en verde» no se puede cumplir antes de integrar, porque GitHub solo permite lanzar a mano (`workflow_dispatch`) un workflow que exista en la rama por defecto. Ese run se hará después de integrar; antes se verifica con un disparador `push` limitado a los archivos de dependencias (S12).
  - **Herramienta fijada:**
    - `pip-audit==2.10.1` y sus 26 dependencias van fijadas en `.github/audit-requirements.txt`, se instalan con `--no-deps` y se comprueban con `pip check`. Sin esa lista, cada run tomaría las últimas versiones de requests, rich, cyclonedx y demás.
    - Con Python 3.12, `cyclonedx-python-lib` también pide `typing_extensions` (`python_version < "3.13"`), que va con ese marcador explícito.
    - Ni `requirements-dev.txt` ni las 24 restricciones de H4 cambian.
- **L20 (2026-11-03):** implementación y verificación de P8.
  - **`26b1553`** (prueba primero; RED: el módulo no existía):
    - `.github/scripts/dependency_audit.py`, en Python estándar, interpreta los JSON de `pip-audit` y `npm audit`.
    - Publica una tabla en el resumen del run: paquete, versión, producción o desarrollo, gravedad (solo npm la da), avisos y versión que los corrige.
    - Devuelve 1 si hay vulnerabilidades o si el informe no es fiable: no hay JSON o tiene otro formato; la herramienta falló (código distinto de 0 sin vulnerabilidades); hay paquetes omitidos (`skip_reason`); se analizaron menos paquetes o a otra versión que los fijados; `auditReportVersion` no es 2; npm analizó un total distinto del número de paquetes de `package-lock.json`, o el lockfile está vacío.
    - `tests/test_dependency_audit.py` usa estructuras como las de las salidas reales capturadas.
    - El caso del lockfile vacío se añadió después, también con prueba primero (RED → GREEN).
  - **`334b631`:** `.github/workflows/dependency-audit.yml` y `.github/audit-requirements.txt`.
    - Se ejecuta cada lunes a las 06:17 UTC, con `workflow_dispatch` y con `push` o `pull_request` limitados a los archivos de dependencias, de la auditoría y del propio workflow.
    - `permissions: contents: read`; `tests.yml` no cambia.
    - **Job `python`:** instala la herramienta fijada con `--no-deps`, ejecuta `pip check` y audita `backend/constraints.txt` (`--no-deps --disable-pip`).
    - **Job `npm`:** `npm audit` completo y `--omit=dev`; después `npm ci --ignore-scripts` y `npm audit signatures`.
    - El código de salida de las herramientas no decide: se pasa al script.
  - **`28c138e`:** README («Auditoría de vulnerabilidades») y auditoría (excepciones, ninguna por ahora; limitaciones).
  - **Verificación en local:**
    - El script con las salidas reales capturadas da 0 o 1 en los 8 casos según lo esperado (limpio, vulnerable, sin dependencias, sin JSON, error de red y proyecto vacío, en Python y en npm).
    - La herramienta se instaló desde la lista fijada en un entorno limpio con 3.14: `pip check` limpio y 24 paquetes auditados.
    - Suite 157 OK y Ruff sin avisos.
  - **Verificación en GitHub:**
    - **Rama de P8, `28c138e`:** `Dependency audit` en verde. `pip-audit` 2.10.1 y `pip check` limpio con Python 3.12 (el marcador de `typing_extensions` funciona); 24 paquetes de Python y 119 de npm sin vulnerabilidades; 70 firmas y 37 atestaciones verificadas. `Tests` en verde (157 y 88 E2E).
    - **Rama desechable `test/dependency-audit-negative`** (4 commits de prueba, nunca integrada, borrada en local y en remoto al terminar):
      1. **Vulnerables:** `cryptography==46.0.7`, `lodash` 4.17.20 en producción y `minimist` 1.2.5 en desarrollo, añadidos solo al lockfile y sin ejecutar scripts. Los dos jobs fallan y la tabla lista `cryptography` (4 avisos, corregido en 48.0.1 o 49.0.0…), `lodash` como producción/high y `minimist` como desarrollo/critical.
      2. **Restricciones vacías:** **falso negativo real.** El job `python` pasó con «No known vulnerabilities in 0 packages», porque la comparación con lo fijado es vacía si el propio `constraints.txt` está vacío. Corregido en `48a3b85` (prueba primero): el script falla si las restricciones no fijan ningún paquete o falta alguno de los declarados en `requirements*.txt`, que el workflow le pasa con `--requirements`. Verificado en local con las salidas reales y con un `constraints.txt` sin `fastapi`. En GitHub, el mismo caso falla con «the constraints pin no packages, so nothing would be analysed».
      3. **Caída simulada de los servicios** (`HTTPS_PROXY` inexistente para `pip-audit`; `--registry` inexistente para npm): los dos jobs fallan como «The audit cannot be trusted», con la causa (sin JSON de `pip-audit`; `ECONNREFUSED` en npm).
    - **Rama de P8, `48a3b85`:** `Dependency audit` y `Tests` en verde (159 pruebas).
  - **Decisiones:**
    - Sin reintentos automáticos: una caída se ve como fallo, nunca como éxito, y solo afecta a los runs de la auditoría, no a los PR ajenos a dependencias.
    - `npm audit` falla con cualquier gravedad, igual que `pip-audit`; el triaje sigue la política de actualización.
    - npm es el que trae Node 22. El script exige `auditReportVersion` 2, así que un cambio de formato falla en vez de pasar.
  - **Pendiente:** el run manual (`workflow_dispatch`) después de integrar, y comprobar que un commit sin cambios de dependencias no lanza la auditoría (L21). P7 sigue sin activar.
- **L21 (2026-11-03):** filtro de rutas y revisión de P8.
  - **Filtro de rutas:** el push de solo documentación `f47d708` lanzó `Tests` pero no `Dependency audit`. `pull_request` usa la misma lista de `paths`.
  - **Revisión** `review-1274eda902ee9eaf`: rama respecto a `main`, riesgo escalado a alto por el elemento 5, lentes de riesgo, fiabilidad y resiliencia, consentimiento del usuario. Aprobada y reconocida (`authority: burned`).
    - **Riesgo:** sin hallazgos.
    - **Tres sugerencias aplicadas en `2686219`**, con prueba primero (RED en dos):
      - **`R4-001`:** una forma inesperada del JSON (por ejemplo, una dependencia sin `version`) acababa en un traceback sin línea en el resumen. Ahora se publica «The audit cannot be trusted: unexpected report content (…)» con código 1. Ya fallaba antes, así que no había falso éxito.
      - **`R3-optional-pin-version-untested`:** prueba nueva. Un paquete con marcador auditado a otra versión falla; ese comportamiento ya existía y ahora queda cubierto.
      - **`R3-table-cell-escaping`:** las celdas escapan `|` y unen los saltos de línea, así que un título de aviso no descoloca la tabla.
  - **Verificación:**
    - En local: suite 162 OK; Ruff sin avisos; las salidas reales (Python limpio y vulnerable, npm limpio y vulnerable) dan el mismo resultado que antes.
    - En GitHub sobre `2686219`: `Dependency audit` (run `41666695451`) y `Tests` (run `41666695456`) en verde.
  - **Pendiente:** aprobación del usuario para integrar; run manual después de integrar; P7.
- **L22 (2026-11-03):** revisión final de P8.
  - **Revisión** `review-11d512e095c01328`: rama completa respecto a `main`, 4 lentes, consentimiento del usuario. Aprobada y reconocida (`authority: burned`). Resiliencia: sin hallazgos.
  - **Aplicado**, con prueba primero (RED → GREEN):
    - **`R2-python-scope-hardcoded-production` (aviso):** todo hallazgo de Python salía como «production», incluidas herramientas de desarrollo. `pip-audit` no sabe qué paquetes van en la aplicación, así que el ámbito de Python es `n/a`, como la gravedad. La distinción producción/desarrollo es solo de npm (auditoría y README).
    - **`R2-requirements-parse-error-mislabelled` (aviso) y `R3-direct-requirement-name-parsing`:** una línea con ruta, URL o enlace VCS se interpretaba como un paquete llamado `-` o `git`, con un mensaje engañoso. Ahora falla con «unsupported requirements line…». Ya fallaba antes, así que no había falso éxito.
    - **`R2-plan-commit-list-incomplete`:** P8 lista todos sus commits.
  - **Opcionales sin aplicar:**
    - **`R2-npm-package-count-duplicated`** y **`R2-chained-ternary-fix`:** legibilidad.
    - **`R3-npm-version-floats`:** npm es el de Node 22. Si cambia el formato o el recuento, el run falla, nunca pasa; ya se decidió en L20.
    - **`R1-001`:** fijar las acciones por SHA; ya existe como P10 opcional.
  - **Verificación local:** suite 163 OK; Ruff sin avisos; las salidas reales de Python (limpia y vulnerable) dan 0 y 1.
- **L23 (2026-11-03):** última revisión de P8 y P7.
  - **Revisión** `review-56aef8cc8f478f49`: rama completa respecto a `main`, 4 lentes, consentimiento del usuario. Aprobada y reconocida (`authority: burned`). Riesgo y resiliencia: sin hallazgos.
  - **Sugerencias opcionales, sin aplicar:**
    - el recuento de paquetes del lockfile se calcula dos veces en `dependency_audit.py` (en `npm_findings` y en `main`);
    - la condición anidada que construye `fix` en `npm_findings`;
    - las listas de `paths` de `push` y `pull_request` están duplicadas en `dependency-audit.yml` y deben mantenerse iguales;
    - no se comprueba que falte en el informe una versión fijada con marcador; hoy `constraints.txt` no tiene ninguna.
  - **P7 cumplida:** el usuario activó las alertas de Dependabot y `gh api repos/eliseumarmon/password-checker/vulnerability-alerts -i` devuelve 204.
- **L24 (2026-11-03):** hallazgos de otra sesión e integración de P8.
  - **Revisión de otra sesión:** el usuario aportó el resumen de `review-10cf5f…`. No es ninguna de las revisiones de esta rama: sus números de línea corresponden a la versión del script anterior a `48a3b85`.
    - **Ya corregidos en la rama:** el ámbito de Python fijado en el código (es `n/a` desde L22) y la falta de prueba para una versión que no coincide (existen las dos pruebas).
    - **Comprobado que no es un fallo:** el total de npm en producción. npm 11.3 con `--omit=dev` informa el mismo `total` que el lockfile (119); si cambiara, el run fallaría, nunca pasaría.
    - **Decisiones ya registradas:** la versión de npm sin fijar, `--require-hashes` (P13), la ausencia de reintentos, y que las pruebas del script las ejecute `tests.yml`.
    - **Siguen como opcionales:** el recuento duplicado y la condición anidada (L23).
  - **Integración**, petición literal: «Integra».
    - Antes: `main` seguía en `27734ba`, la base de la rama, y el diff solo tocaba los 7 archivos de P8, sin código de producción, `tests.yml` ni dependencias.
    - **`cf3f089` — Merge `ci/dependency-audit`** (`--no-ff`): suite 163 OK y Ruff sin avisos en local.
    - **En `main`:**
      - `Tests` (push, run `41669167281`): en verde, 163 pruebas, 24 versiones fijadas que coinciden y 88 E2E.
      - `Dependency audit` (push, run `41669167294`): en verde.
      - **Run manual** (`workflow_dispatch`, run `41669217453`): en verde, 24 paquetes de Python y 119 de npm sin vulnerabilidades y 70 firmas verificadas. Cumple el criterio de aceptación de P8 que solo se podía comprobar tras integrar.
    - Tras activar P7 aparece también un run automático «Dependency Graph» (`update-pip-graph`), en verde.
- **L25 (2026-11-04):** cierre de la fase, petición literal:

  > Puedes eliminar `ci/dependency-audit` tanto en local como en `origin`.
  >
  > Antes, confirma que todos sus commits están incluidos en `main` y que no contiene cambios exclusivos.
  >
  > Comprueba después que `main` está sincronizada con `origin/main` y que el árbol de trabajo queda limpio.
  >
  > Con P7 y P8 completadas, damos por cerrada la fase prioritaria de auditoría y endurecimiento de dependencias.
  >
  > Conserva L23 y L24 pendientes de registrar en `dependency-hardening.md` durante la próxima tarea documental, sin realizar un commit directo en `main`.
  >
  > No comiences P9 ni los opcionales P10–P13 todavía.

  - **Rama borrada:** la local y la remota de `ci/dependency-audit` eran ancestros de `main`, sin commits ni diferencias exclusivas. Se borraron las dos.
  - **Estado final:** `main` y `origin/main` en `cf3f089`, sin commits de diferencia; árbol de trabajo limpio.
  - **Fase prioritaria cerrada.** Abiertas: P9 (baja) y las opcionales P10-P13, sin empezar.
- **L26 (2026-11-04):** limpieza de ramas y consolidación documental.
  - **Petición:** primero «Haz limpieza de ramas. Haz 1 y 2. Pero no empezamos aun la nueva fase. A excepcion de p12 que parece quedarse vinculada directamente a la fase 1 con quitar prime vue y vue router.» Después la acotó: «Haz solo limpieza de ramas. y consolidación documental de la fase 0 sin mirar aun la fase 1».
  - **Ramas borradas, todas integradas** (comprobado que eran ancestros de `main`, en local y en remoto):
    - `docs/expand-future-vault-backlog` y `fix/session-limit-rejections`, en local y en `origin`;
    - `docs/ruff-new-default-rules`, solo en local;
    - `chore/ruff-clean-and-ci`, en local y en `origin`. La local iba por detrás de su remota y `git branch -d` se negó, así que se borró con `-D` después de comprobar que tanto la local como la remota estaban contenidas en `main`.
  - `docs/phase-1-plan` y su worktree no se tocan.
  - **Consolidación:** L23-L26, P7 y P8 cerradas, P12 vinculada a la Fase 1, y `docs/pendiente.md` y la auditoría con el estado final.
- **L27 (2026-11-04):** P9 y P11, petición literal: «Me interesa tener ahora cerrado P9 y P11. Pytest se quitó y nos quedamos con unittest pip-audit se ha usado en el hardening, pero de momento ya no es necesario.»
  - **Decisión de P11:** a la pregunta «¿Cómo los alineo?» (hoy: local con Python 3.14 y Node 24; CI con 3.12 y 22; el README pide 3.12+ y 22+), el usuario eligió «3.12+3.14 y Node 24».
  - **`.venv` local:** se recrea limpio desde las restricciones, para retirar `pytest`, `pip-audit` y sus dependencias.
  - **Procedencia de `httpx2`, comprobada de nuevo:**
    - La última versión es 2.16.0 (2026-10-21; 22 versiones desde el 2026-05-11). La publicación `v2.16.0` de `pydantic/httpx2` la hizo `Kludex`, el mantenedor de Starlette que añadió `httpx2` a `TestClient`, el mismo día que la de PyPI. El repositorio tiene `publish.yml` y está activo.
    - OSV no tiene avisos. Sus archivos en PyPI **siguen sin atestación PEP 740**; queda como riesgo residual.
    - Dependencias nuevas: `httpcore2==2.16.0`, del mismo repositorio, que pide `h11>=0.16` y `truststore>=0.10`; y `truststore` 0.10.5, de Seth Larson, que usa los certificados del sistema en lugar de `certifi`.
    - Starlette no ha anunciado ninguna fecha para retirar `httpx`.
  - **Ramas:** `chore/httpx2` y `ci/align-runtimes`, encadenadas sobre `docs/close-dependency-hardening`, porque las tres tocan este plan.
- **L28 (2026-11-04):** P9 en local (Windows, Python 3.14.7).
  - **Prueba primero:** en `tests/test_required_dependencies.py`, el caso que bloqueaba `httpx` pasa a bloquear `httpx2`. RED con las dependencias anteriores: Starlette recurría a `httpx` instalado y `test_api` no fallaba («[] is not true»).
  - **`810db17`:**
    - `requirements-dev.txt` cambia `httpx>=0.27,<1` por `httpx2>=2.16,<3`.
    - Para `constraints.txt`, las versiones se resolvieron en un entorno limpio manteniendo fijado todo lo demás. Salen `httpx==0.28.1`, `httpcore==1.0.9` y `certifi==2026.10.23`; entran `httpx2==2.16.0`, `httpcore2==2.16.0` y `truststore==0.10.5`. Siguen siendo 24 versiones y no cambia ninguna otra.
    - `tests/test_api.py` no cambia: `fastapi.testclient` elige `httpx2`.
  - **GREEN en el entorno limpio:** `pip check` sin problemas; suite 163 OK; Ruff sin avisos. `fastapi.testclient` se importa con los avisos convertidos en errores, sin `StarletteDeprecationWarning`.
  - **`.venv` local:** se desinstalaron los 32 paquetes que no estaban en las restricciones (las familias de `pytest`, `pip-audit` y `httpx`) y se instaló con `-c`. Quedan exactamente 24 paquetes, idénticos a `constraints.txt`; `pip check` limpio, suite y Ruff en verde. No se borró la carpeta, porque había procesos de Python abiertos que podían bloquearla.
  - **Riesgo residual:** los archivos de `httpx2` en PyPI no tienen atestación PEP 740 (L27).
- **L29 (2026-11-04):** CI de P9 y P11.
  - **P9 en GitHub** (rama `chore/httpx2`, `f9c6d21`): `Tests` (run `41801704242`) y `Dependency audit` (run `41801704251`) en verde. Con Python 3.12 se instala `httpx2` 2.16.0 y coinciden las 24 versiones fijadas; 163 pruebas y 88 E2E. **0** apariciones de `StarletteDeprecationWarning`, que salía en cada run anterior.
  - **P11 (`07e786d`, rama `ci/align-runtimes`):**
    - `frontend/.nvmrc` con `24`.
    - En `tests.yml`, el job `python` usa una matriz `['3.12', '3.14']` con `fail-fast: false`; `frontend` y `e2e` toman Node de `node-version-file: frontend/.nvmrc`.
    - En `dependency-audit.yml`, el job `npm` usa el mismo `.nvmrc`, y `frontend/.nvmrc` se añade a las rutas que lanzan la auditoría, porque fija la versión de npm que audita.
    - README: Python 3.12 o posterior (la CI prueba 3.12 y 3.14), Node.js 24 desde `.nvmrc`; el procedimiento de renovación menciona las dos versiones de Python.
    - El job `e2e` y el job `python` de la auditoría siguen con Python 3.12.
  - **En local, Node 24.21.0:** `npm ci` (119 paquetes) no modifica `package-lock.json` y el build es correcto.
  - **En GitHub** (run `41802123655`): `python (3.12)`, `python (3.14)`, `frontend` y `e2e` en verde.
    - Cada job de Python ejecuta 163 pruebas, Ruff, y la comprobación de las 24 versiones fijadas, que también coinciden con 3.14.
    - Versiones de los runners: Python 3.12.16 y 3.14.9; Node 24.22.1.
    - E2E: 88.
    - `Dependency audit` (run `41802123756`) en verde, con Node 24.22.2: 24 paquetes de Python y 119 de npm sin vulnerabilidades.
  - **Observación:** las versiones de parche de Python y Node varían entre runners (en un mismo día, Python 3.12.15 y 3.12.16; Node 24.22.1 y 24.22.2). Es lo esperado al fijar solo `3.12` y `24`; las versiones de parche no se fijan.
  - **Riesgo residual que se cierra:** Python 3.14 ya se prueba en la CI. Windows sigue sin probarse en la CI.
- **L30 (2026-11-04):** revisión de los cambios encadenados (cierre documental, P9 y P11) respecto a `main`.
  - **Revisión** `review-6b89bc513d330891`: riesgo escalado a alto por el elemento 5; lentes de riesgo y fiabilidad; consentimiento del usuario. Aprobada y reconocida (`authority: burned`).
  - **Riesgo:** una sugerencia, `R1-001`: volver a comprobar la procedencia de `httpx2` en cada renovación, porque sigue sin atestaciones PEP 740. Ya figura como riesgo residual (L27) y queda como regla para las renovaciones.
  - **Fiabilidad:** tres avisos válidos, aplicados.
    - **`R3-httpx2-test-env-dependent`:** si el entorno conserva `httpx`, Starlette recurre a él y el subcaso que bloqueaba solo `httpx2` fallaba aunque no faltara nada.
      - RED reproducido en un entorno limpio al que se añadió `httpx==0.28.1`.
      - El subproceso de la prueba ahora acepta varios paquetes separados por comas, y el caso bloquea `httpx2,httpx`.
      - GREEN tanto con `httpx` sobrante como en el `.venv` limpio (163 pruebas). Ruff sin avisos.
    - **`R3-pendiente-stale-httpx2`:** `docs/pendiente.md` decía que la migración a `httpx2` seguía pendiente; ahora solo quedan medidas opcionales.
    - **`R3-plan-header-p9-open`:** la cabecera del plan decía que P9 seguía abierta; ahora indica P9 y P11 completadas, y abiertas solo P10, P13 y P12 (vinculada a la Fase 1).
