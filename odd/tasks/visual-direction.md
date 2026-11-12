# Dirección visual

Objetivo: dar a la aplicación una identidad y una jerarquía propias, en lugar del aspecto monótono de hoy. La dirección se escribe en §1 y §2 de la [guía visual](../docs/guia-visual.md) y se aplica sobre las variables CSS de `css-tokens` y `scale-tokens`, más una escala de espaciado.
Rama: `feat/visual-direction`, encadenada sobre `refactor/scale-tokens` (`1d2ef00`), sin fusionar todavía. Usuario: «No es necesario subir. Podemos trabajar partiendo desde esta rama ya que van muy ligadas.» Fase 2, n.º 3. Entrega: `ask-on-risk`.
Comprobaciones: `npm run build`, `npm run e2e` y capturas antes y después de cada pantalla. Estado: planificado (L1); supuestos pendientes, se preguntan de uno en uno.

## Specs

- **S1 — Origen.** Del usuario, tras descartar la primera versión de `audit-layout`: «Sin duda no hay jerarquía, pero eso no es un problema de auditoría únicamente, veo que es un problema general de toda la aplicación. Es todo muy monótono.» Y: «La UI es igual de importante para entender lo que se está haciendo.» Método: la skill `frontend-design` (`.claude/skills/frontend-design`), añadida por el usuario: «A ver si nos inspira».
- **S2 — Encargo (por confirmar).** Tema, público y tarea principal de la pantalla, que la skill pide fijar con el cliente antes de diseñar.
- **S3 — Espaciado.** Una escala sobre la base de 4 px de la guía y pocas variables de función, no una por uso (`scale-tokens`, L6). Incluye retirar las cinco declaraciones de espaciado muertas anotadas allí.
- **S4 — Restricciones heredadas de la guía.**
  - Sin peticiones a Internet: ninguna fuente, icono ni imagen remota (§2.2, §7).
  - Estados identificados con texto e icono, nunca solo con color; contraste AA medido (§2.1).
  - Foco visible, objetivos táctiles de 44 px, `prefers-reduced-motion` (§2.2).
  - Tema oscuro por defecto; el tema claro es de la Fase 4 (`light-theme`), pero la paleta nueva debe poder tener su versión clara.
- **S5 — Fuera de alcance.** Rehacer la Auditoría (Fase 2, n.º 4, `audit-layout`), que se hará sobre esta dirección.

## Tasks

Se concretan cuando estén resueltos los supuestos. Previsión: guía (§1 y §2 reescritas, con bocetos), escala de espaciado y aplicación pantalla a pantalla con capturas.

## Log

- **L1 (2026-11-12).** Empieza el plan, a petición del usuario. Parte de `refactor/scale-tokens`, que deja en variables la tipografía y los radios, sin cambio visual y verificado. Pendiente: confirmar el encargo (S2) y después los demás supuestos, de uno en uno.
