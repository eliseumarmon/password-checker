# Dirección visual

Objetivo: dar a la aplicación una identidad y una jerarquía propias, en lugar del aspecto monótono de hoy. La dirección se escribe en §1 y §2 de la [guía visual](../../docs/guia-visual.md) y se aplica sobre las variables CSS de `css-tokens` y `scale-tokens`, más una escala de espaciado.
Rama: `feat/visual-direction`, encadenada sobre `refactor/scale-tokens` (`1d2ef00`), sin fusionar todavía. Usuario: «No es necesario subir. Podemos trabajar partiendo desde esta rama ya que van muy ligadas.» Fase 2, n.º 3. Entrega: `ask-on-risk`.
Comprobaciones: `npm run build`, `npm run e2e` y capturas antes y después de cada pantalla. Estado: en curso (L5); «Mesa de revisión» descartada; se valora usar la skill `hallmark`.

## Specs

- **S1 — Origen.** Del usuario, tras descartar la primera versión de `audit-layout`: «Sin duda no hay jerarquía, pero eso no es un problema de auditoría únicamente, veo que es un problema general de toda la aplicación. Es todo muy monótono.» Y: «La UI es igual de importante para entender lo que se está haciendo.» Método: la skill `frontend-design` (`.claude/skills/frontend-design`), añadida por el usuario: «A ver si nos inspira».
- **S2 — Encargo.** Confirmado por el usuario: «Me encaja» (L2).
  - **Tema:** limpiar y revisar las contraseñas exportadas de varios navegadores antes de llevarlas a Bitwarden, con una auditoría local de su seguridad.
  - **Público:** una persona sola, con sus propias contraseñas, en su equipo y sin conexión. Son sesiones largas, de cientos de registros, que puede retomar otro día.
  - **Tarea principal:** decidir registro a registro qué se queda, qué se fusiona y qué va a la papelera, hasta poder exportar con confianza. La pantalla debe dejar claro en todo momento qué falta por resolver y qué es urgente.
- **S3 — Espaciado.** Una escala sobre la base de 4 px de la guía y pocas variables de función, no una por uso (`scale-tokens`, L6). Incluye retirar las cinco declaraciones de espaciado muertas anotadas allí.
- **S4 — Restricciones heredadas de la guía.**
  - Sin peticiones a Internet: ninguna fuente, icono ni imagen remota (§2.2, §7).
  - Estados identificados con texto e icono, nunca solo con color; contraste AA medido (§2.1).
  - Foco visible, objetivos táctiles de 44 px, `prefers-reduced-motion` (§2.2).
  - Tipografía: una fuente propia con licencia libre, incluida en la aplicación como `woff2` y servida por ella misma; nunca desde Internet. La CSP de la página (`default-src 'self'`) ya lo permite (L3).
  - Tema oscuro por defecto; el tema claro es de la Fase 4 (`light-theme`), pero la paleta nueva debe poder tener su versión clara.
- **S5 — Fuera de alcance.** Rehacer la Auditoría (Fase 2, n.º 4, `audit-layout`), que se hará sobre esta dirección.

## Tasks

Se concretan cuando estén resueltos los supuestos. Previsión: guía (§1 y §2 reescritas, con bocetos), escala de espaciado y aplicación pantalla a pantalla con capturas.

## Log

- **L1 (2026-11-12).** Empieza el plan, a petición del usuario. Parte de `refactor/scale-tokens`, que deja en variables la tipografía y los radios, sin cambio visual y verificado. Pendiente: confirmar el encargo (S2) y después los demás supuestos, de uno en uno.
- **L2 (2026-11-12).** Encargo (S2) propuesto a partir del README y del flujo de usuario. Usuario: «Me encaja».
- **L3 (2026-11-12).** Tipografía. Opciones: una fuente propia incluida en la aplicación o solo las del sistema, que cambian según el equipo. Usuario: «Fuente propia incluida (Recomendado)». Coste previsto: 50–150 KB y un archivo de licencia; hoy el JS pesa 117 KB y el CSS 16 KB.
- **L4 (2026-11-12).** Propuesta «Mesa de revisión», publicada como página privada para el usuario (artefacto `Dp98igUNmxK4wEk72UndCs`, con datos ficticios). Contenido:
  - **Elemento principal:** la cabecera dice con una frase lo que falta («Te quedan 37 registros por revisar»), propone el siguiente paso y muestra una barra con la composición del trabajo, en lugar de cuatro métricas iguales.
  - **Tipografía:** Atkinson Hyperlegible Next, y su versión Mono para secretos revelados y códigos 2FA. Elegida porque distingue `lI1` y `O0`, y la tarea es comprobar usuarios y URL letra a letra. Licencia OFL con nombres reservados: se incluyen los archivos oficiales sin modificar. Cinco tamaños (14, 16, 18, 24 y 36 px), ninguno por debajo de 14.
  - **Color:** fondo de tinta verde pizarra; lavanda solo para acciones, foco y ubicación; coral (crítico) y ámbar (atención) para lo pendiente; lo resuelto en gris con ✓, sin verde. Contraste AA en todos los pares de texto (mínimo 5,9:1).
  - **Escalas:** espaciado de 4, 8, 12, 16, 24, 32 y 48 px; radios de 4 px (controles), 8 px (paneles) y 12 px (lo que flota).
  - **Principios:** una frase dice lo que falta; lo resuelto se aparta; menos cajas; el estado se ve en el borde de la fila; leer antes que decorar.
  - Revisada contra los rasgos genéricos que señala la skill: sin fondo crema ni casi negro con un acento ácido, sin tarjetas iguales, sin etiquetas en mayúsculas ni separadores de punto medio.
- **L5 (2026-11-12).** El usuario descarta la propuesta: «No me gusta. He añadido una nueva skill. Echa un vistazo». Skill nueva: `hallmark` (`.claude/skills/hallmark`), que en un diseño existente solo se usa si el usuario la nombra (`/hallmark audit <ruta>` o `/hallmark redesign <ruta>`).
