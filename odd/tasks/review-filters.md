# Filtros y orden de la revisión

Objetivo: añadir el filtro por estado y el selector de orden junto a la búsqueda, ordenar «Todas» por riesgo y por URL, y conservar los filtros entre visitas.
Rama: `feat/review-filters` desde `main`. Fase 2. Depende de: `native-tables` (reutiliza su módulo de ordenación). Entrega: `ask-on-risk`, previsión ~250 líneas. Solo frontend.
Comprobaciones: `npm run build` y `npm run e2e`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: planificado, sin empezar.

## Specs

- **S1 — Filtro por estado.** `docs/pendiente.md`: «filtro por estado y selector de orden junto a la búsqueda».
  - Un selector con «Todos», «Pendiente», «Revisada», «Verificada» y «No funciona» (las etiquetas de `labelReview`), junto a la búsqueda y al filtro de tipo.
  - En «Duplicados», un grupo cumple el filtro si alguno de sus miembros tiene ese estado. Hoy «Solo pendientes» ya funciona así con `pending`.
  - **Supuesto, a confirmar:** el selector sustituye la casilla «Solo pendientes», que equivale a elegir «Pendiente».
- **S2 — Orden.** `docs/pendiente.md`: «en «Todas», orden por riesgo y por URL, con los grupos de una misma URL contiguos».
  - El selector de orden ofrece «Nombre» (el actual), «Riesgo» y «URL».
  - Riesgo: **supuesto** — más alertas de auditoría primero (reutilizada, poco segura, incompleta, según `audit` de la respuesta) y, a igualdad, por nombre. Nunca se usa la contraseña en el navegador para calcularlo.
  - URL: por host y después por ruta, de modo que los registros de una misma URL quedan contiguos.
  - **Supuesto:** el selector fija el orden de partida; pulsar una cabecera de la tabla lo sustituye, como hoy.
- **S3 — Continuidad.** `docs/pendiente.md`: «continuidad de filtros».
  - El tipo, el estado y el orden se recuerdan entre recargas en `localStorage`, con el mismo tratamiento de errores que la barra lateral contraída (`App.vue`).
  - **Supuesto:** el texto de búsqueda no se guarda, porque puede contener usuarios y la guía (§7) pide: «No guardar credenciales en `localStorage`, `sessionStorage`, `IndexedDB` ni cachés del navegador».
- **S4 — Sin cambios en el backend.** Todo se calcula con el estado que ya recibe el frontend (`records`, `groups`, `audit`).

## Tasks

- [ ] T1 — S1: filtro por estado. RED primero en E2E (cada estado en «Todas» y en «Duplicados»). Ruta: inline.
- [ ] T2 — S2: selector de orden por riesgo y por URL, reutilizando el comparador de `native-tables`. RED primero en E2E con datos ficticios de riesgo conocido. Ruta: inline.
- [ ] T3 — S3: continuidad. RED primero en E2E (recargar conserva tipo, estado y orden, pero no la búsqueda), con almacenamiento no disponible incluido. Ruta: inline.
- [ ] T4 — Documentación en `docs/flujo-usuario.md`. Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`: los filtros viven en `App.vue` (`filterType`, `query`, `pendingOnly`) y se aplican con `matches()`; `audit` ya trae los ids de reutilizadas, poco seguras e incompletas. No depende de ninguna decisión pendiente. Ruta: inline.
