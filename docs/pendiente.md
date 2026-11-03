# Trabajo pendiente

Este documento reúne lo que la aplicación todavía no hace: limitaciones conocidas, trabajo pendiente, ideas de diseño sin implementar y la validación con personas. Para saber cómo funciona hoy, consulta el [flujo de usuario](flujo-usuario.md); para los criterios de diseño, la [guía visual](guia-visual.md).

## Limitaciones conocidas

- El progreso solo se conserva mientras el backend está activo o si se descarga una sesión cifrada. No hay guardado automático, bloqueo por inactividad ni recuperación de contraseña.
- El comparador muestra coincidencias y procedencia, pero no ofrece una comparación completa de contraseñas y notas originales. Cada registro se abre por separado para editarlo. No hay una vista previa detallada de la exportación.
- El identificador de paquete Android no garantiza un enlace para abrir la aplicación. El acceso desde móvil mediante ADB requiere configuración adicional.

## Trabajo pendiente

- Validación con usuarios: no se han realizado entrevistas ni pruebas observadas con personas ni con contraseñas reales (véase [Validación con personas](#validación-con-personas)).
- Una revisión más amplia de accesibilidad y teclado.
- La revisión de dependencias.
- Una evaluación local de fortaleza más completa.
- Límites de sesión: cuando la revisión ya supera un límite y un cambio empeora otro, el mensaje de rechazo puede nombrar el límite que no empeoró; y faltan pruebas por HTTP de esos rechazos al importar y al editar. Detalle en [reliability-hardening](../odd/tasks/reliability-hardening.md#deuda-técnica-registrada) (DT1 y DT2).
- Limpiar los avisos existentes de `ruff`, hoy fuera de CI (DT3).
- Optimización del bundle frontend: analizar el aviso de Vite por un chunk superior a 500 kB; valorar división de código y carga diferida sin ocultar el aviso aumentando únicamente el umbral.
- Identidad de servicios y duplicados: definir si las credenciales se identifican por la URL/URI encontrada al importar o si se vinculan a un servicio lógico común (web, Android, iOS). Conservar las asociaciones originales y evaluar las consecuencias para la detección de duplicados; pertenecer al mismo servicio no implica fusionarlas automáticamente.

## Funcionalidades planificadas

Tienen especificación y tareas en su plan, que es donde se sigue su avance:

1. [Soporte de Safari](../odd/tasks/safari-support.md): importar la exportación de Safari o de la app Contraseñas conservando los códigos 2FA hasta la exportación a Bitwarden; la sesión `.pwc` pasa a v2. Se apoya en la separación formato/origen ya completada (plan [importación: formato y origen](../odd/tasks/import-format-origin.md), cerrado con T5).

## Ideas de diseño sin implementar

Proceden de la propuesta de diseño inicial y de las mejoras anotadas en el flujo. No se han validado con usuarios.

- **Interfaz general:** tema claro; ajustes de idioma, tema y caducidad por inactividad, y una sección de ayuda; botón «Ocultar todo» en la cabecera; filtro por estado y selector de orden junto a la búsqueda; en «Todas», orden por riesgo y por URL, con los grupos de una misma URL contiguos; continuidad de filtros; atajo `Ctrl/Cmd+Z` para el «Deshacer» de la aplicación (hoy solo funciona el deshacer nativo dentro de los campos de texto).
- **Comparación:** revelar contraseñas de forma individual dentro de la comparación; panel comparativo que muestre de cada registro la URL original, el nombre, el usuario, la contraseña oculta, las notas y el estado, y permita conservar A, B o ambos, fusionar notas y editar el candidato final, distinguiendo los datos originales (inmutables) de la salida editable; en móvil, acciones «Elegir para exportación», «Conservar ambas» y «Fusionar notas»; una comparación más completa de originales.
- **Ficha:** en móvil, detalle a pantalla completa con navegación «Anterior / Siguiente pendiente»; botón para copiar la contraseña con aviso de portapapeles; fecha local al confirmar manualmente y acciones «Marcar revisada» y «Acceso verificado» separadas; aviso de edición con deshacer e indicación de qué cambió.
- **Exportación:** modal con resultados incluidos y excluidos, conflictos pendientes, destino y formato Bitwarden, en lugar de la confirmación actual con recuentos; resumen y vista previa antes de exportar.
- **Sesión:** bloqueo tras una inactividad configurada que oculte la interfaz y exija reabrir la sesión cifrada; en la cabecera móvil, un indicador de sesión local o bloqueada.
- **Android:** en el teléfono, «Abrir aplicación (si existe mecanismo compatible)», «Buscar en tienda» y «Marcar verificada».
- **Acceso móvil:** un mecanismo seguro que no dependa de configurar ADB a mano.

## Validación con personas

Las siguientes son metas de diseño, no resultados medidos ni funciones garantizadas. Se propone observar a 4–6 personas con credenciales ficticias, incluyendo navegación por teclado y uso en pantalla pequeña.

| Tarea | Qué observar |
| --- | --- |
| Importar CSV de distintos navegadores | Comprensión de errores, procedencia y reemplazo de sesión |
| Distinguir conflicto de reutilización | Si se conservan cuentas diferentes y se entiende la diferencia |
| Comparar y editar una variante | Si se reconoce la procedencia y se entiende que editar no cambia el servicio |
| Guardar y abrir una sesión | Si se conservan el archivo y su contraseña y se entienden las limitaciones |
| Exportar con conflictos | Si se entiende qué registros se incluyen y que Bitwarden puede crear duplicados |
| Usar la interfaz con teclado o móvil | Foco, acceso a controles, legibilidad y dificultades de navegación |
