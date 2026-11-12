# Tipografía, radios y espaciado en variables CSS

Objetivo: sustituir los tamaños de letra, la familia tipográfica, los pesos, las alturas de línea, los radios y los espacios escritos directamente en `frontend/src/style.css` por variables CSS en `:root`, sin ningún cambio visual. Es la base para probar la nueva dirección visual tocando pocas líneas.
Rama: `refactor/scale-tokens` desde `main` (`4ef1105`). Continúa `css-tokens` (Fase 1), que solo cubrió los colores. Fase 2, n.º 2: va antes de la dirección visual y de rehacer la Auditoría (L3). Entrega: `ask-on-risk`.
Comprobaciones: `npm run build` y `npm run e2e` en `frontend/`, más la comparación de estilos calculados de S2. Estado: en curso (L3); T1 pendiente.

## Specs

- **S1 — Origen.** Del usuario, tras descartar `audit-layout`: «Sin duda no hay jerarquía, pero eso no es un problema de auditoría únicamente, veo que es un problema general de toda la aplicación. Es todo muy monótono. Menos mal que usamos css-token para poder experimentar sin tocar mucho.» Y: «hacemos un css-tokens de nuevo?»
- **S2 — Variables.** Cada `font-size`, `font-family`, `font-weight`, `line-height` y `border-radius` literal de `style.css` pasa a `var(--…)`, con la variable definida en `:root`.
  - Nombres por función, no por valor, como en `css-tokens`: `--type-…` para tamaños de texto, `--icon-…` para los iconos de texto que se dimensionan con `font-size`, `--weight-…`, `--leading-…`, `--font-…` y `--radius-…`.
  - Hoy: 34 `font-size` de 13 valores, 17 `border-radius` de 8 valores, 9 `font-weight`, 4 `line-height` y 1 `font-family`.
  - Aceptación: fuera de `:root` no queda ningún literal de esas propiedades, comprobable con `grep`. Se permiten `0`, `inherit` y `font:inherit`.
- **S3 — Espaciado en variables.** Usuario: «Los espaciados también deberían entrar. Aunque sea más trabajo.» Cada valor en píxeles de `padding`, `margin`, `gap`, `column-gap` y `scroll-padding` pasa a `var(--…)`.
  - Hoy: 185 valores en píxeles en `padding`, `margin` y `gap`, de 34 valores distintos, más los de `scroll-padding`.
  - Nombres por función, agrupando los usos que cumplen el mismo papel: margen lateral de la página, relleno de tarjetas y diálogos, relleno de controles, separación entre elementos apilados o en línea… Si hoy una misma función usa valores distintos, cada valor lleva su variable y la diferencia se anota (S5).
  - Los márgenes negativos que anulan un relleno se expresan a partir de la variable de ese relleno, con `calc(-1 * var(--…))`, para que cambien juntos.
  - Fuera: las posiciones (`top`, `bottom`, `right`) y los tamaños (`width`, `height`, `min-height`), que no son espaciado.
  - Aceptación: fuera de `:root` no queda ningún valor en píxeles en esas propiedades, salvo dentro de `calc()` con variables; comprobable con `grep`. Se permite `0`.
- **S4 — Sin cambio visual.** Usuario, al elegir entre conservar los valores o reducirlos ya a una escala: «Sí» a conservarlos. Cada valor se mantiene aunque difiera de la guía; elegir la escala es una decisión de la dirección visual.
  - Aceptación: estilos calculados idénticos entre `main` y la rama en todos los elementos visibles, a 1440 × 900 y 390 × 844, en la bienvenida, Credenciales (Duplicados y Todas), Auditoría, Papelera, Ajustes y los diálogos de comparación, ficha, sesión y confirmación. Es el método de `css-tokens` (L6), más fiable que comparar píxeles. El script vive fuera del repositorio.
- **S5 — Diferencias con la guía, anotadas y no corregidas.** La guía visual (§2.2) pide textos de 13 px o más, espaciado sobre una base de 4 px y radios de 8, 12 y 16 px. El código usa textos de 11 y 12 px, ocho radios distintos y espacios fuera de la base de 4 px (5, 6, 7, 9, 10, 15 px…). Cada diferencia queda en el Log como entrada para la dirección visual.
- **S6 — Fuera de alcance.**
  - **La escala tipográfica, la identidad y la jerarquía.** Son la dirección visual, que reescribirá §1 y §2 de la guía.
  - **`feat/audit-layout`.** Aparcada sin fusionar (su L10).

## Tasks

- [ ] T1 — S2, S5: inventario y correspondencia valor → variable de tipografía y radios en el Log: cada literal, dónde se usa, la variable elegida y su diferencia con la guía. Ruta: inline. Sin código.
- [ ] T2 — S2, S4: sustitución de tipografía y radios en `style.css` y comparación de estilos calculados entre `main` y la rama. Excepción a RED: refactorización sin cambio de comportamiento; las comprobaciones son S2 (`grep`), S4 (estilos calculados), `npm run build` y `npm run e2e`. Riesgo: ninguna prueba versionada detecta una regresión visual, así que lleva verificación independiente. Ruta: inline.
- [ ] T3 — S3, S5: inventario del espaciado en el Log: cada valor, dónde se usa, la función que cumple y la variable elegida. Ruta: inline. Sin código.
- [ ] T4 — S3, S4: sustitución del espaciado y comparación de estilos calculados, con las mismas comprobaciones y la misma verificación independiente que T2. Ruta: inline.
- [ ] T5 — Documentación: la guía visual (§2.2) dice que los valores viven en variables y enlaza las diferencias de S5. Ruta: inline.

## Log

- **L1 (2026-11-12).** El usuario descarta `audit-layout` tras probarlo y propone experimentar con la interfaz de toda la aplicación. Análisis de `style.css` en `feat/audit-layout`: `css-tokens` convirtió en variables solo los colores (unas 45). Quedan a mano 14 tamaños de letra en 36 sitios, 7 radios, la familia tipográfica del sistema y unos 32 valores de espaciado. La guía visual (§2.2) ya fija una escala, un espaciado base y tres radios que el código no sigue, y su §1 no define identidad ni jerarquía.
- **L2 (2026-11-12).** Decisiones del usuario:
  - Aparcar `feat/audit-layout`: «Sí. Me parece que es lo mejor. La UI es igual de importante para entender lo que se está haciendo.»
  - Conservar los valores actuales en las variables, sin cambio visual: «Sí».
  - Sobre la guía, preguntó «deberíamos establecer una guia visual?». Ya existe, `docs/guia-visual.md`; la dirección visual reescribirá su §1 y su §2 en lugar de crear otra.
  - Rama `refactor/scale-tokens` desde `main` (`4ef1105`). Recuento en `main`: 34 `font-size` (13 valores), 17 `border-radius` (8 valores), 9 `font-weight`, 4 `line-height`, 1 `font-family`. El espaciado queda fuera (S5). Previsión: ~60 líneas cambiadas, porque las líneas de `style.css` son muy largas.
- **L3 (2026-11-12).** Decisiones del usuario: «Sí, añádelo a la Fase 2. Los espaciados también deberían entrar. Aunque sea más trabajo.»
  - Hoja de ruta: este plan pasa a ser el n.º 2 de la Fase 2, seguido de la dirección visual (plan por escribir) y de rehacer la Auditoría. El resto de la Fase 2 va después, para no rehacer el estilo de cada plan.
  - El espaciado entra (S3), con su inventario (T3) y su sustitución (T4) separados de los de tipografía y radios. Recuento en `main`: 185 valores en píxeles en `padding`, `margin` y `gap`, de 34 valores distintos. Previsión total: ~100 líneas cambiadas; las líneas de `style.css` son muy largas, así que cada una agrupa muchos cambios.
