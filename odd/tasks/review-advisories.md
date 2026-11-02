# Observaciones de la revisión nativa

Avisos no bloqueantes de la revisión gentle-ai (riesgo alto, cuatro perspectivas, 6 trozos de `8fceb39..731580a`, todos aprobados).
Se resuelven de una en una, cada una en su rama desde `main`, con test primero cuando aplique.
Ya resueltos y fuera de esta lista: papelera sin cambios (`247e830`), regla de «Pendiente» (`0e3517b`), mensajes de la CLI (`571c11c`), nombre por defecto del informe (`ba8fbbc`).

## Specs

- S1. Cada regla o límite vive en un solo sitio y con nombre.
- S2. Los nombres dicen lo que hacen (eventos, campos, tipos).
- S3. Cada camino que el usuario puede seguir tiene un test que falla si se rompe.
- S4. La documentación y los comentarios dicen exactamente lo que hace el código.

## Tareas

### Constantes y límites (S1)

- [x] T1. Mínimo de 12 caracteres de la contraseña de sesión repetido en `App.vue` y en la etiqueta de `SessionDialog.vue`: constante compartida. (R2-session-min-length-split, trozo 4)
- [x] T2. Tamaño de página 30 repetido en `GroupsTable`, `RecordsTable` y `TrashView`: constante compartida. (R2-page-size-constant, trozo 5)
- [x] T3. Límite de 1000 IDs de `TrashRecords` sin nombre, y la comprobación de lista vacía de `Workspace.trash` no se alcanza desde la API: constante con nombre y comentario de qué capa valida. (R4-001, R2-trash-limits-and-dead-guard, trozo 1)
- [x] T4. Límites de validación de sesión (100 000 registros, 15 archivos, 100 000 caracteres, 1024 en nombres) como números sueltos en `session_snapshot.py`: constantes con nombre, enlazadas a los límites de subida de la API. (R2-001, trozo 3)

### Nombres (S2)

- [x] T5. Se eliminaron `_restored` y `session_saved` por no tener consumidores; el formato `.pwc` permanece intacto. (R2-002, trozo 3)
- [x] T6. `WelcomePanel` y `SettingsView` comparten `sessionRequested(mode)`; el evento de archivos arrastrados es `filesDropped(FileList)`. (R2-session-emit-shape, R2-drop-event-name, trozo 5)
- [x] T7. `CredentialType` define una vez `'web' | 'android'` para `CredentialSummary`, `DuplicateGroup`, `FilterType` y `labelType`. (R2-labeltype-literal-union, trozo 4)
- [x] T8. El selector del editor reutiliza `labelReview` y conserva sus aclaraciones «sin verificar acceso» y «manualmente». (R2-review-options-duplicate-labels, trozo 4)
- [x] T9. `SCREENS` describe el icono y si muestra contador; la navegación usa esos metadatos visuales. (R2-trash-special-case, trozo 4)
- [x] T10. La importación usa `ImportedFile` con campos nombrados; la API normaliza una vez el nombre base y `Workspace` exige metadatos válidos. (R2-004, trozo 2)

### Tests que faltan (S3)

- [x] T11. Importar arrastrando CSV a la bienvenida y con «Importar otros CSV». (R3-single-file-input-untested, trozo 5)
- [x] T12. Errores de descarga con `detail` que no es texto, cuerpo que no es JSON y fallo al guardar sesión. (R3-001, trozo 6)
- [x] T13. La tarjeta móvil de «Todas» muestra `Web`/`Android`. (R3-mobile-type-label, trozo 4)
- [x] T14. El diálogo de sesión se abre vacío tras cerrarlo con datos escritos. (R3-session-secret-reset-untested, trozo 4)
- [x] T15. Detección de Firefox con variantes de cabecera (`http_realm`, espacios). (R2-002, R3-header-key-normalization, trozo 2)

### Interfaz (S3)

- [x] T16. El aviso flotante de error tapa título y acciones de la cabecera (p. ej. «Exportar Bitwarden» en móvil) hasta cerrarlo: aplicar la decisión aprobada de mantenerlo en la parte inferior hasta su cierre, con posición contextual en diálogos y test. (R3-002, trozo 6)

### Documentación y comentarios (S4)

- [x] T17. Resuelta por la redacción vigente de `docs/implementacion-v0.1.md`: ya no afirma que cada pantalla y diálogo sea un componente independiente; no requiere cambios adicionales. (R2-doc-overclaims-frontend-split, trozo 6)
- [x] T18. Resuelta por T16: se eliminó el comentario sobre «la cabecera fija» al extraer `ErrorNotice.vue`; el nuevo comentario describe su ubicación en el diálogo activo, fuera del contenido desplazable. No procede referirse ahora a `.sticky-head`. (R2-misleading-error-placement-comment, trozo 6)

## Registro

- L1. «genera una task con las observaciones de los revisores iremos a por ellas de 1 en 1 en la proxima sesion y haz push a main»
- L2. Para T16 se aprobó mantener el aviso en la parte inferior hasta su cierre, con posición contextual en diálogos.
