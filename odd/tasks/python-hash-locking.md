# Instalación de Python con hashes (P13)

Objetivo: que la instalación de las dependencias de Python compruebe el hash de cada archivo descargado, si el modelo de amenazas de la bóveda lo justifica. Complementa a `backend/constraints.txt`, que fija las versiones pero no comprueba la integridad de lo que se descarga.
Fase 6: se reevalúa durante el diseño de la bóveda (`vault-discovery` T6) y, si se confirma, se implementa junto con ella, en una rama propia desde `main`.
Estado: pendiente, con disparador; no está aprobado para implementarse.

## Specs

- **S1 — Origen.** P13 de [dependency-hardening](../done/dependency-hardening.md), literal: «Bloqueo con hashes (uv con `--universal --generate-hashes`) si el modelo de amenazas crece con la bóveda persistente. Fuera de alcance por ahora.»
- **S2 — Encargo.** Del usuario (L1 de [roadmap-horizons](../done/roadmap-horizons.md)): «P13 se integra en la Fase 6 con su propio paso cuando se implemente la bóveda. Desaparece de dependency-hardening.» «**P13:** conservarla pendiente con el disparador actual, para reevaluarla durante el diseño de la bóveda.»
- **S3 — Contexto de la auditoría.** De [Reproducibilidad](../../docs/auditoria-dependencias.md#reproducibilidad-y-política-de-versiones): «PyPI no permite reemplazar el archivo de una versión ya publicada, así que los hashes solo añaden protección frente a un compromiso del propio índice o del transporte.» Las alternativas con hashes eran C (pip-tools, que resuelve para la plataforma donde se ejecuta) y D (uv, con resolución universal).

## Tasks

- [ ] T1 — S2: reevaluación en `vault-discovery` T6, con el modelo de amenazas de su T1. Se registra en el Log la decisión: implementarla con la bóveda, o descartarla con su motivo. Ruta: inline.
- [ ] T2 — S1, S3: solo si T1 la confirma. Ruta: inline. Riesgo: punto 5 (dependencias y CI); verificación independiente y revisión.
  - Bloqueo con hashes, `--require-hashes` en la CI y en el README, y el procedimiento de renovación.
  - Instalación en limpio con Python 3.12 y 3.14, en Linux (CI) y Windows (local).
  - La auditoría automática (`dependency-audit.yml`) sigue analizando todos los paquetes fijados.

## Log

- **L1 (2026-11-04).** P13 sale de `dependency-hardening` (su L33) a este plan, como paso propio de la Fase 6. Encargo completo en [roadmap-horizons](../done/roadmap-horizons.md), L1.
