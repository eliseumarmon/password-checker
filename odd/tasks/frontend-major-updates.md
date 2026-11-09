# Actualizaciones mayores del frontend (P12)

Objetivo: evaluar y, si compensa, aplicar las versiones mayores pendientes de `pinia` (4), `vite` (8) y `typescript` (7), con pruebas de compatibilidad. Corresponde al hallazgo H10 de la [auditoría de dependencias](../../docs/auditoria-dependencias.md#h10--líneas-mayores-del-frontend-sin-publicaciones-recientes).
Ramas: una por dependencia, desde `main`, cuando se aborde. Fase 1, después de `native-tables` (retira PrimeVue) y de `frontend-bundle` T1 (retira `vue-router`), para no actualizar lo que se va a retirar ni cruzar cambios en `package-lock.json`.
Comprobaciones por tarea: `npm run build` (incluye `vue-tsc`) y `npm run e2e` en `frontend/`; al cerrar, también `python -m unittest discover -s tests` y `ruff check .`. Estado: planificado, sin empezar; no está aprobado para implementarse.

## Specs

- **S1 — Origen.** P12 de [dependency-hardening](../done/dependency-hardening.md), literal: «Actualizaciones mayores del frontend (H10).» «`primevue` y `@primeuix/themes` no se actualizarán: la Fase 1 retira PrimeVue (decisión D1).» «`vue-router`, que no se usa, también se retira en la Fase 1.» «Quedan `pinia` 4, `vite` 8 y `typescript` 7. Siguen siendo opcionales y fuera de este plan: cada una, si se aborda, es una funcionalidad con su propio documento ODD y sus pruebas E2E.»
- **S2 — Encargo.** Del usuario (L1 de [roadmap-horizons](../done/roadmap-horizons.md)): «P12 se integra formalmente en Fase 1 con su propio paso. Desaparece de dependency-hardening.» «**P12:** mantenerla vinculada a la Fase 1, como ya está.» «**Vue Router:** retirarlo durante la Fase 1 y conservar Pinia.»
- **S3 — Aceptación de cada actualización.** Antes de actualizar, comprobar que la versión mayor sigue siendo la vigente y leer su guía de migración. Después, el build y las E2E en verde, sin cambios de comportamiento.

## Tasks

Cada tarea es una funcionalidad con su propia rama, como pedía P12. Este plan sustituye al documento ODD que P12 preveía para cada una.

- [ ] T1 — S1-S3: `pinia` 4 (hoy `^3.0.0`). Se conserva Pinia: la usa `useWorkspace` en `frontend/src/store.ts`. Rama `chore/pinia-4`. Ruta: inline. Riesgo: punto 5 (dependencias).
- [ ] T2 — S1-S3: `vite` 8 (hoy `^7.0.0`). Rama `chore/vite-8`. Ruta: inline. Riesgo: punto 5.
- [ ] T3 — S1-S3: `typescript` 7 (hoy `~5.9.0`). Antes, comprobar que `vue-tsc` (hoy `^3.0.0`) admite esa versión; si no, la tarea espera. Rama `chore/typescript-7`. Ruta: inline. Riesgo: punto 5.
- [x] T4 — Registrar en el Log las retiradas, cuando ocurran: `primevue` y `@primeuix/themes` (`native-tables` T4) y `vue-router` (`frontend-bundle` T1). Ruta: inline. Evidencia en L3 y L4.

## Log

- **L1 (2026-11-04).** P12 sale de `dependency-hardening` (su L33) a este plan, como paso propio de la Fase 1. Encargo completo en [roadmap-horizons](../done/roadmap-horizons.md), L1.
- **L2 (2026-11-04).** Decisión sobre `vue-router` y Pinia, tras comprobar el código: `vue-router` no tiene ningún import en `frontend/src` y Pinia sí se usa (`useWorkspace`). Se valoró conservar `vue-router` para la futura navegación multiusuario. La recomendación fue retirarlo, porque el multiusuario llega después de la bóveda (Fase 6) y reinstalarlo entonces es trivial. El usuario decidió retirarlo en la Fase 1 y conservar Pinia (S2).
- **L3 (2026-11-06).** `native-tables` T4 retira `primevue` y `@primeuix/themes` (`2a3f1ba`), así que este plan no los actualizará. Su T4 sigue abierta hasta que `frontend-bundle` T1 retire `vue-router`.
- **L4 (2026-11-09).** `frontend-bundle` T1 retira `vue-router` (`d56cdd9`), así que este plan no lo actualizará. Con esto se cierra su T4. Quedan `pinia` 4, `vite` 8 y `typescript` 7.
