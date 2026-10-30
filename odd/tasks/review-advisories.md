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

- [ ] T1. Mínimo de 12 caracteres de la contraseña de sesión repetido en `App.vue` y en la etiqueta de `SessionDialog.vue`: constante compartida. (R2-session-min-length-split, trozo 4)
- [ ] T2. Tamaño de página 30 repetido en `GroupsTable`, `RecordsTable` y `TrashView`: constante compartida. (R2-page-size-constant, trozo 5)
- [ ] T3. Límite de 1000 IDs de `TrashRecords` sin nombre, y la comprobación de lista vacía de `Workspace.trash` no se alcanza desde la API: constante con nombre y comentario de qué capa valida. (R4-001, R2-trash-limits-and-dead-guard, trozo 1)
- [ ] T4. Límites de validación de sesión (100 000 registros, 15 archivos, 100 000 caracteres, 1024 en nombres) como números sueltos en `session_snapshot.py`: constantes con nombre, enlazadas a los límites de subida de la API. (R2-001, trozo 3)

### Nombres (S2)

- [ ] T5. `_restored` («cargado de una sesión») se publica como `session_saved` («sesión guardada»): renombrar o documentar. (R2-002, trozo 3)
- [ ] T6. Evento `session` sin datos en `WelcomePanel` y con modo en `SettingsView`; evento `drop` con el mismo nombre que el nativo pero con `FileList`: nombres distintos y explícitos. (R2-session-emit-shape, R2-drop-event-name, trozo 5)
- [ ] T7. `labelType` declara `'web' | 'android'` a mano: derivarlo de `types.ts`. (R2-labeltype-literal-union, trozo 4)
- [ ] T8. El selector de estado de revisión del editor repite textos que ya están en `labels.ts` (y uno difiere): centralizar o anotar por qué difieren. (R2-review-options-duplicate-labels, trozo 4)
- [ ] T9. `SCREENS` trata la papelera como caso especial en tres sitios (icono vacío, título y contador): marcarlo en la propia lista. (R2-trash-special-case, trozo 4)
- [ ] T10. La forma `(nombre, origen, credenciales)` de la importación solo existe por posición entre `api.py` y `Workspace.import_files`, y el nombre base del archivo se normaliza dos veces: tupla con nombre y una sola normalización. (R2-004, trozo 2)

### Tests que faltan (S3)

- [ ] T11. Importar arrastrando CSV a la bienvenida y con «Importar otros CSV». (R3-single-file-input-untested, trozo 5)
- [ ] T12. Errores de descarga con `detail` que no es texto, cuerpo que no es JSON y fallo al guardar sesión. (R3-001, trozo 6)
- [ ] T13. La tarjeta móvil de «Todas» muestra `Web`/`Android`. (R3-mobile-type-label, trozo 4)
- [ ] T14. El diálogo de sesión se abre vacío tras cerrarlo con datos escritos. (R3-session-secret-reset-untested, trozo 4)
- [ ] T15. Detección de Firefox con variantes de cabecera (`http_realm`, espacios). (R2-002, R3-header-key-normalization, trozo 2)

### Interfaz (S3)

- [ ] T16. El aviso flotante de error tapa título y acciones de la cabecera (p. ej. «Exportar Bitwarden» en móvil) hasta cerrarlo: decidir con el usuario la posición o un cierre automático, con test. (R3-002, trozo 6)

### Documentación y comentarios (S4)

- [ ] T17. `docs/implementacion-v0.1.md` dice que cada pantalla y diálogo es un componente, pero cabecera, estadísticas y barra móvil siguen en `App.vue`: precisar la frase. (R2-doc-overclaims-frontend-split, trozo 6)
- [ ] T18. El comentario sobre el aviso de error habla de «la cabecera fija»; el revisor la confundió con `.topbar`. Nombrar `.sticky-head` explícitamente. (R2-misleading-error-placement-comment, trozo 6; el aviso sí estaba dentro de `.sticky-head`, `App.vue@0325170:144-161`)

## Registro

- L1. «genera una task con las observaciones de los revisores iremos a por ellas de 1 en 1 en la proxima sesion y haz push a main»
- L2. T16 necesita una decisión de producto antes de implementar.
