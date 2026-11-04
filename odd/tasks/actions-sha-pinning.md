# Acciones de GitHub fijadas por SHA (P10)

Objetivo: que la CI no ejecute otro código sin una decisión explícita. Cada acción se fija por el SHA de su commit, con la versión en un comentario, y Dependabot propone las actualizaciones. Corresponde al hallazgo H9 de la [auditoría de dependencias](../../docs/auditoria-dependencias.md#h9--acciones-de-github-referenciadas-por-etiqueta-mutable).
Rama: `ci/pin-actions-sha`, encadenada sobre `docs/roadmap-horizons`. No se integra en `main` sin la aprobación del usuario. Entrega: `single-pr`, previsión de unas 40 líneas.
Comprobaciones: cada SHA, contrastado con su etiqueta mediante `gh api`; YAML válido; y la CI en verde, que exige subir la rama. Estado: planificado, sin empezar.

## Specs

- **S1 — Origen.** P10 de [dependency-hardening](../done/dependency-hardening.md), literal: «Acciones de GitHub fijadas por SHA con comentario de versión, y `dependabot.yml` solo para `github-actions` (H9).» «Aceptación: cada `uses:` apunta a un SHA de 40 caracteres que coincide con su etiqueta (`gh api repos/<acción>/git/ref/tags/<v>`), y la CI está en verde.» «Si se aprueba, se puede imponer activando `sha_pinning_required` en los permisos de Actions del repositorio (hoy `false`).» «Regresión: ninguna funcional. Revisión: sí (CI).»
- **S2 — Encargo.** Del usuario (L1 de [roadmap-horizons](roadmap-horizons.md)): «**DT4 y P10:** estoy de acuerdo en resolverlos ahora, siguiendo el flujo habitual de pruebas y revisión independiente.» «prepara DT4 y P10 según el flujo habitual, sin integrar cambios en `main` hasta mi aprobación.»

## Tasks

- [ ] T1 — S1, S2: fijar por SHA las 13 líneas `uses:` de `tests.yml` y `dependency-audit.yml`, y crear `.github/dependabot.yml` solo para el ecosistema `github-actions`. Ruta: inline.
  - Excepción a RED: un workflow no tiene prueba local ejecutable. La comprobación es `gh api` por cada SHA y la CI en verde.
  - Riesgo: punto 5 (CI). Commit propio, verificación independiente y revisión.
- Fuera de este plan: activar `sha_pinning_required` es un ajuste del repositorio que decide su propietario.

## Log

- **L1 (2026-11-04).** P10 sale de `dependency-hardening` (su L33) a este plan, porque se resuelve antes de la Fase 1. Encargo completo en [roadmap-horizons](roadmap-horizons.md), L1.
- **L2 (2026-11-04).** Análisis en `docs/odd-done` (`5a2599a`):
  - Hay 13 líneas `uses:`, todas de acciones oficiales de GitHub y por etiqueta mayor: `actions/checkout@v7`, `actions/setup-python@v7`, `actions/setup-node@v7` y `actions/upload-artifact@v7`.
  - No existe `.github/dependabot.yml`. P7 solo activó las alertas de Dependabot, que son un ajuste del repositorio.
