# Disposición de la Auditoría

Objetivo: que cada categoría de la Auditoría pueda consultarse con todo el espacio disponible, sin perder la vista general en escritorio y con un acordeón en móvil.
Rama: `feat/audit-layout` desde `main`. Fase 2. Depende de: `css-tokens` y `keyboard-accessibility` (Fase 1). Solo frontend. Entrega: `ask-on-risk`.
Comprobaciones: `npm run build` y `npm run e2e`. Estado: planificado, sin empezar; no está aprobado para implementarse.

## Specs

- **S1 — Origen.** Del usuario: «La vista de auditoría son 4 bloques ahora mismo 2x2 Hacer que cada fila esté en un desplegable y que ocupe el alto de la pantalla disponible.» Y, sobre un primer boceto en acordeón: «Eso que propones se parece a un acordeon y para la vista movil me gusta, pero para escritorio desaprovechas espacio.»
  - **Hoy** (`AuditView.vue`): cuatro bloques en una cuadrícula 2×2 (`audit-grid`). Las categorías son contraseñas reutilizadas, poco seguras, datos incompletos y vulneradas. Solo los grupos de contraseñas reutilizadas usan desplegables internos (`<details>`).
- **S2 — Escritorio.** Se mantiene la cuadrícula 2×2 como vista general. Cualquier categoría se puede ampliar: su listado ocupa todo el ancho y el alto restante de la ventana, con desplazamiento interno. Las demás quedan compactas y siguen visibles.
- **S3 — Móvil.** Acordeón vertical, con una sola categoría abierta a la vez.
- **S4 — Accesibilidad.** Cada categoría se amplía o se contrae con un `<button>` que lleva `aria-expanded` y `aria-controls`, operable con teclado. El foco no se pierde al ampliar ni al contraer.
- **S5 — Alcance.** Solo cambia la presentación. Las reglas que deciden qué contraseña es poco segura son de `local-strength`.

## Tasks

- [ ] T1 — S2, S4: ampliación en escritorio. RED primero en E2E (ampliar, contraer, teclado y foco). Ruta: inline.
- [ ] T2 — S3, S4: acordeón en móvil. E2E a 390 px. Ruta: inline.
- [ ] T3 — Documentación en `docs/flujo-usuario.md` y en la guía visual. Ruta: inline.

## Log

- **L1 (2026-11-04).** Origen: anotaciones del usuario sobre una conversación externa, pegada en la sesión; fragmentos en S1. La conversación propuso primero un acordeón también en escritorio. Tras la objeción del usuario, quedó la cuadrícula ampliable en escritorio y el acordeón en móvil. Comprobado en `main` (`ec8d167`): `audit-grid` con los cuatro bloques, y `<details>` solo en las contraseñas reutilizadas.
