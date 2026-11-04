# Acciones de GitHub fijadas por SHA (P10)

Objetivo: que la CI no ejecute otro código sin una decisión explícita. Cada acción se fija por el SHA de su commit, con la versión en un comentario, y Dependabot propone las actualizaciones. Corresponde al hallazgo H9 de la [auditoría de dependencias](../../docs/auditoria-dependencias.md#h9--acciones-de-github-referenciadas-por-etiqueta-mutable).
Rama: `ci/pin-actions-sha`, encadenada sobre `docs/roadmap-horizons`. No se integra en `main` sin la aprobación del usuario. Entrega: `single-pr`, previsión de unas 40 líneas.
Comprobaciones: cada SHA, contrastado con su etiqueta mediante `gh api`; YAML válido; y la CI en verde, que exige subir la rama. Estado: **completado** (L6): verificado, revisado, CI en verde e integrado en `main`.

## Specs

- **S1 — Origen.** P10 de [dependency-hardening](dependency-hardening.md), literal: «Acciones de GitHub fijadas por SHA con comentario de versión, y `dependabot.yml` solo para `github-actions` (H9).» «Aceptación: cada `uses:` apunta a un SHA de 40 caracteres que coincide con su etiqueta (`gh api repos/<acción>/git/ref/tags/<v>`), y la CI está en verde.» «Si se aprueba, se puede imponer activando `sha_pinning_required` en los permisos de Actions del repositorio (hoy `false`).» «Regresión: ninguna funcional. Revisión: sí (CI).»
- **S2 — Encargo.** Del usuario (L1 de [roadmap-horizons](../tasks/roadmap-horizons.md)): «**DT4 y P10:** estoy de acuerdo en resolverlos ahora, siguiendo el flujo habitual de pruebas y revisión independiente.» «prepara DT4 y P10 según el flujo habitual, sin integrar cambios en `main` hasta mi aprobación.»

## Tasks

- [x] T1 — S1, S2: fijar por SHA las 13 líneas `uses:` de `tests.yml` y `dependency-audit.yml`, y crear `.github/dependabot.yml` solo para el ecosistema `github-actions`. Ruta: inline.
  - Excepción a RED: un workflow no tiene prueba local ejecutable. La comprobación es `gh api` por cada SHA y la CI en verde.
  - Riesgo: punto 5 (CI). Commit propio, verificación independiente y revisión.
- Fuera de este plan: activar `sha_pinning_required` es un ajuste del repositorio que decide su propietario.

## Log

- **L1 (2026-11-04).** P10 sale de `dependency-hardening` (su L33) a este plan, porque se resuelve antes de la Fase 1. Encargo completo en [roadmap-horizons](../tasks/roadmap-horizons.md), L1.
- **L2 (2026-11-04).** Análisis en `docs/odd-done` (`5a2599a`):
  - Hay 13 líneas `uses:`, todas de acciones oficiales de GitHub y por etiqueta mayor: `actions/checkout@v7`, `actions/setup-python@v7`, `actions/setup-node@v7` y `actions/upload-artifact@v7`.
  - No existe `.github/dependabot.yml`. P7 solo activó las alertas de Dependabot, que son un ajuste del repositorio.
- **L3 (2026-11-04).** T1 en `ci/pin-actions-sha`, encadenada sobre `docs/roadmap-horizons`.
  - **SHA elegidos:** los de la versión exacta más reciente de cada etiqueta mayor. Según `git ls-remote --tags`, `v7` apunta hoy al mismo commit, así que fijar no cambia lo que ejecuta la CI. Las cuatro son etiquetas ligeras (sin `^{}`).

    | Acción | SHA | Versión |
    |---|---|---|
    | `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | v7.0.1 |
    | `actions/setup-python` | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` | v7.1.0 |
    | `actions/setup-node` | `949feb2413d6458794dcd2491c4babbbce0c15c1` | v7.1.0 |
    | `actions/upload-artifact` | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | v7.0.2 |

  - **Aceptación de S1:** `gh api repos/actions/<acción>/git/ref/tags/<versión>` devuelve `commit` y el mismo SHA en los cuatro casos. Las 13 líneas `uses:` llevan un SHA de 40 caracteres y no queda ningún `@v7`.
  - **`.github/dependabot.yml`:** `version: 2`, una sola entrada `github-actions` en `/`, con frecuencia semanal. Dependabot actualiza el SHA y el comentario de versión.
  - **Sin comprobar en local en este paso:** la validez del YAML. No hay parser ni en el `.venv` ni en `frontend/node_modules`, y no se instala una herramienta nueva para esto. **Corregido en L4:** el Python del sistema sí tiene PyYAML, y el verificador lo usó. El cambio de los workflows solo añade un comentario tras cada valor. La CI valida los workflows al ejecutarlos. GitHub lee `dependabot.yml` desde la rama por defecto, así que su validación final llega al integrar.
  - **Riesgo:** punto 5 (CI). Commit propio; verificación independiente y revisión pendientes.
- **L4 (2026-11-04).** Verificación independiente de `6288161` frente a `1c31f31`: un agente de solo lectura que trabajó sobre objetos de git. Sin bloqueos.
  - **S1:** las 13 líneas `uses:` llevan SHA de 40 caracteres y comentario `# vX.Y.Z`, y no queda ninguna etiqueta. Cada SHA coincide con su etiqueta según `gh api`, de tipo `commit`, y con `git ls-remote`. `v7` apunta al mismo commit en las cuatro acciones, y cada versión es la `releases/latest`.
  - **Solo cambian los `uses:`:** al normalizar `@v7` y `@<sha> # vX` a un mismo valor, los dos workflows son idénticos a la base.
  - **YAML:** PyYAML 6.0.3, el del Python del sistema y sin instalar nada, analiza los tres archivos. `dependabot.yml` cumple el esquema `dependabot-2.0.json` de SchemaStore, revisado a mano porque `jsonschema` no está instalado.
  - **Sin verificar:** la CI en verde, porque la rama no está subida.
  - **Avisos:**
    - (1) L3 decía que no había ningún parser instalado; corregido arriba.
    - (2) Se fijan las etiquetas de parche (v7.0.1…) y no `v7`. Es correcto y coincide con el formato de comentario que actualiza Dependabot.
    - (3) No se configuran `cooldown`, grupos ni `open-pull-requests-limit`; son opcionales y quedan fuera de S1.
  - El verificador dejó archivos temporales fuera del repositorio; ya se eliminaron.
- **L5 (2026-11-04).** Revisión del rango `1c31f31..52e2059`: riesgo alto (scripts de shell en `dependency-audit.yml`), lente de riesgo y consentimiento del usuario. `review-aaa6aa62dd7a3d04`, aprobada sin hallazgos y reconocida (`authority: burned`). Antes, el usuario avanzó `main` hasta `1c31f31` (fast-forward), de modo que el rango ya solo contiene P10.
- **L6 (2026-11-04).** CI en GitHub sobre `3cdb433`, los dos en verde:
  - `Tests` (run `41821560204`): `python (3.12)`, `python (3.14)`, `frontend` y `e2e`, ya con las acciones fijadas por SHA.
  - `Dependency audit` (run `41821560483`), que se lanzó porque cambió su workflow: `python` y `npm`.
  - Petición del usuario, literal: «Sube a origin, cuando pasen CI las integras en main». Se trae `main` (con DT4 ya integrada) a la rama, y el plan pasa a `odd/done`. La hoja de ruta da P10 y DT4 por cerradas.
  - Sigue fuera de este plan: activar `sha_pinning_required` es un ajuste del repositorio que decide su propietario.
- **L7 (2026-11-04).** Como `main` avanzó con DT4, la rama tiene una base nueva y se volvió a revisar. `review-b4398e9ea2cc0c97`, con las cuatro lentes y el consentimiento del usuario, aprobada y reconocida (`authority: burned`). Riesgo, resiliencia y fiabilidad: sin hallazgos. Legibilidad: una sugerencia, `R2-001`. La columna «Cuándo» de la tabla de la Fase 0 mezclaba estado y momento para P10. Aplicada: vuelve a decir «Antes de la Fase 1», porque el estado ya consta en el resumen y en la Fase 1.
