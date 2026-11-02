# Trabajo pendiente

Este documento reúne lo que la aplicación todavía no hace: limitaciones conocidas, trabajo pendiente, ideas de diseño sin implementar y la validación con personas. Para saber cómo funciona hoy, consulta el [flujo de usuario](flujo-usuario.md); para los criterios de diseño, la [guía visual](guia-visual.md).

## Limitaciones conocidas

- El progreso solo se conserva mientras el backend está activo o si se descarga una sesión cifrada. No hay guardado automático, bloqueo por inactividad ni recuperación de contraseña.
- El comparador muestra coincidencias y procedencia, pero no ofrece una comparación completa de contraseñas y notas originales. Cada registro se abre por separado para editarlo. No hay una vista previa detallada de la exportación.
- El identificador de paquete Android no garantiza un enlace para abrir la aplicación. El acceso desde móvil mediante ADB requiere configuración adicional.

## Trabajo pendiente

- Validación con usuarios: no se han realizado pruebas observadas con personas ni con contraseñas reales (véase [Validación con personas](#validación-con-personas)).
- Una revisión más amplia de accesibilidad y teclado.
- La revisión de dependencias.
- Ejecutar las pruebas E2E en CI: hoy CI ejecuta los tests del backend y compila el frontend, pero no lanza Playwright.
- Una evaluación local de fortaleza más completa.

## Ideas de diseño sin implementar

Proceden de la propuesta de diseño inicial y de las mejoras anotadas en el flujo. No se han validado con usuarios.

- **Interfaz general:** tema claro; ajustes de idioma, tema y caducidad por inactividad; botón «Ocultar todo» en la cabecera; filtro por estado y selector de orden junto a la búsqueda; en «Todas», orden por riesgo y por URL, con los grupos de una misma URL contiguos; continuidad de filtros.
- **Comparación:** revelar contraseñas de forma individual dentro de la comparación; panel comparativo para conservar A, B o ambos, fusionar notas y editar el candidato final, distinguiendo los datos originales (inmutables) de la salida editable; en móvil, acciones «Elegir para exportación», «Conservar ambas» y «Fusionar notas»; una comparación más completa de originales.
- **Ficha:** en móvil, detalle a pantalla completa con navegación «Anterior / Siguiente pendiente»; botón para copiar la contraseña con aviso de portapapeles; fecha local al confirmar manualmente y acciones «Marcar revisada» y «Acceso verificado» separadas; aviso de edición con deshacer e indicación de qué cambió.
- **Exportación:** modal con resultados incluidos y excluidos, conflictos pendientes, destino y formato Bitwarden, en lugar de la confirmación actual con recuentos; resumen y vista previa antes de exportar.
- **Sesión:** bloqueo tras una inactividad configurada que oculte la interfaz y exija reabrir la sesión cifrada.
- **Android:** «Abrir aplicación (si existe mecanismo compatible)» y «Buscar en tienda».
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
