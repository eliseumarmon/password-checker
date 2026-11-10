# Evaluación local de fortaleza

Objetivo: detectar más patrones débiles sin conexión y explicar en la auditoría por qué se marca una contraseña, sin mostrarla nunca.
Rama: `feat/local-strength` desde `main`. Fase 2. No depende de otros planes: T1 y T2 son backend y pueden empezar en cualquier momento. Entrega: `ask-on-risk`, previsión ~300 líneas.
Comprobaciones: `python -m unittest discover -s tests` y `ruff check .`; con T3, también `npm run build` y `npm run e2e`. Estado: planificado; orden aprobado (n.º 3 de 8, L4); supuestos pendientes, se preguntan al empezar.

## Specs

- **S1 — Origen.** `docs/pendiente.md`: «Una evaluación local de fortaleza más completa.»
- **S2 — Reglas nuevas, en el dominio.**
  - Viven en `domain/strength.py`, solo con la biblioteca estándar de Python, como exige `tests/test_architecture.py`.
  - Nuevos motivos de debilidad:
    - secuencias y recorridos de teclado (por ejemplo, `abcd`, `4321`, `qwer`, `asdf`);
    - bloques repetidos (`abcabc`);
    - fechas y años;
    - palabras comunes con sustituciones simples (`p@ssw0rd`);
    - contraseñas que contienen el usuario o el nombre del sitio.
  - Las reglas actuales (longitud mínima de 12, recomendada de 14 y lista de contraseñas comunes) no cambian. **Supuesto:** las reglas nuevas solo añaden motivos; no retiran avisos que hoy existen.
  - **Supuesto:** no se añade una dependencia de estimación de fortaleza (del tipo zxcvbn). Habría que revisar su cadena de suministro y rompería la regla de dominio solo con la biblioteca estándar; queda como alternativa si las reglas propias se quedan cortas.
- **S3 — Motivos en la auditoría.**
  - La auditoría devuelve, para cada contraseña poco segura, uno o varios códigos de motivo (por ejemplo, `sequence` o `contains_username`) y la interfaz los muestra en español.
  - Nunca se devuelve ni se muestra la contraseña ni un fragmento de ella.
  - Guía (§2.1): «No utilizar verde para indicar que una contraseña es «segura» si únicamente ha superado reglas locales básicas. «Sin alertas locales» es más preciso.»
- **S4 — Fuera de alcance.** La comprobación de filtraciones (guía, §9: «Verificar filtraciones en bases externas (estado **No comprobado**, jamás «0»).»).

## Tasks

- [ ] T1 — S2: reglas en el dominio. RED primero en `tests/test_domain.py`, con un caso por regla y casos fuertes que no deben marcarse. Ruta: inline.
- [ ] T2 — S3: códigos de motivo en `audit`. RED primero en `tests/test_workspace_contract.py` y `tests/test_api.py`, comprobando que ninguna respuesta contiene la contraseña. Ruta: inline.
  - Riesgo: punto 3 (añade un campo a la respuesta de `/api/workspace`, que consume el frontend). Es un campo opcional nuevo, así que solo hay riesgo si cambia la forma de `weak`; se mantiene compatible.
- [ ] T3 — S3: motivos en la pantalla Auditoría. RED primero en E2E. Ruta: inline.
- [ ] T4 — Documentación en `docs/flujo-usuario.md` (paso 5). Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`:
  - `assess_strength()` combina longitud (12 y 14) con 27 contraseñas comunes y dos patrones: un carácter repetido seis o más veces, y prefijos como `12345`, `qwerty`, `asdf` o `abcd`.
  - `is_weak()` solo marca `OBVIOUS` y `SHORT`; `MODERATE` no avisa.
  - `audit.weak` es una lista de ids sin motivo.
  - No depende de ninguna decisión pendiente. Ruta: inline.
- **L4 (2026-11-10).** Revisión del plan contra `main` (`af881a5`), tras la Fase 1 y `review-filters`, a petición del usuario: «Planifica el resto de la fase2». Orden aprobado: «Pequeños primero (Recomendado)»; este plan es el n.º 3 de 8. Supuestos: «Justo antes de cada uno (Recomendado)», así que los supuestos y las decisiones pendientes se preguntan al empezar.
  - Nada desfasado en `domain/strength.py`.
  - Restricción nueva: `audit.weak` debe seguir siendo una lista de ids, porque la usa el orden «Riesgo» de «Todas» (`App.vue:81`, `alertsById`, de `review-filters`). Los motivos van en un campo aparte y opcional.
  - El dominio sigue sin dependencias externas (`tests/test_architecture.py`).
  - Su T3 se hace sobre la maqueta nueva de `audit-layout`.
  - Decisiones pendientes nuevas: si `MODERATE` (12 o 13 caracteres) sigue sin marcarse, y si los motivos nuevos cuentan como «poco segura» o solo informan; el idioma de los motivos, con D6 abierta.
