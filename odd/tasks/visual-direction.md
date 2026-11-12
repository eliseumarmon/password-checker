# Dirección visual

Objetivo: dar a la aplicación una identidad y una jerarquía propias, en lugar del aspecto monótono de hoy. La dirección se escribe en §1 y §2 de la [guía visual](../../docs/guia-visual.md) y se aplica sobre las variables CSS de `css-tokens` y `scale-tokens`, más una escala de espaciado.
Rama: `feat/visual-direction`, encadenada sobre `refactor/scale-tokens` (`1d2ef00`), sin fusionar todavía. Usuario: «No es necesario subir. Podemos trabajar partiendo desde esta rama ya que van muy ligadas.» Fase 2, n.º 3. Entrega: `ask-on-risk`.
Comprobaciones: `npm run build`, `npm run e2e` y capturas antes y después de cada pantalla. Estado: en curso (L14); entrega por partes: T1 y T2 primero; T1 en curso.

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

Rediseño completo con Hallmark (`/hallmark redesign`, profundidad `full`, alcance de aplicación) y el tema Console en gama graphite (L12). Se conservan el contenido y el cableado: manejadores, roles, etiquetas y clases que leen las pruebas E2E. Ninguna prueba se cambia para que pase el rediseño. Cada tarea termina con `npm run build`, la suite E2E completa y capturas de antes y después.

- [ ] T1 — Fuentes incluidas: Host Grotesk (400 y 500) y Atkinson Hyperlegible Mono (400 y 500), archivos `woff2` oficiales sin modificar, con sus licencias OFL, servidos por la propia aplicación. RED: prueba E2E de que las dos familias cargan y de que la página no pide nada fuera de su origen. Ruta: inline.
- [ ] T2 — Sistema Console: los colores, la tipografía, el espaciado (escala de 4 px, S3, con las cinco declaraciones muertas de `scale-tokens` L6), los radios (10, 6 y 4 px) y el suelo de Hallmark: bordes de campo a 3:1, `:active`, foco en ámbar, `overflow-x: clip`, la barra lateral sin animar su anchura y el sello en la primera línea del CSS. Ruta: inline.
- [ ] T3 — Cabecera: las cuatro cifras como un panel de lecturas cortado por filetes, con los valores en Atkinson Hyperlegible Mono (mismas etiquetas y clase `.metric`), la frase sin punto medio y las dos zonas fijas sin chocar (puerta 56). Ruta: inline.
- [ ] T4 — Credenciales: pestañas, filtros, tablas y tarjetas móviles en el material de Console. Chips en azul frío para lo que detecta la aplicación y en rojo para el conflicto; verbos en lugar de flechas («Comparar», «Editar»); iconos SVG en lugar de ↕ y ⚠. Ruta: inline.
- [ ] T5 — Diálogos y avisos: la comparación como diff dentro de la ventana de hoy (decisión del usuario: «Diff en la ventana (Recomendado)»; el despliegue bajo la fila pasa a `compare-resolution`), la ficha, la sesión, la confirmación y los avisos de error, importación y cambio. Ruta: inline.
- [ ] T6 — Auditoría, Papelera, Ajustes y bienvenida en el mismo material, sin recomponer la Auditoría (S5). Ruta: inline.
- [ ] T7 — Barrido de Hallmark (`sloplint --render --kept`, puertas juzgadas y revisión final en contexto limpio), documentación (`docs/guia-visual.md` §1 y §2 reescritas según Console, hoja de ruta) y cierre del plan. Ruta: inline.

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
- **L6 (2026-11-12).** `/hallmark audit frontend`, a petición del usuario. Sin cambios en el código. Género inferido: `modern-minimal`, con alcance de pantalla de aplicación (`--scope app`).
  - Linter (`sloplint --render --before`) sobre `frontend/src` y la pantalla inicial servida en el puerto 5173 con 37 registros ficticios: 19 FAIL, 79 REFLEX (77 de espaciado fuera de la escala de 4 px) y 18 WARN. El registro de lo que tiene hoy la pantalla está en `.hallmark/` (excluida de Git en local, como `.claude/`).
  - Hallmark solo renderiza URL, y la aplicación cambia de pantalla sin cambiar la URL; la Auditoría, Ajustes y los diálogos se juzgaron con capturas propias.
  - `puppeteer-core` 25.16.0 se instaló en una carpeta temporal fuera del repositorio, solo para el renderizado.
- **L7 (2026-11-12).** Alcance elegido por el usuario: «Rediseño completo» (`/hallmark redesign`, profundidad `full`, alcance de aplicación). Se conservan el contenido, el cableado y el armazón de pantallas (barra lateral y navegación móvil); se cambian el sistema y la composición de cada pantalla.
  - Reparto de temas (`theme.mjs deal`, semilla `local-tool-where-one-a003·3525948d·2026-11-12·r0`): Console (grafito, ámbar y azul frío), Ink (papel claro, tinta negra y verde azulado) y Dusk (paisaje fotográfico y vidrio). Propuesto: Console, porque su material es el diff y el registro de auditoría.
- **L8 (2026-11-12).** Sobre la propuesta de Console, el usuario preguntó si la skill permite crear un tema nuevo (sí: la vía `custom` de Hallmark, `references/direction.md`). Decisión: «Haz un tercer y último intento con estas directivas. Carga también la skill de frontend-design. Haz las preguntas que necesites para ir en la dirección acertada».
  - Qué falló en «Mesa de revisión», en palabras del usuario: «Pizarra + lavanda me parece demasiado de IA. No me gusta especialmente. El menú de passwordchecker plegable con el icono actual me gusta. El borde izquierdo de "credenciales" me parece demasiado IA. Puedes seguir las guías de material design aunque crees un tema nuevo.»
  - Consecuencias: se conserva la barra lateral plegable con la marca actual (◇); ninguna franja de color en el borde de un elemento seleccionado; Material Design (M3) como guía de sistema: roles de color, escala tipográfica, formas y capas de estado.
- **L9 (2026-11-12).** Respuestas del usuario, de una en una: esquema «Oscuro, como hoy»; tono «Suave»; color semilla «Propón tú (Recomendado)»; y, sobre la tipografía: «Me gustaba la opcion de atkinson hyperlegible para las contraseñas. Se puede conservar eso? Haz un artefacto para qcada opción. Una imagen vale más que mil palabras».
  - Atkinson Hyperlegible Mono se conserva en las tres, con un solo papel: contraseñas reveladas y códigos 2FA.
  - Paletas generadas con la librería de color de Material (`@material/material-color-utilities` 0.3.0, esquema `TonalSpot` oscuro; la 0.4.0 no carga en Node), más un color de advertencia armonizado con cada semilla. Fuera de la opción 3 su terciario lavanda.
  - Tres páginas de muestra con datos ficticios, privadas: «Bandeja de revisión» (lista y detalle, musgo dorado, Albert Sans), «Tablero de destinos» (montones por estado, rosa palo, Inclusive Sans y Figtree) y «Tabla serena» (tabla con chips y panel lateral, cian grisáceo, Lexend). Las tres conservan la barra lateral plegable con ◇ y no usan franjas en los bordes.
  - `sloplint --render --scope app` sobre las tres: 0 FAIL, una excepción justificada (39b, la marca y las filas de lista de 72 px) y avisos descartados con motivo.
- **L10 (2026-11-12).** Usuario: «Me gusta más tabla serena y aún así no termina de convencerme. Cómo se veria con console y graphite?». Cuarta muestra, privada: «Tabla serena en grafito», la estructura de la opción 3 con los colores, la tipografía (Host Grotesk 400 y 500, Atkinson Hyperlegible Mono para las contraseñas) y las formas de Console (6 px en controles, 4 px en chips, 10 px en paneles, filetes y sin sombras).
  - Significados de Console: ámbar para lo que hace la persona (acción principal, ubicación, filtros elegidos, «No funciona»); azul frío para lo que detecta la aplicación (copias, reutilizadas, débiles, incompletas, varias cuentas); rojo solo para el conflicto.
  - `sloplint`: limpio tras subir el borde del campo de búsqueda a 3:1 y quitar la negrita sintética (`font-synthesis: none`, pesos 400 y 500).
- **L11 (2026-11-12).** Usuario: «Mejor. Cómo se vería siguiendo únicamente el tema console con graphite sin lo que estamos diseñando nosotros?». Quinta muestra, privada: «Password Checker en Console», el rediseño que haría Hallmark solo con Console sobre la pantalla de hoy, sin Material ni las estructuras propuestas.
  - Se conservan la barra lateral, la cabecera, las pestañas, los filtros (búsqueda y tres selectores) y las columnas de Duplicados, con sus textos (salvo el punto medio de la cabecera, que pasa a dos frases).
  - Cambian: las cuatro cifras son un solo panel dividido por filetes, con los valores en Atkinson Hyperlegible Mono; la comparación deja la ventana emergente y se despliega bajo su fila como un diff, con `=` y `≠` en el margen y en rojo suave lo que difiere; los controles son el par de Console (ámbar relleno y contorno sobre grafito).
  - `sloplint`: 0 FAIL; la marca de 59 px como excepción y el aviso de la tabla en el móvil descartado, porque la pantalla real usa tarjetas en el móvil.
- **L12 (2026-11-12).** Sobre «Password Checker en Console», el usuario: «Me gusta infinitamente más». Dirección elegida: el tema Console de Hallmark en gama graphite, sin las estructuras propias (Material, chips, panel lateral). Es un tema del catálogo pedido por el usuario (`theme: Console (by request)`), no un tema a medida.
  - Decisión abierta: la muestra despliega la comparación bajo su fila, pero hoy es una ventana emergente de la que dependen unas 15 comprobaciones en 5 archivos E2E (`review`, `change-notices`, `dialogs`, `import-warnings`, `safari-totp`), y `compare-resolution` (Fase 2, n.º 9 y 10) ya rehace la comparación.
- **L13 (2026-11-12).** Comparación: «Diff en la ventana (Recomendado)». El diff de la muestra va dentro de la ventana de hoy y no se toca ninguna prueba; el despliegue bajo la fila pasa a `compare-resolution`. Tareas T1 a T7 definidas. Previsión: bastante más de 400 líneas, así que se pregunta la forma de entrega.
- **L14 (2026-11-12).** Entrega: «Por partes (Recomendado)». Primero T1 y T2, que cambian el aspecto de toda la aplicación, y se enseñan al usuario antes de seguir con T3 a T7.
