# Bóveda persistente: diseño previo

Objetivo: resolver por escrito, sin código, las preguntas que el trabajo pendiente exige responder antes de planificar la bóveda, y preparar las decisiones D4, D5, D7 y D8. La primera versión es una bóveda personal, local y cifrada, pero su diseño tiene en cuenta la evolución futura hacia el multiusuario (S4), sin incluirla.
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
- **S4 — Evolución hacia el multiusuario (L4).**
  - «No quiero implementarlo todavía ni ampliar el alcance de la primera bóveda persistente. Primero desarrollaremos una bóveda personal, local y cifrada.»
  - «Sin embargo, quiero que su diseño tenga en cuenta la evolución posterior hacia cuentas de usuario, bóvedas personales y de organización, departamentos, permisos y compartición de secretos. No se trata de implementar ahora esas capacidades, sino de estudiar las implicaciones arquitectónicas y evitar decisiones que dificulten innecesariamente esa evolución.»
  - «Ampliar `vault-discovery` (T4, T5 y T6) para evaluar la evolución hacia múltiples bóvedas, propietarios y una arquitectura de claves compatible con futuras capacidades multiusuario. No implementarlas todavía.»
  - «Mantén separados el alcance de la primera bóveda y la evolución empresarial.»

## Tasks

- [ ] T1 — S1: modelo de amenazas. Activos (contraseñas, 2FA, notas, adjuntos, metadatos), atacantes, superficies (API local, navegador, disco, portapapeles, archivos temporales, copias `.pwc`) y medidas existentes. Base de todos los demás. Ruta: inline.
- [ ] T2 — S1, S2: contrato de persistencia y exportación. Ruta: inline.
  - Cubre el `.pwc` como respaldo portable, la política de versiones y migraciones y cómo se tratan los campos desconocidos.
  - Prepara **D8** y, con ella, **D3**.
  - Se adelanta a las demás tareas de esta fase para no comprometer `.pwc` v3 sin este diseño.
- [ ] T3 — S1, S2: almacenamiento. SQLite y otras opciones; cifrado en reposo; qué metadatos pueden quedar visibles sin desbloquear; esquema e índices. Ruta: inline.
- [ ] T4 — S1, S4: modelo de elementos (`VaultItem`) y relación entre servicio, cuenta y acceso. Prepara **D5**. Ruta: inline.
  - **Evolución (S4):** varias bóvedas y propietarios. A qué pertenece cada elemento (bóveda, colección) y quién es su propietario: hoy, una persona; más adelante, una organización.
  - Identificadores que no den por hecho una única bóveda local.
  - Qué haría falta añadir al modelo para las bóvedas de organización, los departamentos y los permisos, y si la primera versión lo impide.
- [ ] T5 — S1, S4: clave maestra y ciclo de bloqueo (derivación, exposición en memoria, cambio de contraseña, reautenticación, pérdida sin puerta trasera). Prepara **D4**. Ruta: inline.
  - **Evolución (S4):** arquitectura de claves compatible con el multiusuario. Por ejemplo, una jerarquía en la que la contraseña maestra protege una clave de usuario y esta, una clave por bóveda. Así, conceder o revocar el acceso a una bóveda no obligaría a volver a cifrar todos sus elementos.
  - Comparar el coste de prepararlo en la primera versión con el de migrar después.
  - La recuperación organizativa sigue siendo una decisión pendiente del trabajo pendiente. T5 solo señala qué la haría posible o imposible.
- [ ] T6 — S1, S4: propuesta de alcance de la primera versión: una bóveda personal, local y cifrada (L4). Prepara **D7**. Ruta: inline.
  - Dos listas separadas:
    - lo que la primera versión deja preparado, a partir de las conclusiones de T4 y T5;
    - lo que queda para la evolución empresarial, sin planificar: cuentas de usuario, bóvedas de organización, departamentos, permisos, compartición de secretos y sincronización.
  - Reevalúa P13 ([python-hash-locking](python-hash-locking.md), instalación con hashes) con el modelo de amenazas de T1.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» Con ella, el usuario aporta una revisión externa que recomienda definir los contratos esenciales de almacenamiento y exportación antes de comprometer `.pwc` v3. De ahí D8 y el adelanto de T2. El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`:
  - Las capas del backend (dominio, aplicación e infraestructura, protegidas por `tests/test_architecture.py`) admiten un puerto de repositorio con un adaptador de almacenamiento.
  - `sqlite3` forma parte de la biblioteca estándar de Python.
  - Argon2id y AES-256-GCM ya están en uso para el `.pwc` (`infrastructure/sessions.py`).
  - `Workspace` es un estado único en memoria, con historial de deshacer por instantáneas completas y límites ligados al tamaño del `.pwc`; la bóveda necesitará otro modelo.
  - Ruta: inline.
- **L4 (2026-11-04).** El usuario confirma que el multiusuario «es una dirección futura de Password Checker que ya habíamos establecido y que está recogida en `pendiente.md`». Encargo completo en `odd/tasks/roadmap-horizons.md`, L1; fragmentos que afectan a este plan en S4.
  - **Cambios:** S4 nueva; T4, T5 y T6 amplían su alcance; T6 ya no trata el multiusuario como algo que queda fuera, sino como una evolución que el diseño debe permitir.
  - **Orientación de D7:** la primera versión es una bóveda personal, local y cifrada.
  - **P13:** sale del plan de dependencias a [python-hash-locking](python-hash-locking.md) y se reevalúa en T6.
  - Ninguna tarea estaba empezada, así que no se reabre nada.
