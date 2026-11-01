# Estado de implementación

La aplicación es una interfaz local FastAPI + Vue 3 para revisar credenciales y exportarlas en formato Bitwarden. Requiere Python 3.12 o posterior. No se han realizado pruebas observadas con personas ni con contraseñas reales.

## Implementado

- `app.py` inicia el servidor en `127.0.0.1:8000`. La API valida origen y host y envía cabeceras `no-store`. La interfaz no utiliza telemetría ni fuentes externas.
- La importación admite hasta 15 CSV, 5 MiB por archivo y 20 MiB en total. Se aplica de forma transaccional y reemplaza la sesión anterior tras confirmación en la interfaz.
- Los originales se mantienen inmutables; los candidatos se pueden editar, marcar como pendientes, revisados, verificados o incorrectos, descartar y restaurar. Cambiar la identidad o la contraseña invalida la verificación. El historial en memoria permite deshacer hasta 30 operaciones.
- Hay listas de duplicados y registros, búsqueda y filtros, un comparador de coincidencias con procedencia y un editor individual con contraseña oculta inicialmente. La fusión de copias exactas requiere confirmación y conserva notas distintas.
- La auditoría local identifica reutilización, debilidad básica y datos incompletos. No comprueba filtraciones ni inicia sesión en servicios.
- La sesión se puede descargar manualmente en `.pwc` con Argon2id y AES-256-GCM y abrir más tarde. Se recuperan los registros, ediciones y estados guardados; no se recuperan el historial de deshacer ni los filtros o la pantalla seleccionada.
- La exportación descarga un CSV Bitwarden tras confirmar el número incluido y los grupos con conflicto. La interfaz presenta tablas en escritorio y tarjetas en pantallas pequeñas.
- Hay pruebas unitarias, de API y E2E con datos ficticios. El dominio puro vive en `backend/password_checker/domain/`, el espacio de revisión en `application/`, los adaptadores en `infrastructure/` y la API conecta con `frontend/src/`.

## Limitaciones y trabajo pendiente

- El progreso solo se conserva mientras el backend está activo o si se descarga una sesión cifrada. No hay guardado automático, bloqueo por inactividad ni recuperación de contraseña.
- El parser multipart del framework podría usar almacenamiento temporal durante las subidas. El lector CSV propio procesa los datos en memoria y no crea archivos temporales explícitos.
- El comparador muestra coincidencias y procedencia, pero no ofrece una comparación completa de contraseñas y notas originales. Cada registro se abre por separado para editarlo. No hay una vista previa detallada de la exportación.
- El identificador de paquete Android no garantiza un enlace para abrir la aplicación. El acceso desde móvil mediante ADB requiere configuración adicional.
- Siguen pendientes la validación con usuarios, una revisión más amplia de accesibilidad y teclado, la revisión de dependencias y CI frontend, y una evaluación local de fortaleza más completa.

Los CSV importados y exportados contienen secretos en texto plano. Protege también el archivo cifrado, que incluye credenciales y notas originales.
