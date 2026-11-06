# Tema claro

Objetivo: añadir un tema claro con contraste AA y un ajuste para elegir el tema.
Rama: `feat/light-theme` desde `main`. Fase 4. Depende de: `css-tokens` (variables de color) y `native-tables` (sin estilos de PrimeVue ni clase `app-dark`). Entrega: `ask-on-risk`, previsión ~250 líneas. Solo frontend.
Comprobaciones: `npm run build` y `npm run e2e`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`; capturas de los dos temas. Estado: planificado, sin empezar.

## Specs

- **S1 — Origen.** `docs/pendiente.md`: «tema claro; ajustes de idioma, tema y caducidad por inactividad». Este plan cubre el tema y su ajuste. El idioma (D6) y la caducidad por inactividad (D4) siguen pendientes de decisión (`docs/hoja-de-ruta.md`).
- **S2 — Paleta y contraste.**
  - Los valores de partida son la columna «Claro alternativo» de la guía (§2.1). La guía advierte: «Colores **propuestos**, sujetos a mediciones automáticas de contraste en implementación: AA en texto normal (≥ 4,5:1), ≥ 3:1 para componentes/indicadores significativos y foco visible.»
  - Aceptación, guía (§8): «Tema claro y oscuro | Contrastan textos y componentes, nunca depender solo del color». Se mide cada par en uso en los dos temas y se registra en el Log; ningún par puede quedar por debajo del umbral.
- **S3 — Ajuste.**
  - En Ajustes: «Sistema», «Oscuro» y «Claro».
  - **Supuesto:** por defecto se sigue `prefers-color-scheme` del sistema.
  - La preferencia se guarda en `localStorage` con el mismo tratamiento de errores que la barra lateral. Es una comodidad de presentación, no un dato sensible.
  - El tema se aplica antes de montar la aplicación, sin destello del otro tema. La CSP (`script-src 'self'`) impide un script en línea, así que se hace al inicio del bundle.

## Tasks

- [ ] T1 — S2: variables del tema claro y tabla de contrastes en el Log. Ruta: inline.
- [ ] T2 — S3: ajuste, preferencia y aplicación al arrancar. RED primero en E2E: la elección se mantiene al recargar; «Sistema» sigue la preferencia emulada; el almacenamiento no disponible no rompe la página. Ruta: inline.
- [ ] T3 — Capturas de todas las pantallas en los dos temas (script fuera del repositorio) y documentación en `docs/flujo-usuario.md` (Ajustes). Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`: los colores están escritos directamente en `style.css` (de ahí la dependencia de `css-tokens`); `index.html` fija `class="app-dark"` solo para PrimeVue. No depende de ninguna decisión pendiente. Ruta: inline.
- **L4 (2026-11-06).** Corrige L3: `app-dark` no era solo para PrimeVue. A través de esa clase, PrimeVue aplicaba `color-scheme: dark`, que oscurece los controles nativos (desplegables, casillas y barras de desplazamiento). Con `native-tables` T4, `style.css` declara `:root{color-scheme:dark}` e `index.html` ya no tiene la clase. **El tema claro tiene que cambiar también `color-scheme`**; si no, esos controles quedarían oscuros sobre fondo claro. La prueba `keeps native controls dark without any table library` (`tables.spec.ts`) fija el valor actual y habrá que adaptarla.
