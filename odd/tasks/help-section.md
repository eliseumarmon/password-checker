# Sección de ayuda

Objetivo: añadir dentro de la aplicación una ayuda breve, local y sin recursos remotos, para las tareas principales.
Rama: `feat/help-section` desde `main`. Fase 4. No depende de otros planes; conviene hacerlo después de `keyboard-accessibility` para no tocar a la vez la navegación. Entrega: `ask-on-risk`, previsión ~150 líneas. Solo frontend.
Comprobaciones: `npm run build` y `npm run e2e`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: planificado, sin empezar.

## Specs

- **S1 — Origen.** `docs/pendiente.md`: «y una sección de ayuda».
- **S2 — Contenido.**
  - Respuestas breves a: cómo exportar desde cada navegador; qué diferencia hay entre duplicado, conflicto y reutilización; qué guarda una sesión cifrada y qué no; cómo exportar a Bitwarden; cómo se tratan los códigos 2FA; y qué datos salen del equipo (ninguno).
  - **Supuesto:** la ayuda resume y no sustituye a `docs/flujo-usuario.md`, que sigue siendo la referencia. Cada respuesta corta remite a la pantalla donde se hace la tarea, para no mantener dos textos completos.
- **S3 — Privacidad.** Guía (§7): «No hacer peticiones a Internet para iconos, fuentes, analítica, imágenes o JS». La ayuda no carga nada externo y sus enlaces externos, si los hay, solo se abren tras un clic.
- **S4 — Ubicación.** **Supuesto:** una sección dentro de Ajustes, no una quinta pantalla, para no cambiar la navegación.

## Tasks

- [ ] T1 — S2-S4: sección de ayuda. RED primero en E2E: la sección existe, se navega con teclado y no hace peticiones externas. Ruta: inline.
- [ ] T2 — Documentación en `docs/flujo-usuario.md` (Ajustes). Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`: `SettingsView.vue` tiene tres filas informativas (sesión cifrada, modo móvil con ADB y exportación) y es el lugar natural de la ayuda. No depende de ninguna decisión pendiente. Ruta: inline.
