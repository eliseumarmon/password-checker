# Bóveda persistente: diseño previo

Objetivo: resolver por escrito, sin código, las preguntas que el trabajo pendiente exige responder antes de planificar la bóveda, y preparar las decisiones D4, D5, D7 y D8.
Rama: `docs/vault-discovery` desde `main`. Fase 6, que es solo de documentación hasta que se decida D7. T2 se adelanta porque D8 (Fase 3) lo necesita. Entrega: un documento por tarea, cada uno revisable por separado.
Comprobaciones: revisión del usuario de cada documento; no hay código ni pruebas. Estado: planificado, sin empezar.

## Specs

- **S1 — Preguntas que hay que responder.** `docs/pendiente.md`, «Preguntas a resolver antes de elaborar un plan»:
  - «Elegir el primer alcance útil: bóveda personal local, tipos de elementos básicos y respaldos, o requisitos empresariales desde el inicio; evitar mezclar estas fases en una sola implementación.»
  - «Concretar modelo de amenazas, cifrado autenticado, derivación y rotación de claves, tratamiento de adjuntos, recuperación, límites y protección frente a exposición en API, logs, portapapeles y archivos temporales.»
  - «Definir migración de registros actuales a elementos persistentes; esquema, IDs, identidades de servicio, conflictos y garantías de no perder TOTP u otros campos durante cambios de modelo.»
  - «Investigar las implicaciones de compartir secretos y 2FA, gestionar permisos y revocaciones y elegir cómo probar todo ello con datos ficticios antes de utilizarlo con credenciales empresariales.»
- **S2 — Restricciones vigentes.**
  - `docs/pendiente.md`: «**No reintroducir la CLI eliminada**, ni comandos de extracción de secretos o de inyección/ejecución (`run`), como dependencia de estas ideas.»
  - «**SQLite es una candidata** para la persistencia, no una arquitectura de almacenamiento ni una elección criptográfica cerrada.»
  - «No prometer compatibilidad retrospectiva ni reintroducir la lectura de v1 sin una decisión nueva.»
- **S3 — Entregables.** Un documento por tema en `docs/boveda/` (**supuesto** de ubicación), cada uno con: contexto, opciones, ventajas e inconvenientes, recomendación y lo que queda abierto. Ninguno aprueba una implementación.

## Tasks

- [ ] T1 — S1: modelo de amenazas. Activos (contraseñas, 2FA, notas, adjuntos, metadatos), atacantes, superficies (API local, navegador, disco, portapapeles, archivos temporales, copias `.pwc`) y medidas existentes. Base de todos los demás. Ruta: inline.
- [ ] T2 — S1, S2: contrato de persistencia y exportación. Ruta: inline.
  - Cubre el `.pwc` como respaldo portable, la política de versiones y migraciones y cómo se tratan los campos desconocidos.
  - Prepara **D8** y, con ella, **D3**.
  - Se adelanta a las demás tareas de esta fase para no comprometer `.pwc` v3 sin este diseño.
- [ ] T3 — S1, S2: almacenamiento. SQLite y otras opciones; cifrado en reposo; qué metadatos pueden quedar visibles sin desbloquear; esquema e índices. Ruta: inline.
- [ ] T4 — S1: modelo de elementos (`VaultItem`) y relación entre servicio, cuenta y acceso. Prepara **D5**. Ruta: inline.
- [ ] T5 — S1: clave maestra y ciclo de bloqueo (derivación, exposición en memoria, cambio de contraseña, reautenticación, pérdida sin puerta trasera). Prepara **D4**. Ruta: inline.
- [ ] T6 — S1: propuesta de alcance de la primera versión, con lo que queda fuera (multiusuario, compartición, sincronización). Prepara **D7**. Si el modelo de amenazas crece, activa P13 (instalación con hashes) del plan de dependencias. Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» Con ella, el usuario aporta una revisión externa que recomienda definir los contratos esenciales de almacenamiento y exportación antes de comprometer `.pwc` v3. De ahí D8 y el adelanto de T2. El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`:
  - Las capas del backend (dominio, aplicación e infraestructura, protegidas por `tests/test_architecture.py`) admiten un puerto de repositorio con un adaptador de almacenamiento.
  - `sqlite3` forma parte de la biblioteca estándar de Python.
  - Argon2id y AES-256-GCM ya están en uso para el `.pwc` (`infrastructure/sessions.py`).
  - `Workspace` es un estado único en memoria, con historial de deshacer por instantáneas completas y límites ligados al tamaño del `.pwc`; la bóveda necesitará otro modelo.
  - Ruta: inline.
