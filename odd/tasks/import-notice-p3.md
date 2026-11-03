# Observaciones P3 de los avisos de importación

Resuelve las observaciones 1-5 de `docs/pendiente.md` (revisión de T4 del plan [importación: formato y origen](import-format-origin.md), registro L10) con las decisiones tomadas el 2026-11-03.
Una rama desde `main` (`fix/import-notice-p3`), test primero cuando aplique y un commit por tarea.

## Specs

- S1. Cada importación correcta con avisos empieza con «Ver detalles» contraído.
- S2. Los avisos se borran solo cuando una sesión `.pwc` se abre correctamente; si la apertura se cancela o falla, se conservan. Las demás operaciones no los tocan.
- S3. El botón de cierre de cada aviso tiene una etiqueta accesible propia: «Cerrar mensaje de error» y «Cerrar advertencia de importación». Se mantienen los roles `alert` y `status`.
- S4. Política de navegadores: características CSS Baseline Widely Available, sin fallback para navegadores que no las tengan. `:has()` se mantiene (Baseline Widely Available desde 2026).
- S5. `execute()` e `importFiles()` siguen separadas a propósito: solo la importación sustituye los avisos.

## Tareas

- [x] T1. «Ver detalles» vuelve a contraerse con cada importación correcta (S1): E2E con dos importaciones de 4 o más columnas descartadas.
- [x] T2. Abrir un `.pwc` correctamente borra los avisos; cancelar o fallar los conserva (S2): E2E de los tres casos.
- [x] T3. Etiquetas de cierre por tipo en `NoticeBase.vue` (S3): selectores E2E actualizados y prueba de que son distintas.
- [x] T4. Documentación (S2-S5): `docs/flujo-usuario.md` con el nuevo comportamiento al abrir un `.pwc`; política de navegadores en el README; comentario en `store.ts` sobre la separación intencionada; observaciones 1-5 retiradas de `docs/pendiente.md`.

Fuera de alcance: extraer código común de `execute()` e `importFiles()`. El plan de Safari trata de importar sus exportaciones, no del navegador, así que no afecta a S4.
Sin prueba E2E nueva para S4: «keeps the stacked warning and error usable in a short mobile viewport» ya cubre el apilado con teclado en un viewport móvil.

## Registro

- L1 (2026-11-03). Plan creado a partir de una propuesta verificada contra el código: `expanded` en `WarningNotice.vue` no se reinicia mientras el componente sigue montado; la apertura de `.pwc` usa `store.execute`, que no toca los avisos (`App.vue` `submitSession`); `NoticeBase.vue` usa «Cerrar aviso» para los dos tipos; `:has()` aparece en tres reglas de `style.css`, no solo en el apilado de avisos.
- L2 (2026-11-03). T1-T4 implementadas, una por commit, con test primero en T1-T3: «collapses the details again for each new import with a summary» (RED: `aria-expanded` seguía en `true`), «clears the warning only when a session opens successfully» (RED: el aviso seguía tras abrir la sesión; cubre contraseña errónea y cancelación en la confirmación) y la comprobación de etiquetas distintas en «stacks a later error above the warning» (RED: no existía «Cerrar mensaje de error»). Nueve selectores E2E pasan de «Cerrar aviso» a la etiqueta de su tipo. T4: `docs/flujo-usuario.md`, política de navegadores en el README, comentario de `store.ts` y retirada de las observaciones P3 1-5 de `docs/pendiente.md`. Verificación local: E2E 85 passed (83 + 2 nuevas), `npm run build` (vue-tsc + vite) OK.
