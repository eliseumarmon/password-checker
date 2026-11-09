# Actualizaciones mayores del frontend (P12)

Objetivo: evaluar y, si compensa, aplicar las versiones mayores pendientes de `pinia` (4), `vite` (8) y `typescript` (7), con pruebas de compatibilidad. Corresponde al hallazgo H10 de la [auditoría de dependencias](../../docs/auditoria-dependencias.md#h10--líneas-mayores-del-frontend-sin-publicaciones-recientes).
Rama: `chore/update-dependencies`, desde `main`, con un commit por paquete (L5). Fase 1, después de `native-tables` (retira PrimeVue) y de `frontend-bundle` T1 (retira `vue-router`), para no actualizar lo que se va a retirar ni cruzar cambios en `package-lock.json`.
Comprobaciones por tarea: `npm run build` (incluye `vue-tsc`) y `npm run e2e` en `frontend/`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: `pinia` 4 y `vite` 8 hechos (L5-L7); `typescript` 7 bloqueado hasta que las herramientas de Vue lo admitan.

## Specs

- **S1 — Origen.** P12 de [dependency-hardening](../done/dependency-hardening.md), literal: «Actualizaciones mayores del frontend (H10).» «`primevue` y `@primeuix/themes` no se actualizarán: la Fase 1 retira PrimeVue (decisión D1).» «`vue-router`, que no se usa, también se retira en la Fase 1.» «Quedan `pinia` 4, `vite` 8 y `typescript` 7. Siguen siendo opcionales y fuera de este plan: cada una, si se aborda, es una funcionalidad con su propio documento ODD y sus pruebas E2E.»
- **S2 — Encargo.** Del usuario (L1 de [roadmap-horizons](../done/roadmap-horizons.md)): «P12 se integra formalmente en Fase 1 con su propio paso. Desaparece de dependency-hardening.» «**P12:** mantenerla vinculada a la Fase 1, como ya está.» «**Vue Router:** retirarlo durante la Fase 1 y conservar Pinia.»
- **S3 — Aceptación de cada actualización.** Antes de actualizar, comprobar que la versión mayor sigue siendo la vigente y leer su guía de migración. Después, el build y las E2E en verde, sin cambios de comportamiento.

## Tasks

P12 proponía una rama por dependencia; el usuario decidió una sola, con un commit por paquete (L5). Este plan sustituye al documento ODD que P12 preveía para cada una.

- [x] T1 — S1-S3: `pinia` 4 (antes `^3.0.0`). Se conserva Pinia: la usa `useWorkspace` en `frontend/src/store.ts`. Ruta: inline. Evidencia en L5. Riesgo: punto 5 (dependencias).
- [x] T2 — S1-S3: `vite` 8 (antes `^7.0.0`). Ruta: inline. Evidencia en L6. Riesgo: punto 5.
- [ ] T3 — S1-S3: `typescript` 7 (hoy `~5.9.0`). Antes, comprobar que `vue-tsc` (hoy `^3.0.0`) admite esa versión; si no, la tarea espera. **Bloqueada** (L5): `vue-tsc` y `@vue/compiler-sfc` no funcionan con TS 7. Ruta: inline. Riesgo: punto 5.
- [x] T4 — Registrar en el Log las retiradas, cuando ocurran: `primevue` y `@primeuix/themes` (`native-tables` T4) y `vue-router` (`frontend-bundle` T1). Ruta: inline. Evidencia en L3 y L4.

## Log

- **L1 (2026-11-04).** P12 sale de `dependency-hardening` (su L33) a este plan, como paso propio de la Fase 1. Encargo completo en [roadmap-horizons](../done/roadmap-horizons.md), L1.
- **L2 (2026-11-04).** Decisión sobre `vue-router` y Pinia, tras comprobar el código: `vue-router` no tiene ningún import en `frontend/src` y Pinia sí se usa (`useWorkspace`). Se valoró conservar `vue-router` para la futura navegación multiusuario. La recomendación fue retirarlo, porque el multiusuario llega después de la bóveda (Fase 6) y reinstalarlo entonces es trivial. El usuario decidió retirarlo en la Fase 1 y conservar Pinia (S2).
- **L3 (2026-11-06).** `native-tables` T4 retira `primevue` y `@primeuix/themes` (`2a3f1ba`), así que este plan no los actualizará. Su T4 sigue abierta hasta que `frontend-bundle` T1 retire `vue-router`.
- **L4 (2026-11-09).** `frontend-bundle` T1 retira `vue-router` (`d56cdd9`), así que este plan no lo actualizará. Con esto se cierra su T4. Quedan `pinia` 4, `vite` 8 y `typescript` 7.
- **L5 (2026-11-09).** El usuario pide una sola rama: «En serio hay que actualizar en cada rama no puedes hacer chore/update-dependencies o algo asi?». Aprueba empezar: «Sí». Pide comprobar antes la compatibilidad: «compruebalo. cómo lo sabemos eso?» y «y consultando internet?».
  - **Comprobación en una copia aparte** (`main` en `57ddfa2`), instalando cada versión:
    - `pinia` 4.1.0: comprobación de tipos y compilación correctas.
    - `vite` 8.3.7: comprobación de tipos y compilación correctas.
    - `pinia` 4 y `vite` 8 juntos: `npm run e2e`, 147 de 147.
    - `typescript` 7.0.2: **falla**. `vue-tsc` da `ERR_PACKAGE_PATH_NOT_EXPORTED` en `./lib/tsc`, y `vite build` falla en `@vue/compiler-sfc`, al resolver los tipos importados de `defineProps`. El rango de `vue-tsc` (`typescript >=5.0.0`) admite TS 7 aunque no funcione.
  - **Fuentes consultadas:** [vuejs/language-tools #6124](https://github.com/vuejs/language-tools/issues/6124) y [la beta de TS 7.1](https://infoq.com/news/2026/11/typescript-7-1-beta), para TS 7; [las notas de Pinia 4.0.0](https://newreleases.io/project/npm/pinia/release/4.0.0); [la guía de migración de Vite](https://vite.dev/guide/migration.md). T3 queda bloqueada hasta que las herramientas de Vue admitan TS 7.
  - **T1:** `pinia` pasa a `^4.1.0`. Según sus notas, los cambios son ESM y `@vue/devtools-api` como dependencia obligatoria, que npm instala solo (8.2.1). `package-lock.json`: 5 paquetes retirados (`copy-anything`, `mitt`, `rfdc`, `speakingurl` y `superjson`), 1 añadido (`nostics`) y 5 cambiados. `npm audit`: 0 vulnerabilidades.
  - **Bundle** (medido antes de T1, sobre `main`): JS, 120 547 bytes (43 707 con gzip); con `pinia` 4, 120 567 (43 713). No cambia de forma apreciable.
  - Comprobaciones: `npm run build` correcto; `npm run e2e`, 147 de 147. Riesgo: punto 5 (dependencias).
- **L6 (2026-11-09).** T2: `vite` pasa a `^8.3.7`. `@vitejs/plugin-vue` 6.0.10 ya lo admite y no cambia. `vite.config.ts` no usa ninguna opción de `esbuild` ni de Rollup, así que no hace falta tocarlo. `package-lock.json`: Rolldown y sus binarios sustituyen a Rollup; `esbuild` sigue en el archivo como dependencia opcional de `vite` 8 (L7). `npm audit`: 0 vulnerabilidades.
  - **Bundle:** JS, 119 916 bytes (42 624 con gzip), frente a 120 567 (43 713); CSS, 16 430 (4183), frente a 16 463 (4171). La compilación pasa de 1,35 s a 0,34 s. Vite no avisa de ningún chunk de más de 500 kB.
  - **Estilos calculados** de los 20 estados: las únicas diferencias de presentación son 244 de `background-position` (`0% 0%` a `0px 0px`) en botones sin imagen de fondo, porque el nuevo minificador escribe `background:transparent` de otra forma. No cambia ni el color ni la imagen. El resto de diferencias, en `scroll-padding-*`, son el margen de 8 px de `keyboard-accessibility`, posterior a la captura de referencia.
  - Comprobaciones: `npm run build` correcto; `npm run e2e`, 147 de 147; `python -m unittest discover -s tests`, OK; `ruff check .`, sin avisos. Riesgo: punto 5 (dependencias); pendiente de verificación independiente.
- **L7 (2026-11-09).** Verificación y revisión de T1 y T2:
  - **Verificación independiente** (`93ee442` frente a `57ddfa2`, en copias limpias): sin bloqueos. `npm ci`, `npm ls --all` y `npm audit` correctos; en `package.json` solo cambian `pinia` y `vite`; todo lo añadido al `package-lock.json` procede de ellos. En total, en la rama: 33 paquetes retirados, 31 añadidos y 6 con otra versión. `npm run e2e`, 147 de 147. Comprobó además en el navegador que no hay violaciones de CSP, errores de consola ni peticiones fallidas al recorrer las pantallas y los diálogos, y confirmó que `typescript` 7 falla como dice L5.
  - **No probado:** el modo de desarrollo (`npm run dev`), porque `vite.config.ts` envía `/api` al puerto 8000, donde puede estar la instancia real del usuario.
  - **Revisión** (`review-risk` y `review-reliability`, con el consentimiento del usuario; riesgo punto 5, elevado a mano): aprobada y confirmada. Su única sugerencia, que L6 decía que Rolldown sustituía también a esbuild, se corrige: `esbuild` sigue como dependencia opcional de `vite` 8.
  - **Medición con gzip:** los tamaños de L6 se midieron con `zlib` de Node; otra herramienta da valores algo distintos. Los tamaños sin comprimir coinciden.
