# Dependencias y cadena de suministro: auditoría y plan de endurecimiento

Objetivo: diagnosticar riesgos de dependencias, reproducibilidad y CI, y proponer un plan proporcionado. Diagnóstico completo en [auditoria-dependencias](../../docs/auditoria-dependencias.md).
Rama de la auditoría: `docs/dependency-audit` desde `main` (solo documentación). **Estado del plan: propuesta pendiente de aprobación**; ninguna tarea P se implementa sin ella. Pruebas de cada tarea: `python -m unittest discover -s tests`, `ruff check .`, `npm run build`, `npm run e2e`.

## Specs

Fase de auditoría (autorizada):

- **S1 — Inventario y diagnóstico.** «Examina el estado real del repositorio, tanto backend (Python/FastAPI) como frontend (Vue/Vite)». «Ejecuta `pip-audit` y `npm audit`, distinguiendo dependencias de producción y desarrollo.» «Determina si las instalaciones son reproducibles entre desarrollo y CI.» «No instales ni ejecutes herramientas adicionales sin valorar antes su procedencia y seguridad.»
- **S2 — Análisis de riesgos.** Por hallazgo: «Dependencia o componente afectado.», «Versión instalada y versiones vulnerables, cuando corresponda.», «Vulnerabilidad identificada y referencias (CVE/GHSA).», «Severidad y explotabilidad real en Password Checker.», «Si afecta a producción, desarrollo o CI.», «Posible impacto sobre credenciales, TOTP, cifrado, sesiones `.pwc` y archivos importados.», «Corrección recomendada y riesgos de compatibilidad.» «No equipares automáticamente la severidad publicada de una vulnerabilidad con su riesgo real en nuestra aplicación.» «Distingue los hallazgos confirmados, los riesgos potenciales y las cuestiones que no hayan podido verificarse.»
- **S3 — Reproducibilidad y política de versiones.** «No implementes todavía ninguna alternativa. Recomienda la más adecuada para el tamaño y arquitectura actuales del proyecto, evitando complejidad innecesaria.»
- **S4 — Plan de actuación.** «Prepara un plan siguiendo el flujo ODD existente, con tareas pequeñas, independientes y verificables.» Por tarea: «Prioridad según riesgo e impacto.», «Dependencias entre tareas.», «Archivos previsiblemente afectados.», «Criterios de aceptación verificables.», «Pruebas necesarias.», «Riesgos de regresión.», «Necesidad de revisión independiente.» «Distingue entre correcciones urgentes, mejoras de mantenimiento y medidas opcionales.»
- **S5 — Límites.** «No actualices paquetes.» «No modifiques el código ni la configuración de CI.» «No introduzcas nuevas herramientas permanentes.» «No alteres el cifrado, el formato `.pwc` ni las reglas de consolidación.» «No recuperes la CLI eliminada.» «No utilices credenciales reales.»
- **S6 — Entrega.** «Presenta primero un resumen ejecutivo de los hallazgos y sus prioridades.» «No dupliques información en `docs/pendiente.md`; utiliza referencias a los documentos específicos.» «Solicita una **revisión independiente del diagnóstico y del plan**, centrada en seguridad, exactitud de los hallazgos, proporcionalidad de las soluciones y posibles omisiones.» «No implementes ninguna corrección, no integres cambios en `main` y no modifiques dependencias hasta que apruebe el plan.»

## Tasks

Auditoría:

- [x] A1 — S1, S2, S3, S5: diagnóstico en `docs/auditoria-dependencias.md` y referencia en `docs/pendiente.md`. Ruta: inline. Commit: el de «add dependency and supply-chain audit».
- [x] A2 — S4: esta propuesta de tareas. Ruta: inline. Mismo commit.
- [x] A3 — S6: revisión independiente del diagnóstico y del plan. Ruta: un revisor independiente de solo lectura (L3). La revisión nativa de gentle-ai también aprobó el commit, pero solo con comprobaciones estructurales. Correcciones en el commit «apply independent review».

Propuesta de endurecimiento (**pendiente de aprobación**). Cada bloque es una funcionalidad con su propia rama desde `main`, para respetar «una funcionalidad por rama». H/R remiten a los hallazgos de la auditoría.

**Correcciones urgentes: rama `fix/cryptography-50`** (P1 y P2 son la red de seguridad de P3; los tres en la misma rama, un commit cada uno).

- [ ] P1 — Prueba de compatibilidad del formato `.pwc` (H3). Prioridad: urgente, previa a P3. Depende de: nada.
  - Archivos: `tests/test_sessions.py` (o un `tests/test_session_format.py` nuevo).
  - Aceptación:
    - Una sesión ficticia cifrada con `cryptography` 46.0.7 y `argon2-cffi` 25.1.0 se descifra a un contenido esperado. Se guarda como constante en un archivo `.py`, porque `.gitignore` excluye `*.pwc` y `*.json`.
    - `encrypt_session` usa `secrets.token_bytes`, así que el vector se genera una sola vez con sal y nonce fijos, llamando directamente a `hash_secret_raw` y `AESGCM` (o con un script desechable). **No se modifica `encrypt_session` para inyectarle aleatoriedad.**
    - Una clave Argon2id derivada de sal y contraseña fijas coincide con su valor conocido.
    - Al cambiar en `sessions.py` un parámetro de `_key`, el `AAD` o un campo del envoltorio, la prueba falla. Es una comprobación manual temporal, que se deshace sin llegar a ningún commit.
  - Pruebas: la propia prueba más la suite completa. El commit no cambia `sessions.py`.
  - Regresión: ninguna en producción; solo añade pruebas.
  - Revisión independiente: no (sin código de producción).
- [ ] P2 — Que las pruebas de cifrado y API no se salten en silencio (H2). Prioridad: urgente, previa a P3. Depende de: nada.
  - Archivos: `tests/test_sessions.py`, `tests/test_session_limits.py`, `tests/test_api.py`.
  - Aceptación: sin `try/except ImportError` ni `skipUnless` por dependencias obligatorias. Con `cryptography` bloqueada en un proceso aislado (`sys.modules['cryptography'] = None` antes de descubrir las pruebas), `unittest` termina en error, no en `OK (skipped=N)`. Suite: 138 pruebas, 0 saltadas.
  - Pruebas: suite completa; la comprobación del bloqueo se ejecuta a mano y no se versiona.
  - Regresión: quien ejecute las pruebas sin instalar `requirements-dev.txt` verá errores en lugar de saltos. Es el comportamiento buscado; documentarlo en el README si hace falta.
  - Revisión independiente: no.
- [ ] P3 — `cryptography>=50.0.2,<51` (H1). Prioridad: urgente. Depende de: P1 y P2.
  - Archivos: `backend/requirements.txt`; si P4 ya existiera, también `backend/constraints.txt`.
  - Aceptación: OSV (o `pip-audit`) sin avisos para `cryptography`. P1 en verde con 50.0.2: los `.pwc` de 46.0.7 se abren. Suite, `ruff check .` y E2E en verde en local (Python 3.14) y en CI (3.12). Sin cambios en `sessions.py`.
  - Pruebas: suite completa, E2E y CI.
  - Regresión: wheels con OpenSSL 4.0.x. Desde 49.0.0 no hay wheels de Windows de 32 bits ni de macOS x86_64: un Mac Intel tendría que compilar con Rust. Documentarlo si afecta a alguien.
  - Revisión independiente: **sí** (seguridad y dependencias: elementos 2 y 5 de alto riesgo).

**Mantenimiento: rama `chore/reproducible-installs`.**

- [ ] P4 — Restricciones de Python con todas las versiones fijadas y límites inferiores seguros (H4, R1). Prioridad: alta. Depende de: P3 (para no fijar una `cryptography` vulnerable).
  - Archivos: `backend/constraints.txt` (nuevo), `backend/requirements.txt`, `backend/requirements-dev.txt`, `.github/workflows/tests.yml` (jobs `python` y `e2e`: `-c backend/constraints.txt`) y `README.md` (instalación, pruebas y cómo regenerar).
  - Aceptación:
    - `constraints.txt` fija con `==` todas las dependencias de `requirements-dev.txt` y sus transitivas. Se genera con `pip freeze` en un entorno limpio con Python 3.12.
    - `pip freeze` en Linux omite colorama, así que **se añade a mano** (el valor de `click` en Windows) y el README documenta ese paso.
    - En la CI, las líneas `Successfully installed` del job `python` coinciden exactamente con `constraints.txt` (salvo colorama), y las del job `e2e` son un subconjunto.
    - Límite inferior `python-multipart>=0.0.31`. Ninguna versión conocida de FastAPI ni de uvicorn exige `starlette>=1.3.1` ni `h11>=0.16` (FastAPI 0.162.0 pide `starlette>=0.46.0`; uvicorn, `h11>=0.8`), así que esos mínimos se fijan en `constraints.txt`.
  - Pruebas: suite, Ruff, build y E2E en CI. Instalación en limpio en local con `-c` y Python 3.14.
  - Regresión:
    - Un `pip install` sin `-c` sigue funcionando con los rangos. Si los rangos y las restricciones discrepan, pip falla con un error explícito.
    - Las restricciones generadas con 3.12 se usan también con 3.14 en local. Hoy funciona, pero una regeneración futura podría fijar un paquete sin wheel para cp314.
  - Revisión independiente: **sí** (CI y dependencias: elemento 5).
- [ ] P5 — README con `npm ci` (H7). Prioridad: media. Depende de: nada.
  - Archivos: `README.md`.
  - Aceptación: la instalación usa `npm ci` y el README explica cuándo regenerar el lockfile (`npm install` deliberado).
  - Pruebas: ninguna ejecutable; revisar el texto.
  - Regresión: ninguna.
  - Revisión independiente: no.
- [ ] P6 — Decidir sobre `pytest` (H8). Prioridad: baja. Depende de: decisión del usuario.
  - Archivos: `backend/requirements-dev.txt` y, si se conserva, `README.md`.
  - Aceptación: o se retira (y la CI sigue en verde con `unittest`), o se documenta como ejecutor local opcional.
  - Pruebas: suite.
  - Regresión: el IDE configurado con pytest dejaría de encontrarlo.
  - Revisión independiente: no.

**Mantenimiento: detección, rama `ci/dependency-audit`.**

- [ ] P7 — Activar las alertas de Dependabot (H5). Prioridad: alta e inmediata. Depende de: nada.
  - Archivos: ninguno. Es un ajuste del repositorio que **solo puede activar el propietario** (Settings → Advanced Security → Dependabot alerts).
  - Aceptación: `gh api repos/eliseumarmon/password-checker/vulnerability-alerts -i` devuelve 204.
  - No verificado: que GitHub detecte `cryptography` con requisitos que solo tienen rangos. Para Python, las alertas probablemente solo cubran dependencias directas, así que la red real es P8.
  - Pruebas y regresión: ninguna.
  - Revisión independiente: no.
- [ ] P8 — Workflow de auditoría separado (H5). Prioridad: media. Depende de: P3 y P4.
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
- [ ] P9 — Migrar las pruebas de API de `httpx` a `httpx2` (H6). Prioridad: baja; cuando Starlette anuncie la retirada o en la siguiente actualización programada. Depende de: P4. Rama propia.
  - Archivos: `backend/requirements-dev.txt`, `backend/constraints.txt` y, si cambia la importación, `tests/test_api.py`.
  - Aceptación: sin `StarletteDeprecationWarning` en la CI y con la suite en verde. Procedencia de `httpx2` revisada de nuevo (sus archivos no tenían atestación PEP 740 el 2026-11-03).
  - Pruebas: suite.
  - Regresión: diferencias de comportamiento del cliente en `TestClient`.
  - Revisión independiente: no.

**Medidas opcionales** (cada una en su propia rama si se aprueba):

- [ ] P10 — Acciones de GitHub fijadas por SHA con comentario de versión, y `dependabot.yml` solo para `github-actions` (H9). Prioridad: baja. Archivos: `.github/workflows/*.yml`, `.github/dependabot.yml`. Aceptación: cada `uses:` apunta a un SHA de 40 caracteres que coincide con su etiqueta (`gh api repos/<acción>/git/ref/tags/<v>`), y la CI está en verde. Si se aprueba, se puede imponer activando `sha_pinning_required` en los permisos de Actions del repositorio (hoy `false`). Regresión: ninguna funcional. Revisión: sí (CI).
- [ ] P11 — Alinear los entornos: Python 3.12 disponible en local, o añadir 3.14 a una matriz de CI, y `engines` o `.nvmrc` para Node (H4). Prioridad: baja. Archivos: `.github/workflows/tests.yml`, `frontend/package.json`, `README.md`. Aceptación: la versión de referencia está documentada y la CI la prueba. Revisión: sí si toca la CI.
- [ ] P12 — Actualizaciones mayores del frontend (H10): `primevue` 5 con `@primeuix/themes` 3 primero (llevan más tiempo sin publicar y van en el bundle), después `pinia` 4, `vue-router` 5, `vite` 8 y `typescript` 7. **Fuera de este plan:** cada una es una funcionalidad con su propio documento ODD y sus pruebas E2E.
- [ ] P13 — Bloqueo con hashes (uv con `--universal --generate-hashes`) si el modelo de amenazas crece con la bóveda persistente. Fuera de alcance por ahora.

Orden recomendado: P7 (inmediata, sin código) → P1, P2 → P3 → P4, P5 → P8 → resto según la política de actualización. Previsión: P1-P3 unas 150 líneas, P4-P6 unas 80 más el archivo generado y P8 unas 60; cada rama por debajo de las ~400 líneas, con un PR por rama.

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
