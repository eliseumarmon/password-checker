# Soporte de Safari (exportación de Apple)

Importar las contraseñas exportadas desde Safari o la app Contraseñas sin perder los códigos 2FA (`OTPAuth`) y conservarlos hasta la exportación a Bitwarden (`login_totp`).
La aplicación está en desarrollo: el formato de sesión `.pwc` pasa a v2 sin compatibilidad con v1.
Depende de `odd/tasks/import-format-origin.md`, que se hace antes: Safari entra como formato `safari` con origen `safari`.
Una rama por tarea desde `main`, encadenadas cuando compartan archivos; test primero; solo credenciales y secretos TOTP ficticios; se mantiene el lector CSV basado en alias, sin adaptadores nuevos.

## Specs

- S1. Detección: un CSV con cabecera `Title,URL,Username,Password,Notes,OTPAuth` se identifica como `safari` sin depender del nombre del archivo, admitiendo variaciones de mayúsculas y espacios. Prioridad explícita: cabeceras distintivas de Safari, después Firefox, después Chromium (Brave sigue detectándose por nombre de archivo, como hoy).
- S2. Conservación: `OTPAuth` se importa como `totp` en la credencial original y en el candidato editable; columna ausente o vacía → cadena vacía.
- S3. Exportación: `bitwarden_row` rellena `login_totp` con el `totp` vigente del candidato, sin alterar la URI `otpauth://`; antes se verifica que Bitwarden acepta ese formato.
- S4. Confidencialidad: el TOTP se trata como una contraseña. No aparece en resúmenes, listados, grupos, auditoría, mensajes de error, logs ni respuestas generales de la API. Solo viaja en la importación, la ficha de edición, la sesión cifrada y la exportación.
- S5. Sesiones: `.pwc` pasa a versión 2 con `totp` en original y candidato; una sesión v1 se rechaza con un mensaje claro, sin migración.
- S6. Duplicados (confirmado): con la misma URL, usuario y contraseña:
  - mismo TOTP → pueden ser copia exacta (reglas actuales);
  - TOTP distintos y no vacíos → no son copia exacta y no se fusionan;
  - solo uno con TOTP → se fusionan y el resultado conserva ese TOTP;
  - ambos vacíos → comportamiento actual.
  La decisión se toma por grupo (misma URL, usuario y contraseña), no con una clave por copia: si el grupo tiene un único TOTP no vacío, las copias compatibles se fusionan conservándolo; si tiene varios TOTP distintos no vacíos, se conservan todas las credenciales del grupo sin ninguna fusión automática, incluidas las que no tienen TOTP (tampoco se fusionan entre sí). El resultado no depende del orden de importación y ningún secreto se pierde ni se sobrescribe. La clasificación de grupos es coherente con estas reglas.
- S7. Integridad: ninguna columna conocida con datos de la credencial se descarta en silencio. El caso actual (Safari importado como `chrome`, perdiendo `OTPAuth`) queda corregido.
- S8. Edición (confirmado): el editor muestra el TOTP como campo editable, oculto por defecto, con su propio «Mostrar/Ocultar», independiente del de la contraseña. Se puede introducir, sustituir o borrar; el cambio persiste en el candidato, la sesión cifrada y la exportación. No se valida la URI ni se generan códigos.

## Tareas

- [x] T1. Detección de Safari (S1, S7): `safari` en `ORIGINS` y en `FORMATS`; detección por cabeceras normalizadas con la prioridad de S1; tests de cabecera, mayúsculas, espacios, ausencia de `OTPAuth` y sin regresiones en Chromium y Firefox; test de regresión obligatorio: un CSV de Brave reconocido hoy por su nombre sigue identificándose como `brave`.
- [ ] T2. Modelo e importación (S2): `totp` en `Credential` y `Candidate`, vacío por defecto; `read_export` lee el alias normalizado `otpauth`; se propaga del original al candidato; tests con valor presente, vacío y columna ausente.
- [ ] T3. Exportación Bitwarden (S3): verificar en la documentación de Bitwarden que `login_totp` admite una URI `otpauth://`; `bitwarden_row` la escribe; exportación válida sin TOTP; tests de valor exacto y CSV generado.
- [ ] T4. Sesiones v2 (S5, S8): `to_payload`/`from_payload` con `totp` en original y candidato, `version` 2, rechazo explícito de v1, límite de longitud con nombre y errores que nombran el campo sin reproducir el secreto; tests de ida y vuelta, edición persistente y rechazo de v1.
- [ ] T5. Duplicados con TOTP (S6): agrupar primero por identidad (URL, usuario y contraseña), inspeccionar los TOTP distintos del grupo y decidir después qué se fusiona, para evitar una equivalencia no transitiva; adaptar `merge_exact` y la clasificación de grupos. Caso obligatorio: A (TOTP vacío), B (`TOTP_1`) y C (`TOTP_2`) con la misma URL, usuario y contraseña → B y C quedan separados y A no hace de puente. Tests: las cuatro combinaciones de S6, todas las permutaciones de A, B y C, grupos con varias copias sin TOTP, el grupo A1, A2 (sin TOTP), B y C, donde no se fusiona ninguna copia (tampoco A1 con A2), y una fusión posterior que no descarta un TOTP ya conservado.
- [ ] T6. Confidencialidad (S4): `summarize`, grupos, auditoría y respuestas generales sin `totp`; `detail` sí, para el editor; tests de API con un valor ficticio reconocible que no aparece en `/api/workspace`, listados, grupos ni errores.
- [ ] T7. Interfaz y E2E (S1-S4, S8): campo TOTP editable y oculto con su «Mostrar/Ocultar»; editarlo no toca la contraseña; textos de navegadores admitidos con Safari; E2E: importar CSV de Safari, abrir la ficha, editar el TOTP, guardar, guardar y abrir sesión, exportar y comprobar que `login_totp` tiene el último valor.
- [ ] T8. Documentación (S4, S7, S8): README (formatos admitidos), `docs/flujo-usuario.md`, `docs/guia-visual.md`; campo TOTP y su edición; aviso de que los CSV de Apple y de Bitwarden llevan contraseñas y secretos 2FA en texto plano; incompatibilidad de `.pwc` v1.

## Fuera de alcance

Importar el ZIP de Safari; conservar `guid` y fechas de Firefox; diferenciar adicionalmente Edge, Opera y Vivaldi de Chrome (no se modifica ni se elimina la detección existente de Brave); generar códigos TOTP; validar criptográficamente los secretos; bóveda persistente o sincronización.

## Criterios de aceptación global

1. Safari se detecta por la cabecera.
2. Ningún TOTP se pierde en importación, edición, fusión permitida, guardado, restauración o exportación.
3. Dos TOTP distintos y no vacíos nunca se fusionan automáticamente.
4. El TOTP es editable y está oculto por defecto.
5. La exportación Bitwarden refleja exactamente el TOTP vigente del candidato.
6. Los secretos no aparecen en respuestas generales, auditoría, errores ni logs.
7. `.pwc` v2 funciona y `.pwc` v1 se rechaza explícitamente.
8. Los tests existentes de Chromium y Firefox siguen pasando.

## Registro

- L1. «La aplicación está en desarrollo no es necesario mantener compatibilidad con v1. Haz una lista de tareas nueva.»
- L2. Fuentes verificadas: `password_csv_writer.cc` de Chromium (cabecera `name,url,username,password,note`, una fila por dominio afiliado) y la documentación de Apple «Importing data exported from Safari» (columnas `Title,URL,Username,Password,Notes,OTPAuth`; ZIP con `Passwords.csv`).
- L3. Comprobado con un CSV ficticio: hoy `read_upload` lo clasifica como `chrome` y descarta `OTPAuth`.
- L4. S6 confirmada: TOTP distintos y no vacíos impiden la fusión; si solo uno existe, se conserva.
- L5. S8/T7 confirmada: TOTP editable, oculto por defecto, con control de visibilidad propio.
- L6. No se introducen adaptadores CSV ni ampliaciones de producto sin necesidad demostrada.
- L7. T5 revisada: decisión por grupo, caso A/B/C obligatorio con todas sus permutaciones; T1 añade la regresión de Brave por nombre de archivo.
- L8. «Cuando un grupo de identidad contenga varios TOTP distintos y no vacíos, se conservarán todas sus credenciales sin fusiones automáticas dentro del grupo, incluidas las que no tengan TOTP.»
- L9. Orden decidido: primero la separación de formato y origen (`import-format-origin.md`); Safari, después.
- L10 (2026-11-03). Reanudado tras cerrar `import-format-origin.md`. Plan conciliado con el código actual: `BROWSER_SOURCES` se llama hoy `ORIGINS` (`domain/credential.py`) y la detección vive en `detect_format_and_origin` con `FORMATS` (`csv_reader.py`). Decisión derivada de S1 y L2: la cabecera distintiva de Safari es `OTPAuth` (como `httpRealm` en Firefox), porque la exportación documentada de Apple siempre la incluye; sin ella, `Title,URL,Username,Password,Notes` se sigue leyendo como Chromium sin perder datos (`title` y `notes` ya son alias). El formato `safari` no aplica la reparación de título de Chromium. Hasta T2, un `OTPAuth` con datos genera un aviso de columna descartada en lugar de perderse en silencio (S7). T1 en `feat/safari-t1-detection`: RED 7 fallos (detección y `ORIGINS`), GREEN backend 109 tests OK (106 + 3). Revisión (fiabilidad) aprobada con dos avisos, atendidos: pruebas de que un `OTPAuth` con datos avisa sin mostrar el secreto y de que `safari` no repara títulos desplazados (mutación comprobada: aplicarle la reparación hace fallar la prueba); `FORMATS` recupera su orden y añade `safari` al final (solo se usa como pertenencia). Backend 111 tests OK.
