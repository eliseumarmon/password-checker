# Hoja de ruta

Este documento reúne en un solo sitio las fases de trabajo de Password Checker, el plan de cada funcionalidad y las decisiones que siguen abiertas, para que la hoja de ruta no dependa de conversaciones. **Es una propuesta:** solo están aprobadas la decisión D1 y la planificación de la Fase 1. Las ideas de origen están en el [trabajo pendiente](pendiente.md); el funcionamiento actual, en el [flujo de usuario](flujo-usuario.md).

## Resumen

| Fase | Objetivo | Estado | Bloqueada por | Planes |
|---|---|---|---|---|
| 0 | Endurecer dependencias y cadena de suministro | **Cerrada** (2026-11-04) | — | [dependency-hardening](../odd/tasks/dependency-hardening.md) |
| 1 | Cimientos del frontend: colores en variables, tablas nativas, accesibilidad y tamaño del bundle | Planificada | D2, solo para una tarea | [css-tokens](../odd/tasks/css-tokens.md), [native-tables](../odd/tasks/native-tables.md), [keyboard-accessibility](../odd/tasks/keyboard-accessibility.md), [frontend-bundle](../odd/tasks/frontend-bundle.md) |
| 2 | Revisión más ágil, sin cambiar el formato `.pwc` | Planificada | — | [review-filters](../odd/tasks/review-filters.md), [undo-ux](../odd/tasks/undo-ux.md), [secret-visibility](../odd/tasks/secret-visibility.md), [export-preview](../odd/tasks/export-preview.md), [compare-resolution](../odd/tasks/compare-resolution.md), [local-strength](../odd/tasks/local-strength.md), [mobile-record-detail](../odd/tasks/mobile-record-detail.md) |
| 3 | Datos de revisión que se guardan en la sesión (`.pwc` v3) | **Bloqueada** | D8, D3 (y D5 para las asociaciones de servicio) | Sin plan detallado (véase [Fase 3](#fase-3--datos-de-revisión-en-la-sesión)) |
| 4 | Ajustes: tema claro, ayuda, bloqueo por inactividad, idioma | Planificada en parte | D4 (bloqueo), D6 (idioma) | [light-theme](../odd/tasks/light-theme.md), [help-section](../odd/tasks/help-section.md) |
| 5 | Validación con personas | Planificada | — | [user-validation](../odd/tasks/user-validation.md) |
| 6 | Bóveda persistente: primero diseño, después implementación | Diseño planificado; implementación **bloqueada** | D7 | [vault-discovery](../odd/tasks/vault-discovery.md) |

Fuera de la hoja de ruta, por no ser viables sin un modelo de amenazas: multiusuario y compartición, sincronización entre equipos y acceso móvil sin ADB. Sigue vigente la restricción de no reintroducir la CLI.

## Cómo leer las fases

- **Las fases agrupan; las dependencias ordenan.** El orden real lo marca el apartado «Depende de» de cada plan, no una secuencia rígida. Por ejemplo, `local-strength` es casi todo backend y puede empezar en cualquier momento, y la validación con personas se hace en rondas a medida que avanzan las fases.
- **Una decisión pendiente solo bloquea lo que la necesita.** Cada plan indica qué decisión lo bloquea, si alguna lo hace.
- **Los pendientes de baja prioridad de la Fase 0 (P9-P13) no bloquean ninguna fase.**
- **Cada plan es un documento ODD** en `odd/tasks/`, con sus specs, tareas, pruebas y registro. Ningún plan está aprobado para implementarse hasta que el usuario lo diga.

## Decisiones

| ID | Pregunta | Estado | Bloquea | Recomendación |
|---|---|---|---|---|
| D1 | ¿Mantener PrimeVue (y actualizarlo) o sustituirlo por tablas propias? | **Aprobada** (2026-11-03): tablas HTML nativas con Vue, sin PrimeVue | — | — |
| D2 | ¿Debe `Esc` cerrar los diálogos de comparación, ficha y sesión? | **Pendiente** | `keyboard-accessibility` T2 | Opción A |
| D3 | Al pasar a `.pwc` v3, ¿se migran las sesiones v2 o se rechazan, como se hizo con v1? | **Pendiente** | Fase 3 | Decidir después de D8 |
| D4 | ¿Qué significa «bloquear» por inactividad? | **Pendiente** | Bloqueo por inactividad (Fase 4) | Opción B, como primer paso de la bóveda |
| D5 | ¿Las credenciales se identifican por su URL o se vinculan a un servicio lógico común? | **Pendiente** | Asociaciones de servicio (Fase 3) y modelo de la bóveda (Fase 6) | Decidir en `vault-discovery` T4 |
| D6 | ¿Se traduce la interfaz a otros idiomas? | **Pendiente** | Ajuste de idioma (Fase 4) | Aplazar hasta la validación con personas |
| D7 | ¿Cuál es el alcance de la primera versión de la bóveda? | **Pendiente** | Implementación de la Fase 6 | Decidir con los documentos de `vault-discovery` |
| D8 | ¿Cómo encaja `.pwc` v3 con la futura bóveda? | **Pendiente** (nueva, 2026-11-04) | Fase 3 | Definir antes el contrato de persistencia y exportación |

### D2 — `Esc` en los diálogos

**Hoy:** el [flujo de usuario](flujo-usuario.md) documenta que solo el diálogo de confirmación se cierra con `Esc`: «Los demás diálogos (comparación, ficha, sesión cifrada) no se cierran con `Esc`.»

| Opción | Efecto | Ventaja | Inconveniente |
|---|---|---|---|
| A. `Esc` cierra todos los diálogos | La ficha con cambios sin guardar pide confirmación antes de cerrarse, igual que hoy con «✕»; la comparación y la sesión se cierran directamente | Es lo que espera el patrón de diálogo de WAI-ARIA APG y unifica el comportamiento | En la sesión se pierde la contraseña escrita (no se guarda nada más) |
| B. Mantener el comportamiento actual | Solo la confirmación se cierra con `Esc` | No cambia nada documentado | Comportamiento distinto según el diálogo, menos predecible con teclado |

Recomendación: A. No se pierden cambios porque reutiliza la confirmación de la ficha. Conviene resolverla antes de `keyboard-accessibility` T2, que trabaja el teclado de esos mismos diálogos.

### D3 — Sesiones v2 al pasar a v3

| Opción | Ventaja | Inconveniente |
|---|---|---|
| A. Migrar: leer v2 y completar los campos nuevos con valores por defecto | El usuario no pierde sesiones guardadas | Mantener un lector de v2 |
| B. Rechazar v2, como se hizo con v1 | Un solo formato que validar | Obliga a reimportar los CSV |

Depende de D8: si la Fase 3 se aplaza hasta la bóveda, D3 se decide sobre el formato que salga de allí.

### D4 — Bloqueo por inactividad

El backend sigue entregando datos aunque la interfaz se oculte, así que un bloqueo solo visual no protege nada.

| Opción | Efecto | Inconveniente |
|---|---|---|
| A. Vaciar la memoria del backend | Para continuar hay que abrir el `.pwc` | Se pierden los cambios no guardados en un `.pwc` |
| B. Cifrar el trabajo en memoria con una clave del usuario | Desbloquear restaura el trabajo | Es el ciclo de clave maestra de la bóveda; conviene diseñarlo en `vault-discovery` T5 |

### D5 — Identidad de servicios

Pregunta literal del [trabajo pendiente](pendiente.md): «definir si las credenciales se identifican por la URL/URI encontrada al importar o si se vinculan a un servicio lógico común (web, Android, iOS). Conservar las asociaciones originales y evaluar las consecuencias para la detección de duplicados; pertenecer al mismo servicio no implica fusionarlas automáticamente.» Como forma parte del modelo de datos de la bóveda, se estudia en `vault-discovery` T4 para no diseñarlo dos veces.

### D6 — Idioma

Hay textos fijos en español en todos los componentes, y los mensajes de error del backend también están en español. Traducir exige extraer todos los textos y dar códigos a los errores. Se recomienda aplazarlo hasta que la validación con personas muestre que hace falta.

### D7 — Alcance de la primera versión de la bóveda

El [trabajo pendiente](pendiente.md) pide: «Elegir el primer alcance útil: bóveda personal local, tipos de elementos básicos y respaldos, o requisitos empresariales desde el inicio; evitar mezclar estas fases en una sola implementación.» Se decide con los documentos de `vault-discovery`.

### D8 — `.pwc` v3 y la bóveda

La Fase 3 cambiaría el formato `.pwc` para guardar datos de revisión antes de diseñar la bóveda, que también cambiará el formato: el trabajo pendiente prevé el `.pwc` como «respaldo portable» capaz de incluir «diferentes tipos de elementos, sus adjuntos y metadatos necesarios». Hacer v3 sin ese diseño puede obligar a una segunda migración.

| Opción | Ventaja | Inconveniente |
|---|---|---|
| A. Definir antes el contrato de persistencia y exportación (`vault-discovery` T2) y hacer v3 conforme a él | Los datos de revisión llegan pronto sin rehacer el formato después | Adelanta parte del diseño de la bóveda |
| B. Aplazar la Fase 3 hasta la bóveda | Un solo cambio de formato | La fecha de confirmación y las asociaciones de servicio esperan a la Fase 6 |

Recomendación: hacer primero `vault-discovery` T2 y decidir entre A y B con ese documento.

## Fases

### Fase 0 — Endurecimiento de dependencias

Cerrada el 2026-11-04: P2-P8 integradas en `main`, con las alertas de Dependabot (P7) activadas y la auditoría automática (P8) en marcha. Quedan P9 (prioridad baja) y las opcionales P10-P13, que no bloquean nada. P12 queda absorbida en parte por la Fase 1: `primevue`, `@primeuix/themes` y `vue-router` se retiran en lugar de actualizarse. Detalle en [dependency-hardening](../odd/tasks/dependency-hardening.md).

### Fase 1 — Cimientos del frontend

| Plan | Depende de |
|---|---|
| [css-tokens](../odd/tasks/css-tokens.md): colores en variables CSS, sin cambio visual | — |
| [native-tables](../odd/tasks/native-tables.md): tablas nativas y retirada de PrimeVue (D1) | `css-tokens` |
| [keyboard-accessibility](../odd/tasks/keyboard-accessibility.md): revisión de accesibilidad, foco en diálogos, pestañas | `css-tokens`, `native-tables`; T2, de D2 |
| [frontend-bundle](../odd/tasks/frontend-bundle.md): retirar `vue-router`; dividir el código solo si sigue el aviso de 500 kB | T1: nada; T2-T3: `native-tables` |

### Fase 2 — Revisión más ágil

Nada de esta fase cambia el formato `.pwc`.

| Plan | Depende de |
|---|---|
| [review-filters](../odd/tasks/review-filters.md): filtro por estado, orden por riesgo y por URL, continuidad de filtros | `native-tables` |
| [undo-ux](../odd/tasks/undo-ux.md): `Ctrl/Cmd+Z` y aviso tras guardar con «Deshacer» | — |
| [secret-visibility](../odd/tasks/secret-visibility.md): «Ocultar todo», revelar contraseñas en la comparación, copiar contraseña | — |
| [export-preview](../odd/tasks/export-preview.md): ventana de exportación con incluidos, excluidos y conflictos | `keyboard-accessibility` (foco en diálogos) |
| [compare-resolution](../odd/tasks/compare-resolution.md): conservar A, B o ambas, fusionar notas, editar el candidato final | `secret-visibility`, `keyboard-accessibility` |
| [local-strength](../odd/tasks/local-strength.md): evaluación local de fortaleza más completa | — |
| [mobile-record-detail](../odd/tasks/mobile-record-detail.md): ficha móvil a pantalla completa, acciones rápidas de revisión, «Buscar en tienda» | `keyboard-accessibility` |

### Fase 3 — Datos de revisión en la sesión

**Bloqueada por D8 y D3.** Sin plan detallado hasta resolverlas. Contenido previsto, todo persistido en `.pwc`:

- «fecha local al confirmar manualmente» (de la ficha, en el trabajo pendiente);
- las asociaciones de servicio, si D5 las aprueba.

Es un cambio de formato persistido: requerirá verificación independiente y un solo salto de versión que reúna todos los campos nuevos.

### Fase 4 — Ajustes

| Plan | Estado |
|---|---|
| [light-theme](../odd/tasks/light-theme.md): tema claro y su ajuste | Planificado; depende de `css-tokens` y `native-tables` |
| [help-section](../odd/tasks/help-section.md): sección de ayuda | Planificado |
| Bloqueo por inactividad e indicador de sesión en la cabecera móvil | **Bloqueado por D4** |
| Ajuste de idioma | **Bloqueado por D6** |

### Fase 5 — Validación con personas

[user-validation](../odd/tasks/user-validation.md): observación de 4-6 personas con credenciales ficticias, en rondas. La primera ronda puede hacerse tras la Fase 1; la segunda, tras la Fase 2.

### Fase 6 — Bóveda persistente

[vault-discovery](../odd/tasks/vault-discovery.md): modelo de amenazas y documentos de decisión, sin código. Su T2 (contrato de persistencia y exportación) se adelanta porque D8 lo necesita. La implementación queda **bloqueada por D7**, que se decide con esos documentos.

## Origen y cambios

| Fecha | Cambio |
|---|---|
| 2026-11-03 | Informe de viabilidad de `pendiente.md` con las Fases 0-6 y las decisiones D1-D7. Hasta este documento solo existía en la conversación y, resumido, en la memoria del agente. |
| 2026-11-03 | D1 aprobada; planes de la Fase 1 en `odd/tasks/`. |
| 2026-11-04 | Fase 0 cerrada (P7 y P8). |
| 2026-11-04 | Revisión externa de la hoja de ruta, aportada por el usuario. Se incorporan tres puntos: (1) resolver D2 durante la Fase 1, antes del trabajo de teclado en los diálogos; (2) definir la relación entre `.pwc` v3 y la bóveda antes de comprometer v3, que da lugar a D8 y a adelantar `vault-discovery` T2; (3) leer las fases como agrupaciones con dependencias, no como una secuencia rígida. |
