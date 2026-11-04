# Validación con personas

Objetivo: observar a personas usando Password Checker con credenciales ficticias y convertir lo observado en trabajo priorizado.
Rama: `docs/user-validation` desde `main`, solo para el material y los resultados. Fase 5, en rondas: la primera puede hacerse tras la Fase 1 y la segunda, tras la Fase 2. Entrega: `ask-on-risk`, previsión ~200 líneas de documentación y un generador de datos ficticios.
Comprobaciones: el generador produce CSV que la aplicación importa sin errores (`python -m unittest discover -s tests`). Estado: planificado, sin empezar.

## Specs

- **S1 — Origen.** `docs/pendiente.md`, «Validación con personas»: «Las siguientes son metas de diseño, no resultados medidos ni funciones garantizadas. Se propone observar a 4–6 personas con credenciales ficticias, incluyendo navegación por teclado y uso en pantalla pequeña.» Tareas que propone ese apartado:
  - «Importar CSV de distintos navegadores» — «Comprensión de errores, procedencia y reemplazo de sesión».
  - «Distinguir conflicto de reutilización» — «Si se conservan cuentas diferentes y se entiende la diferencia».
  - «Comparar y editar una variante» — «Si se reconoce la procedencia y se entiende que editar no cambia el servicio».
  - «Guardar y abrir una sesión» — «Si se conservan el archivo y su contraseña y se entienden las limitaciones».
  - «Exportar con conflictos» — «Si se entiende qué registros se incluyen y que Bitwarden puede crear duplicados».
  - «Usar la interfaz con teclado o móvil» — «Foco, acceso a controles, legibilidad y dificultades de navegación».
- **S2 — Datos ficticios.**
  - Un generador crea CSV de Chrome, Firefox y Safari con credenciales inventadas que cubren duplicados exactos, conflictos, reutilización, contraseñas débiles, registros Android y códigos 2FA ficticios.
  - Los CSV no se versionan (`.gitignore` excluye `*.csv`); se generan en un directorio temporal.
  - Nunca se usan credenciales reales.
- **S3 — Rondas.**
  - **Supuesto:** ronda 1 tras la Fase 1 (importación, teclado y móvil); ronda 2 tras la Fase 2 (comparación, edición y exportación con conflictos).
  - Cada ronda tiene un guion, una hoja de observación y el consentimiento de los participantes.
- **S4 — Resultados.**
  - Un documento por ronda en `docs/`, sin datos personales de los participantes: tarea, qué se observó, gravedad y propuesta.
  - Las propuestas entran en `docs/hoja-de-ruta.md` solo con la aprobación del usuario.
  - Pueden resolver D6 (idioma) si muestran que hace falta.

## Tasks

- [ ] T1 — S2: generador de datos ficticios, con una prueba que importa cada CSV generado. Ruta: inline.
- [ ] T2 — S3: guion, hoja de observación y consentimiento. Ruta: inline.
- [ ] T3 — S3, S4: ronda 1 y su documento de resultados. Depende de: la Fase 1. Ruta: inline. La observación la hacen personas; el agente solo prepara el material y redacta lo observado.
- [ ] T4 — S3, S4: ronda 2 y su documento de resultados. Depende de: la Fase 2. Ruta: inline.

## Log

- **L1 (2026-11-03).** Petición original: «Examina pendiente.md. Examina la base del código y evalúa su viabilidad. Genera planes para llevar a cabo las nuevas features de forma coherente.»
- **L2 (2026-11-04).** «Necesito que documentes todos los planes y que marques las decisiones pendientes.» «No empieces ninguna implementación.» Con ella, el usuario aporta una revisión externa que propone hacer la validación de forma progresiva; de ahí las rondas de S3. El plan viene del informe de viabilidad del 2026-11-03, recogido en `docs/hoja-de-ruta.md`.
- **L3 (2026-11-04).** Análisis en `main`: los E2E generan sus CSV en el propio código (por ejemplo, `paginationCsv` en `review.spec.ts`), que sirve de modelo para el generador. No depende de ninguna decisión pendiente. Ruta: inline.
