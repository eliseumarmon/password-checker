# Dependencias y cadena de suministro: auditoría y plan de endurecimiento

Objetivo: diagnosticar riesgos de dependencias, reproducibilidad y CI, y proponer un plan proporcionado. Diagnóstico completo en [auditoria-dependencias](../../docs/auditoria-dependencias.md).
Rama de la auditoría: `docs/dependency-audit` desde `main` (solo documentación). **Estado del plan: aprobado (L4)**, empezando por `fix/cryptography-50`, encadenada sobre `docs/dependency-audit` (que debe integrarse antes). H4 y H5 siguen pendientes; nada se integra en `main` sin aprobación del usuario. Pruebas de cada tarea: `python -m unittest discover -s tests`, `ruff check .`, `npm run build`, `npm run e2e`.

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
