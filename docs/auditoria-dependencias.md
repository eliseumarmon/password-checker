# Auditoría de dependencias y cadena de suministro

Diagnóstico de las dependencias del backend (Python/FastAPI) y del frontend (Vue/Vite), de la reproducibilidad de las instalaciones y de la CI. **No es una auditoría de seguridad de la aplicación**: solo valora cómo afectan las dependencias a Password Checker. El plan de actuación está en [dependency-hardening](../odd/tasks/dependency-hardening.md); se aprobó después de la auditoría y su estado se sigue allí.

- **Fecha y base:** 2026-11-03, rama `main` en `cfda098`. Ninguna dependencia, configuración ni código se modificó durante la auditoría.
- **Entornos examinados:** `.venv` local (Python 3.14.7 de 64 bits, pip 26.2.2), `frontend/node_modules` local (Node 24.21.0, npm 11.3.0) y el registro del último run de CI en `main` (`41639170151`: Python 3.12.15, Node 22, `ubuntu-24.04`).
- **Herramientas:** `npm audit`, `npm audit signatures`, `npm outdated`, `npm ls`, `pip list --outdated`, `pip check` y `pip show` (todas ya instaladas), la API pública de [OSV](https://osv.dev), la API JSON de PyPI y `gh api`. Los comandos están en [Evidencias reproducibles](#evidencias-reproducibles).
- **`pip-audit`:** no se ejecutó durante la auditoría, porque no estaba instalado. En su lugar se consultó OSV con las versiones exactas instaladas. Tras aprobarse el plan se instaló `pip-audit` 2.10.1 en el `.venv` y confirmó los mismos resultados (L5 de [dependency-hardening](../odd/tasks/dependency-hardening.md)).
- **Estado posterior:** H1 y H2 se corrigen en la rama `fix/cryptography-50`; H3 quedó fuera de alcance por decisión del usuario, porque no hay sesiones `.pwc` antiguas que conservar.

## Exposición real de Password Checker

La gravedad publicada de un aviso no equivale al riesgo aquí. Lo que condiciona la explotabilidad, comprobado en el código:

- **Solo escucha en loopback:** `uvicorn` en `127.0.0.1:8000` ([app.py](../app.py)); `TrustedHostMiddleware` solo admite `127.0.0.1` y `localhost` ([api.py:31](../backend/password_checker/api.py#L31)), lo que frena el DNS rebinding.
- **Peticiones de otros sitios:** `origin_guard` rechaza en `/api/` cualquier `Origin` ajeno o `Sec-Fetch-Site: cross-site` antes de leer el cuerpo ([api.py:35-46](../backend/password_checker/api.py#L35-L46)). **No cubre `/assets/`**, que sirve `StaticFiles` ([api.py:205](../backend/password_checker/api.py#L205)).
- **Criptografía usada:** solo `AESGCM` e `InvalidTag` de `cryptography` y `hash_secret_raw` (Argon2id) de `argon2-cffi` ([sessions.py:14-16](../backend/password_checker/infrastructure/sessions.py#L14-L16)). No se usan X.509, PKCS#7, CMS, PKCS#12, TLS ni QUIC.
- **Sin red saliente:** el backend no importa clientes HTTP ni sockets; [urls.py](../backend/password_checker/domain/urls.py) nunca resuelve direcciones.
- **Entradas no fiables:** los CSV y los `.pwc` que elige el usuario, que llegan como `multipart/form-data` y pasan por `python-multipart` y Starlette.
- **Frontend:** sin `v-html` ni `innerHTML`, sin recursos externos y con CSP `script-src 'self'` ([api.py:215](../backend/password_checker/api.py#L215)). El bundle solo incluye las dependencias de producción.
- **Repositorio público** en GitHub: la CI se ejecuta en `push` y `pull_request` (no `pull_request_target`), con `permissions: contents: read` y sin secretos.

## Resumen de prioridades

| ID | Hallazgo | Tipo | Riesgo real | Ámbito | Prioridad |
| --- | --- | --- | --- | --- | --- |
| [H1](#h1--cryptography-4607-con-avisos-abiertos-y-un-rango-que-impide-corregirlos) | `cryptography` 46.0.7 con avisos abiertos; el rango `<47` impide corregirlos | Confirmado | Bajo hoy (código afectado inalcanzable) | Producción | **Urgente** por el rango, no por los avisos |
| [H2](#h2--pruebas-de-cifrado-y-api-que-se-saltan-en-silencio) | Pruebas de cifrado y API que se saltan en silencio si falla una importación | Confirmado | Medio durante actualizaciones | Pruebas, CI | **Urgente** (previa a H1) |
| [H3](#h3--sin-prueba-de-compatibilidad-del-formato-pwc-entre-versiones) | Sin prueba de compatibilidad del formato `.pwc` entre versiones | Confirmado | Medio durante actualizaciones | Pruebas | **Urgente** (previa a H1) |
| [H4](#h4--instalaciones-python-no-reproducibles) | Instalaciones Python no reproducibles (sin bloqueo; Python y Node distintos en local y CI) | Confirmado | Medio | Producción, desarrollo, CI | Mantenimiento (alta) |
| [H5](#h5--sin-detección-de-vulnerabilidades) | Sin detección de vulnerabilidades: alertas de Dependabot desactivadas y ninguna auditoría en CI | Confirmado | Medio | CI, repositorio | Mantenimiento (alta) |
| [R1](#r1--límites-inferiores-que-admiten-versiones-vulnerables) | Los límites inferiores admiten versiones con avisos conocidos (`python-multipart`, Starlette, h11) | Potencial | Bajo hoy; medio en entornos antiguos | Producción, desarrollo | Mantenimiento |
| [H6](#h6--httpx-sin-publicaciones-desde-2024-y-obsoleto-para-testclient) | `httpx` sin versiones desde 2024 y obsoleto para `TestClient` | Confirmado | Bajo (rotura futura de pruebas) | Pruebas, CI | Mantenimiento |
| [H7](#h7--readme-instala-el-frontend-con-npm-install) | El README instala el frontend con `npm install` en lugar de `npm ci` | Confirmado | Bajo | Desarrollo | Mantenimiento |
| [H8](#h8--pytest-declarado-pero-no-usado-por-la-ci-ni-por-la-documentación) | `pytest` declarado pero no usado por la CI ni por la documentación | Confirmado | Bajo | Desarrollo, CI | Mantenimiento (decisión) |
| [H9](#h9--acciones-de-github-referenciadas-por-etiqueta-mutable) | Acciones de GitHub referenciadas por etiqueta mutable (`@v7`) | Confirmado | Bajo | CI | Opcional |
| [H10](#h10--líneas-mayores-del-frontend-sin-publicaciones-recientes) | Cuatro líneas mayores del frontend sin publicaciones recientes | Confirmado | Bajo hoy | Producción (bundle) | Opcional (planificar) |

Sin vulnerabilidades conocidas en el frontend: `npm audit` da 0 en producción y en desarrollo, las 119 entradas del lockfile tienen firma del registro verificada (85 con atestación) y ninguna está marcada como obsoleta.

## Inventario

### Backend (Python)

| Archivo | Dependencia directa | Rango | Instalada (local = CI) |
| --- | --- | --- | --- |
| `backend/requirements.txt` | `fastapi` | `>=0.115,<1` | 0.162.0 |
| | `uvicorn` | `>=0.30,<1` | 0.54.0 |
| | `python-multipart` | `>=0.0.9,<1` | 0.0.33 |
| | `cryptography` | `>=44,<47` | 46.0.7 (última publicada: 50.0.2) |
| | `argon2-cffi` | `>=23,<26` | 25.1.0 (última) |
| `backend/requirements-dev.txt` (incluye el anterior) | `pytest` | `>=8,<10` | 9.2.0 |
| | `httpx` | `>=0.27,<1` | 0.28.1 |
| | `ruff` | `==0.17.3` | 0.17.3 |

- **Transitivas de producción (15):** annotated-doc 0.0.5, annotated-types 0.8.0, anyio 4.16.0, argon2-cffi-bindings 26.1.0, cffi 2.1.1, click 8.5.0, h11 0.16.0, idna 3.20, opentelemetry-api 1.45.2, pycparser 3.12, pydantic 2.14.2, pydantic-core 2.50.2, starlette 1.10.0, typing-extensions 4.16.0, typing-inspection 0.4.4. En Windows se añade colorama 0.4.6 (por click).
- **Transitivas de desarrollo (6):** certifi, httpcore, iniconfig, packaging, pluggy y Pygments (por pytest y httpx), además de las de producción. En total, 29 paquetes en la CI (20 de producción).
- **No hay archivo de bloqueo.** El registro de la CI muestra exactamente las mismas versiones que el entorno local, pero solo porque ambos se instalaron hace poco: nada lo garantiza ([H4](#h4--instalaciones-python-no-reproducibles)).
- `pip check`: sin requisitos rotos.
- **Procedencia:** `opentelemetry-api` es una dependencia obligatoria nueva de FastAPI 0.162 (`opentelemetry-api>=1.44.0` en sus metadatos), publicada por OpenTelemetry (CNCF). Solo se instala la API, sin SDK ni exportadores (que FastAPI deja en el extra `opentelemetry`), así que no envía telemetría. Es un ejemplo de transitiva que entra sin intervención del proyecto.

### Frontend (npm)

| Dependencia | Tipo | Rango | Instalada | Última de su línea mayor | Última publicada |
| --- | --- | --- | --- | --- | --- |
| `vue` | producción | `^3.5.0` | 3.5.44 | 3.5.44 (2026-10-13) | 3.5.44 |
| `primevue` | producción | `^4.0.0` | 4.5.5 | 4.5.5 (2026-04-08) | 5.0.4 |
| `@primeuix/themes` | producción | `^1.0.0` | 1.2.5 | 1.2.5 (2025-09-27) | 3.1.0 |
| `pinia` | producción | `^3.0.0` | 3.0.4 | 3.0.4 (2025-11-05) | 4.1.0 |
| `vue-router` | producción | `^4.5.0` | 4.6.4 | 4.6.4 (2025-12-11) | 5.4.0 |
| `vite` | desarrollo | `^7.0.0` | 7.3.7 | 7.3.7 (2026-10-06) | 8.3.5 |
| `@vitejs/plugin-vue` | desarrollo | `^6.0.0` | 6.0.10 | 6.0.10 | 6.0.10 |
| `typescript` | desarrollo | `~5.9.0` | 5.9.3 | 5.9.3 (2025-09-30) | 7.0.2 |
| `vue-tsc` | desarrollo | `^3.0.0` | 3.3.13 | 3.3.14 | 3.3.14 |
| `@playwright/test` | desarrollo | `^1.64.1` | 1.64.1 | 1.64.1 | 1.64.1 |

- **`package-lock.json`:** `lockfileVersion` 3, 119 entradas (74 de desarrollo, 53 opcionales por plataforma; la CI en Linux instala 70). Todas se resuelven desde `https://registry.npmjs.org/` con `integrity` SHA-512; `node_modules` coincide con el lockfile (`npm ls` sin errores).
- **Scripts de instalación:** solo `esbuild` 0.28.2 (verifica su binario de plataforma) y `fsevents` (opcional, solo macOS). Ambos con firma verificada.
- La CI instala con `npm ci --no-audit --no-fund`: reproducible con el lockfile.

### CI y herramientas de build

- [`.github/workflows/tests.yml`](../.github/workflows/tests.yml): jobs `python`, `frontend` y `e2e` en `ubuntu-latest`.
- **Acciones:** `actions/checkout`, `actions/setup-python`, `actions/setup-node` y `actions/upload-artifact`, todas de GitHub y por etiqueta `@v7` (últimas publicadas: v7.0.1, v7.1.0, v7.1.0 y v7.0.2).
- **Navegador de pruebas:** `npx playwright install --with-deps chromium` descarga Chrome for Testing 156.0.8078.4 desde `cdn.playwright.dev` y paquetes del sistema con `apt`. La versión la determina `@playwright/test` del lockfile.
- **Ajustes de seguridad del repositorio** (`gh api`): escaneo de secretos y protección de push activados; **alertas y actualizaciones de seguridad de Dependabot desactivadas**.
- **Rama `main` sin protección** (`gh api repos/eliseumarmon/password-checker/branches/main/protection` devuelve 404): ninguna comprobación de CI es obligatoria para integrar.
- **Permisos de Actions:** `GITHUB_TOKEN` en solo lectura por defecto, sin poder aprobar PR, y `sha_pinning_required: false`.

## Hallazgos confirmados

### H1 — `cryptography` 46.0.7 con avisos abiertos y un rango que impide corregirlos

| Aviso | Versiones afectadas | Corregido en | Gravedad publicada | ¿Alcanzable en Password Checker? |
| --- | --- | --- | --- | --- |
| [GHSA-537c-gmf6-5ccf](https://github.com/pyca/cryptography/security/advisories/GHSA-537c-gmf6-5ccf): OpenSSL vulnerable incluido en los wheels ([aviso de OpenSSL de 2026-06-09](https://openssl-library.org/news/secadv/20260609.txt)) | 0.5.0 – 48.0.0 (wheel con OpenSSL 3.5.6) | 48.0.1 | Alta | **No.** Los CVE del aviso de OpenSSL afectan a PKCS#7, CMS, QUIC, OCSP, AES-OCB, AES-SIV/AES-GCM-SIV, ASN.1, PKCS#12, CMP, FFC-DH y verificación X.509. AES-GCM mediante la API AEAD no aparece. |
| [GHSA-g6cj-pr64-35w5](https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5) / CVE-2026-69247: oráculo de Bleichenbacher en el descifrado PKCS#7 | 44.0.0 – 49.x | 50.0.0 | Alta | **No.** No se usa PKCS#7. |
| [GHSA-jwv3-5hgf-82ww](https://github.com/pyca/cryptography/security/advisories/GHSA-jwv3-5hgf-82ww) / CVE-2026-69249: construcción exponencial de cadenas X.509 | hasta 48.x | 49.0.0 | Alta | **No.** No se verifican certificados. |
| [GHSA-m2h6-j472-rp4c](https://github.com/pyca/cryptography/security/advisories/GHSA-m2h6-j472-rp4c) / CVE-2026-69248: comodines DNS que escapan de `permittedSubtrees` | hasta 48.x | 49.0.0 | Moderada | **No.** No se verifican certificados. |

- **Problema estructural (confirmado):** el rango `cryptography>=44,<47` excluye todas las versiones corregidas, y la línea 46 no ha vuelto a publicar desde 46.0.7 (2026-04-08). Cualquier instalación nueva, incluida la CI, instala por diseño una versión con avisos. Si mañana apareciera un fallo que sí afectase a AES-GCM, la corrección también quedaría fuera del rango.
- **Ámbito:** producción. **Impacto sobre credenciales, TOTP, cifrado, `.pwc` e importaciones:** ninguno conocido con los avisos actuales; el cifrado de sesiones depende por completo de esta biblioteca.
- **Corrección recomendada:** `cryptography>=50.0.2,<51` tras [H2](#h2--pruebas-de-cifrado-y-api-que-se-saltan-en-silencio) y [H3](#h3--sin-prueba-de-compatibilidad-del-formato-pwc-entre-versiones).
- **Corrección aplicada:** `cryptography>=50.0.2`, **sin techo**, para no volver a bloquear correcciones futuras. La reproducibilidad queda para H4 (`constraints.txt`) y la detección, para H5. H3 quedó fuera de alcance. Decisión en L8 de [dependency-hardening](../odd/tasks/dependency-hardening.md).
- **Compatibilidad** ([CHANGELOG de 47.0.0 a 50.0.0](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)): ninguna ruptura afecta a `AESGCM` ni a `InvalidTag`. Los wheels pasan a OpenSSL 4.0.x. La versión 49.0.0 retira los wheels de Windows de 32 bits y de macOS x86_64: el entorno local es de 64 bits y hay wheels `win_amd64` y `manylinux_2_34_x86_64` para 50.0.2, pero un Mac Intel tendría que compilar desde el código fuente (con Rust). AES-GCM es un estándar determinista, así que el formato `.pwc` no debería cambiar; [H3](#h3--sin-prueba-de-compatibilidad-del-formato-pwc-entre-versiones) lo demuestra en lugar de suponerlo.

### H2 — Pruebas de cifrado y API que se saltan en silencio

[test_sessions.py:9-18](../tests/test_sessions.py#L9-L18), [test_session_limits.py:16](../tests/test_session_limits.py#L16) y [test_api.py:18-31](../tests/test_api.py#L18-L31) capturan `ImportError` y marcan las clases con `skipUnless(..., 'Optional ... dependencies not installed')`. Pero `cryptography`, `argon2-cffi`, FastAPI y `httpx` son **obligatorias** según `requirements*.txt`.

- **Fallo posible:** una actualización que rompa la importación (API retirada, wheel inexistente para la plataforma) hace que `unittest` termine con `OK (skipped=N)` y que el job `python` quede en verde sin haber probado el cifrado. El job `e2e` lo detectaría indirectamente, porque el backend no arrancaría, pero sin señalar la causa.
- **Estado actual:** 138 pruebas, ninguna saltada, en local y en CI.
- **Ámbito:** pruebas y CI. **Impacto:** podría integrarse una actualización de `cryptography` o `argon2-cffi` sin que se ejecute ninguna prueba de `.pwc`.
- **Corrección:** importar directamente y dejar que el fallo de importación sea un error.

### H3 — Sin prueba de compatibilidad del formato `.pwc` entre versiones

Las pruebas de sesión solo cifran y descifran dentro de la misma ejecución ([test_sessions.py:30-79](../tests/test_sessions.py#L30-L79)). Ninguna descifra un `.pwc` generado previamente, con valores conocidos.

- **Fallo posible:** si al actualizar cambiase la derivación de clave (Argon2id `time_cost=3`, `memory_cost=65536`, `parallelism=1`, `hash_len=32`; [sessions.py:31-34](../backend/password_checker/infrastructure/sessions.py#L31-L34)) o el cifrado, las pruebas seguirían pasando, pero los `.pwc` ya guardados no se podrían abrir.
- **Impacto:** pérdida de acceso a sesiones `.pwc` existentes, con sus credenciales y TOTP.
- **Corrección:** una prueba con una sesión ficticia cifrada con las versiones actuales, guardada en el código de la prueba (`.gitignore` excluye `*.pwc` y `*.json`). No altera el formato ni el cifrado.

### H4 — Instalaciones Python no reproducibles

- **Sin bloqueo:** las dependencias Python solo tienen rangos, ninguna transitiva está fijada y cada instalación (cada run de CI) resuelve la última versión permitida. Una publicación defectuosa o maliciosa de cualquiera de las 29 dependencias entra en la CI y en las instalaciones nuevas sin ningún cambio en el repositorio. El caso de `opentelemetry-api` muestra que el conjunto cambia sin intervención.
- **Versiones de Python distintas:** el `.venv` local es Python 3.14.7, la CI usa 3.12.15 y el README exige «3.12+». En esta máquina solo están Python 3.14 y 3.11 (`py -0`), así que no se puede reproducir la CI en local. Hay `.pyc` de 3.11 en `tests/__pycache__`, aunque el código exige 3.12 (sintaxis PEP 695).
- **Node distinto:** 24.21.0 en local y 22 en CI. `package.json` no declara `engines` y no hay `.nvmrc`. El lockfile reduce el impacto a diferencias de runtime y de npm.
- **Ámbito:** producción, desarrollo y CI. **Impacto:** indirecto, porque una dependencia comprometida del servidor tendría acceso a todo lo que el backend maneja en memoria (credenciales, TOTP, contraseña de sesión).

### H5 — Sin detección de vulnerabilidades

- `gh api repos/eliseumarmon/password-checker/vulnerability-alerts` devuelve 404: **alertas de Dependabot desactivadas** en un repositorio público. Las actualizaciones de seguridad también están desactivadas.
- La CI no audita nada (`npm ci --no-audit`) y no hay `dependabot.yml`.
- `main` no está protegida, así que aunque una auditoría fallase, nada impediría integrar.
- **Evidencia del efecto:** los avisos de [H1](#h1--cryptography-4607-con-avisos-abiertos-y-un-rango-que-impide-corregirlos) se publicaron entre junio y agosto de 2026 y no han aparecido en ninguna parte hasta esta auditoría.
- **Ámbito:** CI y repositorio.

### H6 — `httpx` sin publicaciones desde 2024 y obsoleto para `TestClient`

- `httpx` 0.28.1 (2024-12-06) es su última versión en PyPI.
- La CI emite `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` desde Starlette 1.2.0 ([PR #3291](https://github.com/Kludex/starlette/pull/3291)).
- **Fallo posible:** Starlette no está fijado. Una versión que retire el soporte de `httpx` rompería `test_api.py` en CI sin ningún cambio en el repositorio. Con [H2](#h2--pruebas-de-cifrado-y-api-que-se-saltan-en-silencio) la rotura sería silenciosa si se manifestara como `ImportError`.
- **Procedencia de `httpx2`** (comprobada): repositorio `pydantic/httpx2`, creado el 2026-05-11, 22 versiones y 2.16.0 como última (2026-10-21). Starlette lo incluye en su extra `full`. Sus archivos en PyPI **no tienen atestación PEP 740**.
- **Ámbito:** pruebas, sin efecto en producción.

### H7 — README instala el frontend con `npm install`

[README.md:15](../README.md#L15) usa `npm install`, que puede reescribir `package-lock.json` dentro de los rangos `^`. La sección de pruebas E2E y la CI usan `npm ci`. **Ámbito:** desarrollo.

### H8 — `pytest` declarado pero no usado por la CI ni por la documentación

- Ninguna prueba importa `pytest`; la CI y el README usan `python -m unittest`. Aun así, `requirements-dev.txt` lo instala junto con cuatro transitivas (iniconfig, packaging, pluggy, Pygments).
- Hay `.pyc` compilados por pytest 9.2.0 en `tests/__pycache__`, así que alguien lo usa o lo usó en local (quizá desde el IDE).
- **Decisión pendiente:** retirarlo, o documentarlo como ejecutor local opcional. **Ámbito:** desarrollo y CI.

### H9 — Acciones de GitHub referenciadas por etiqueta mutable

Las cuatro acciones son de GitHub y se fijan por etiqueta mayor (`@v7`), que puede moverse a otro commit.

- **Mitigaciones existentes:** `permissions: contents: read`, ningún secreto en el workflow y ningún `pull_request_target`.
- **Impacto de una acción comprometida:** alterar el resultado de la CI o leer código ya público. No podría escribir en el repositorio ni acceder a credenciales.
- **Ámbito:** CI, sin efecto en producción.

### H10 — Líneas mayores del frontend sin publicaciones recientes

- `primevue` 4.x no publica desde 2026-04-08, `@primeuix/themes` 1.x desde 2025-09-27, `pinia` 3.x desde 2025-11-05 y `vue-router` 4.x desde 2025-12-11; todas tienen una versión mayor posterior. `vite` 7.x y `typescript` 5.9 también están por detrás, pero `vite` 7 sigue recibiendo versiones (7.3.7, 2026-10-06).
- No hay vulnerabilidades conocidas, y la exposición es limitada (sin HTML dinámico, CSP estricta).
- **Riesgo:** que una corrección futura solo llegue a la versión mayor nueva y obligue a migrar con prisa.
- **Ámbito:** producción (bundle) y build.

## Riesgos potenciales

### R1 — Límites inferiores que admiten versiones vulnerables

`pip install -r` no actualiza un paquete que ya cumple el rango. Un entorno antiguo puede conservar versiones vulnerables aunque la CI (siempre limpia) instale las corregidas. Consultas a OSV sobre las versiones mínimas permitidas:

| Rango declarado | Versión mínima admitida | Avisos relevantes (corregido en) | ¿Alcanzable? |
| --- | --- | --- | --- |
| `python-multipart>=0.0.9` | 0.0.9 | 8 avisos, incluidos DoS en el parser multipart: [GHSA-59g5-xgcq-4qw3](https://github.com/advisories/GHSA-59g5-xgcq-4qw3) (0.0.18), [GHSA-pp6c-gr5w-3c5g](https://github.com/advisories/GHSA-pp6c-gr5w-3c5g) (0.0.27), [GHSA-5rvq-cxj2-64vf](https://github.com/advisories/GHSA-5rvq-cxj2-64vf) (0.0.30); el último corregido en 0.0.31 | Solo con peticiones del mismo origen o locales: `origin_guard` rechaza las de otros sitios antes de leer el cuerpo. DoS local. |
| `fastapi>=0.115` → `starlette>=0.37.2,<0.39` | 0.38.6 | [GHSA-wqp7-x3pw-xc5r](https://github.com/advisories/GHSA-wqp7-x3pw-xc5r): SSRF y robo de credenciales NTLM mediante rutas UNC en `StaticFiles` en Windows (1.1.0); [GHSA-86qp-5c8j-p5mr](https://github.com/advisories/GHSA-86qp-5c8j-p5mr): validación de `Host` (1.0.1); otros hasta 1.3.1 | **Plausible**, no reproducido: la app usa `StaticFiles` en `/assets/`, que `origin_guard` no protege, y se usa en Windows. Una página web visitada mientras la app está abierta podría provocar una autenticación NTLM saliente con una Starlette antigua. |
| `cryptography>=44` | 44.0.0 | Los cuatro avisos de [H1](#h1--cryptography-4607-con-avisos-abiertos-y-un-rango-que-impide-corregirlos) y tres más corregidos en 46.x (GHSA-79v4-65xg-pq4g, GHSA-m959-cc7f-wv43, GHSA-r6ph-v2qm-q3c2) | No consta que ninguno afecte a AES-GCM; los corrige la tarea P3. |
| `uvicorn>=0.30` → `h11>=0.8` | 0.14.0 | [GHSA-vqfr-h8mv-ghfj](https://github.com/advisories/GHSA-vqfr-h8mv-ghfj) (0.16.0) | Bajo: el contrabando de peticiones requiere un proxy intermedio, y no lo hay. |
| `pytest>=8` | 8.0.0 | [GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g) (9.0.3) | Solo desarrollo. |

- **Estado actual:** las versiones instaladas en local y en CI (python-multipart 0.0.33, starlette 1.10.0, h11 0.16.0) no están afectadas.
- **Corrección:** un archivo de restricciones (véase [Reproducibilidad](#reproducibilidad-y-política-de-versiones)) y límites inferiores por encima de las versiones corregidas.

### R2 — Descarga de navegadores en CI sin verificación propia

`playwright install` descarga binarios de `cdn.playwright.dev` y ejecuta `apt-get` con privilegios en el runner. La versión está fijada por el lockfile; no se ha comprobado si Playwright verifica sumas de los binarios descargados. Solo afecta a CI.

## Cuestiones no verificadas

- **`pip-audit` real:** durante la auditoría no se ejecutó; los resultados de Python proceden de OSV (`/v1/querybatch` con las versiones exactas). Su procedencia se comprobó: `pip-audit` 2.10.1 (2026-06-10), del repositorio `pypa/pip-audit`, con atestaciones PEP 740 en PyPI y 10 dependencias directas. **Resuelto después:** ejecutado en el `.venv` sobre 54 paquetes, coincide con OSV (L5 del plan).
- **Explotabilidad de GHSA-wqp7-x3pw-xc5r con Starlette < 1.1.0:** deducida del aviso y del código, sin prueba de concepto.
- **Retirada de `httpx` en `TestClient`:** Starlette lo marca como obsoleto, pero no se ha encontrado una fecha ni una versión de retirada.
- **Verificación de integridad de Playwright** al descargar navegadores.
- **Si Dependabot y el grafo de dependencias de GitHub interpretan un archivo de restricciones** como el propuesto en [Reproducibilidad](#reproducibilidad-y-política-de-versiones), o los requisitos actuales, que solo tienen rangos. `gh api …/dependency-graph/sbom` devuelve 404: no se sabe si porque el grafo está desactivado o por permisos. Lo previsible es que las alertas de Python cubran como mucho las dependencias directas.
- **Funcionamiento de `cryptography` 50.0.2** con Python 3.14 en Windows y con 3.12 en CI: hay wheels para ambos, pero no se han instalado.

## Reproducibilidad y política de versiones

### Python: fijar las transitivas

| Alternativa | Ventajas | Inconvenientes |
| --- | --- | --- |
| A. Mantener solo rangos (estado actual) | Ningún trabajo | No reproducible; las transitivas entran sin revisión ([H4](#h4--instalaciones-python-no-reproducibles)) |
| **B. Rangos en `requirements*.txt` + `backend/constraints.txt` con `==` para todas las dependencias (directas y transitivas), generado con `pip freeze` en un entorno limpio e instalado con `-c`** | Sin herramientas nuevas; los rangos siguen expresando la política y las restricciones, la versión exacta; una línea por paquete, fácil de revisar; un paquete solo de Windows (colorama) puede figurar sin efecto en Linux | Sin hashes; la regeneración es manual y conviene hacerla con Python 3.12 (reproducción de la CI) |
| C. pip-tools (`pip-compile --generate-hashes`) | Bloqueo con hashes y `--require-hashes` | Herramienta nueva; resuelve para la plataforma donde se ejecuta: un bloqueo generado en Linux omite colorama y falla en Windows con `--require-hashes` |
| D. uv (`uv pip compile --universal --generate-hashes` o `uv lock`) | Resolución universal con hashes, rápida | Binario y flujo nuevos para un proyecto de 29 paquetes |

**Recomendación: B.** Fijar las versiones exactas es lo que impide que una publicación nueva entre sin decisión. PyPI no permite reemplazar el archivo de una versión ya publicada, así que los hashes solo añaden protección frente a un compromiso del propio índice o del transporte. Si el proyecto evoluciona hacia la bóveda persistente descrita en [pendiente](pendiente.md#evolución-futura-gestor-de-secretos-con-bóveda-persistente), conviene reconsiderar D.

### npm

`npm ci` con `package-lock.json` (v3, `integrity` en todas las entradas) ya es reproducible en CI. Basta con usar `npm ci` también en el README ([H7](#h7--readme-instala-el-frontend-con-npm-install)) y mantener los rangos `^`, que solo se aplican al regenerar el lockfile. La separación entre producción y desarrollo de `package.json` es correcta: el bundle solo contiene `dependencies`.

### Separación de producción, desarrollo y pruebas

`requirements.txt` (producción) y `requirements-dev.txt` (pruebas y lint, incluye el anterior) bastan para este tamaño. El job `e2e` ya instala solo producción. Las restricciones (B) cubren ambos archivos. Queda la decisión sobre `pytest` ([H8](#h8--pytest-declarado-pero-no-usado-por-la-ci-ni-por-la-documentación)).

### Política de actualización propuesta

- **Avisos de seguridad:** valorar en un plazo de 7 días si el código afectado es alcanzable (como en este documento). Si lo es, corregir en una rama propia; si no, corregir en la siguiente actualización programada y registrar la justificación.
- **Actualización programada mensual:** regenerar `constraints.txt` y el lockfile dentro de los rangos, revisar el diff de versiones y pasar la CI completa.
- **Versiones mayores:** una funcionalidad y una rama por cada una, con su plan ODD. Nunca junto con otras actualizaciones.
- **Ruff:** seguir el procedimiento del [README](../README.md#pruebas).

### Detección en CI sin fallos imprevistos

- **Activar las alertas de Dependabot** en los ajustes del repositorio. No cambia el código ni la CI y avisa sin bloquear.
- **Añadir un workflow aparte** (`dependency-audit.yml`), no un paso dentro de `tests.yml`. Se ejecutaría con `schedule` semanal, `workflow_dispatch` y `pull_request` filtrado a los archivos de dependencias. Usaría `pip-audit` fijado a una versión exacta sobre `constraints.txt` (`--no-deps --disable-pip`, sin resolver ni instalar el proyecto) y `npm audit`, que funciona solo con el lockfile. `npm audit signatures` necesita los paquetes instalados (sin ellos devuelve `found no dependencies to audit`), así que el job ejecutaría antes `npm ci --ignore-scripts --no-fund` para no correr scripts de instalación.
- **Limitaciones operativas:** GitHub desactiva los workflows programados tras 60 días sin actividad en el repositorio, y solo avisa del fallo programado a quien modificó por última vez el cron. Sin protección de `main`, el resultado informa pero no bloquea.
- **Por qué así:**
  - Un aviso nuevo no rompe los PR ajenos a las dependencias: falla el run programado, que GitHub notifica.
  - En un PR que cambia dependencias, el autor ve el resultado de su propio cambio.
  - Los avisos verificados como no alcanzables se ignoran con `--ignore-vuln <ID>` y su justificación se registra en este documento, con la fecha de revisión.
- **Alternativa:** `actions/dependency-review-action` solo evalúa las dependencias que cambia un PR (nunca falla por cambios externos), pero no detecta avisos nuevos sobre dependencias ya presentes y depende del grafo de dependencias ([no verificado](#cuestiones-no-verificadas) con un archivo de restricciones).

## Evidencias reproducibles

Desde la raíz del repositorio, con el `.venv` local (en Windows, `.venv/Scripts/python.exe`):

```bash
python -m pip list --format=freeze        # versiones instaladas
python -m pip list --outdated             # cryptography 46.0.7 → 50.0.2
python -m pip show fastapi                # Requires: …, opentelemetry-api, …
python -m pip check                       # sin requisitos rotos
cd frontend
npm audit; npm audit --omit=dev           # 0 vulnerabilidades
npm audit signatures                      # 119 firmas verificadas, 85 atestaciones
npm outdated; npm ls --depth=0
```

- **OSV:** `POST https://api.osv.dev/v1/querybatch` con `{"package":{"name":…,"ecosystem":"PyPI"},"version":…}` por paquete, y `GET https://api.osv.dev/v1/vulns/<ID>` para el detalle.
- **CI:** `gh run view 41639170151 --log` (líneas `Successfully installed` y `StarletteDeprecationWarning`).
- **Dependabot:** `gh api repos/eliseumarmon/password-checker/vulnerability-alerts -i` (404 = desactivadas) y `gh api repos/eliseumarmon/password-checker --jq .security_and_analysis`.
