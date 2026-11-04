# Hoja de ruta: horizontes futuros y reubicación de los pendientes de dependencias

Objetivo: que la hoja de ruta presente el multiusuario, la compartición y la sincronización como horizontes previstos y no como funcionalidades descartadas; que el diseño de la bóveda estudie esa evolución sin incluirla en la primera versión; y que P10, P12 y P13 salgan de `dependency-hardening`, que pasa a `odd/done`.
Rama: `docs/roadmap-horizons`, encadenada sobre `docs/odd-done`, que mueve los planes completados a `odd/done`. No se integra en `main` sin la aprobación del usuario. Entrega: `single-pr`, solo documentación, previsión de unas 200 líneas.
Comprobaciones: enlaces relativos y anclas válidos, y lectura estructural. No hay código ni pruebas. Estado: **completado** (L4): integrado en `main`.

## Specs

- **S1 — Horizontes futuros en la hoja de ruta.** «Reformular `hoja-de-ruta.md` para que multiusuario, compartición y sincronización figuren como horizontes futuros previstos, no como funcionalidades descartadas.» «No es necesario crear una Fase 7 ni planificar todavía el multiusuario.» «Mantén separados el alcance de la primera bóveda y la evolución empresarial.»
- **S2 — Diseño de la bóveda preparado para esa evolución.**
  - «No quiero implementarlo todavía ni ampliar el alcance de la primera bóveda persistente. Primero desarrollaremos una bóveda personal, local y cifrada.»
  - «Sin embargo, quiero que su diseño tenga en cuenta la evolución posterior hacia cuentas de usuario, bóvedas personales y de organización, departamentos, permisos y compartición de secretos. No se trata de implementar ahora esas capacidades, sino de estudiar las implicaciones arquitectónicas y evitar decisiones que dificulten innecesariamente esa evolución.»
  - «Ampliar `vault-discovery` (T4, T5 y T6) para evaluar la evolución hacia múltiples bóvedas, propietarios y una arquitectura de claves compatible con futuras capacidades multiusuario. No implementarlas todavía.»
- **S3 — P12 en la Fase 1.** «P12 se integra formalmente en Fase 1 con su propio paso. Desaparece de dependency-hardening.» «**P12:** mantenerla vinculada a la Fase 1, como ya está.» «**Vue Router:** retirarlo durante la Fase 1 y conservar Pinia.»
- **S4 — P13 en la Fase 6.** «P13 se integra en la Fase 6 con su propio paso cuando se implemente la bóveda. Desaparece de dependency-hardening.» «**P13:** conservarla pendiente con el disparador actual, para reevaluarla durante el diseño de la bóveda.»
- **S5 — Cierre de `dependency-hardening`.** «Dependency hardening pasa a done.» **Supuesto:** P10 también sale del plan, a uno propio, porque un plan en `odd/done` no puede tener tareas abiertas y P10 se resuelve ahora (S6).
- **S6 — DT4 y P10 antes de la Fase 1.** «**DT4 y P10:** estoy de acuerdo en resolverlos ahora, siguiendo el flujo habitual de pruebas y revisión independiente.» «Realiza primero las correcciones documentales y prepara DT4 y P10 según el flujo habitual, sin integrar cambios en `main` hasta mi aprobación.» En esta rama solo se sitúan en la hoja de ruta. Se implementan en sus propias ramas, encadenadas sobre esta: `fix/csv-header-line` (DT4) y `ci/pin-actions-sha` (P10).

## Tasks

- [x] T1 — S1, S2: en `docs/hoja-de-ruta.md`, horizontes futuros y orientación de D7; en `odd/tasks/vault-discovery.md`, ampliar T4-T6. Ruta: inline (solo documentación, sin disparadores de delegación). Commit: el de «present multiuser, sharing and sync as future horizons».
- [x] T2 — S3-S6: planes propios para P10 (`actions-sha-pinning`), P12 (`frontend-major-updates`) y P13 (`python-hash-locking`); `dependency-hardening` pasa a `odd/done`; se actualizan la hoja de ruta, `pendiente.md`, `auditoria-dependencias.md`, `frontend-bundle.md` y `native-tables.md`. Ruta: inline. Mismo commit.

## Log

- **L1 (2026-11-04).** Petición original, literal:
  > El commit documental de odd/done está ya finalizado.
  >
  > El multiusuario no es un cambio de rumbo ni una simple exploración. Es una dirección futura de Password Checker que ya habíamos establecido y que está recogida en `pendiente.md`.
  >
  > No quiero implementarlo todavía ni ampliar el alcance de la primera bóveda persistente. Primero desarrollaremos una bóveda personal, local y cifrada.
  >
  > Sin embargo, quiero que su diseño tenga en cuenta la evolución posterior hacia cuentas de usuario, bóvedas personales y de organización, departamentos, permisos y compartición de secretos. No se trata de implementar ahora esas capacidades, sino de estudiar las implicaciones arquitectónicas y evitar decisiones que dificulten innecesariamente esa evolución.
  >
  > Respecto a los pendientes:
  >
  > - **DT4 y P10:** estoy de acuerdo en resolverlos ahora, siguiendo el flujo habitual de pruebas y revisión independiente.
  > - **P12:** mantenerla vinculada a la Fase 1, como ya está.
  > - **P13:** conservarla pendiente con el disparador actual, para reevaluarla durante el diseño de la bóveda.
  > - **Vue Router:** retirarlo durante la Fase 1 y conservar Pinia.
  >
  > En la documentación, quiero dos correcciones:
  >
  > 1. Reformular `hoja-de-ruta.md` para que multiusuario, compartición y sincronización figuren como horizontes futuros previstos, no como funcionalidades descartadas.
  > 2. Ampliar `vault-discovery` (T4, T5 y T6) para evaluar la evolución hacia múltiples bóvedas, propietarios y una arquitectura de claves compatible con futuras capacidades multiusuario. No implementarlas todavía.
  >
  > Mantén separados el alcance de la primera bóveda y la evolución empresarial. No es necesario crear una Fase 7 ni planificar todavía el multiusuario.
  >
  > Realiza primero las correcciones documentales y prepara DT4 y P10 según el flujo habitual, sin integrar cambios en `main` hasta mi aprobación.
  >
  > Además P12 se integra formalmente en Fase 1 con su propio paso. Desaparece de dependency-hardening.
  > P13 se integra en la Fase 6 con su propio paso cuando se implemente la bóveda. Desaparece de dependency-hardening.
  >
  > Dependency hardening pasa a done.
- **L2 (2026-11-04).** Contexto comprobado en `docs/odd-done` (`5a2599a`) antes de editar:
  - El multiusuario está recogido en `docs/pendiente.md`, apartados «Compartición, equipos y verificación en dos pasos» y «Dispositivos, sincronización e integraciones». En cambio, `docs/hoja-de-ruta.md` decía: «Fuera de la hoja de ruta, por no ser viables sin un modelo de amenazas: multiusuario y compartición, sincronización entre equipos y acceso móvil sin ADB.» El usuario no pidió cambiar el acceso móvil sin ADB, así que mantiene su estado.
  - `vue-router` no tiene ningún import en `frontend/src`. Pinia sí se usa: `useWorkspace` en `frontend/src/store.ts`.
  - DT4: `read_upload` informa siempre de `malformed_csv(1)` (`backend/password_checker/infrastructure/csv_reader.py`), mientras que `checked_rows` usa `reader.line_num`.
  - P10: las 13 líneas `uses:` de `.github/workflows/` van por etiqueta (`@v7`) y no existe `.github/dependabot.yml`. P7 activó las alertas de Dependabot, que son un ajuste del repositorio.
- **L3 (2026-11-04).** T1 y T2 hechas en un solo commit, porque `vault-discovery` T6 enlaza el plan de P13 que crea T2.
  - **Comprobación de enlaces:** script de solo lectura, fuera del repositorio, sobre los 11 Markdown del commit. Todos los destinos relativos y anclas resuelven. Solo avisa de `../README.md#L15` en la auditoría, un ancla de línea de GitHub que ya existía y no es un encabezado.
  - **Sin tocar:** las menciones históricas a `odd/tasks/dependency-hardening.md` en los Log, como `native-tables` L3. El enlace a `reliability-hardening` de la hoja de ruta se actualizará en la rama de DT4 si ese plan pasa a `odd/done`.
  - **Siguiente:** DT4 en `fix/csv-header-line` y P10 en `ci/pin-actions-sha`, las dos encadenadas sobre esta rama.
- **L4 (2026-11-04).** Cierre.
  - **Integración en `main`:** el usuario la avanzó hasta `1c31f31` por fast-forward. Esto incluye `docs/odd-done` (`5a2599a`) y esta rama. La revisión nativa la había dado como pasiva.
  - **S6, DT4 y P10:** cerradas en sus ramas e integradas con la CI en verde y la revisión aprobada. DT4 entró con el merge `9ec9a30` (L16-L18 de [reliability-hardening](reliability-hardening.md)) y P10, con el merge `ec8d167` ([actions-sha-pinning](actions-sha-pinning.md)).
  - **Movido a `odd/done` con un commit directo en `main`.** Petición, literal: «No hace falta que crees una rama de documentación para cerrar roadmap-horizons. Haz el commit modificandolo directamente con el prefijo docs».
