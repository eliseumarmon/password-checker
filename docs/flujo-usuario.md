# Flujo de usuario y validación

Este documento describe el flujo implementado y reúne propuestas de validación. No se han realizado entrevistas ni pruebas observadas con personas. Véanse el [estado de implementación](implementacion-v0.1.md) y la [guía visual](guia-visual.md).

## Flujo disponible

1. Exporta CSV de Chrome, Brave o Firefox y abre la aplicación local siguiendo la [guía de instalación](../README-GUI.md). Los CSV contienen contraseñas en texto plano: guárdalos en un lugar privado.
2. Selecciona o arrastra hasta 15 CSV. El servidor admite hasta 5 MiB por archivo y 20 MiB en total. Una importación válida reemplaza la sesión activa tras confirmación; si falla alguno de los archivos, no se aplica ninguno. No existe una vista previa antes de importar.
3. En **Duplicados**, abre un grupo para comparar nombre, usuario, URL, origen, línea y coincidencias de URL, usuario y contraseña. La contraseña no aparece en el comparador. Abre cada ficha para ver o editar sus campos y estado de revisión. **Todas** permite buscar, filtrar y abrir registros individuales.
4. Las credenciales se conservan al importar. Puedes mover registros a la papelera y restaurarlos, o usar **Fusionar copias exactas** tras confirmar: se combinan sus notas y las copias sobrantes pasan a la papelera. Las variantes con contraseñas diferentes no se fusionan automáticamente. Hay hasta 30 operaciones para deshacer en la sesión activa.
5. En **Auditoría** revisa reutilización, debilidad básica y datos incompletos. Las filtraciones no se comprueban. Los estados pendiente, revisada, verificada e incorrecta son declaraciones del usuario; editar la contraseña guardada no cambia la del servicio.
6. Para continuar otro día, descarga una sesión cifrada `.pwc` con **Guardar sesión cifrada**. Para reanudarla, usa **Abrir sesión cifrada anterior** y la misma contraseña. Se restauran registros y decisiones guardadas, pero no el historial de deshacer ni la selección o filtros de pantalla. No existe guardado automático ni recuperación de contraseña.
7. **Exportar Bitwarden** pide confirmación e indica el número de credenciales incluidas y de grupos con contraseñas conflictivas. Descarga un CSV en texto plano; selecciona **Bitwarden (csv)** al importarlo. Verifica la migración antes de borrar los originales o el respaldo y elimina después las copias CSV que ya no necesites.

Los enlaces web se abren solo por acción del usuario. Las URI Android no son enlaces web; la comprobación de la aplicación se hace manualmente. El uso desde móvil mediante ADB requiere configuración externa y no forma parte del flujo de instalación documentado.

## Casos y límites relevantes

- Los registros con la misma URL y usuario pero distinta contraseña permanecen separados. La reutilización entre cuentas tampoco implica que deban fusionarse.
- Los orígenes web distinguen esquema, host y puerto para el análisis de reutilización. Las rutas de un mismo origen y usuario cuentan como una cuenta.
- El lector admite comas y saltos de línea entrecomillados. Si la anchura de una fila es ambigua, rechaza la importación; puede completar una nota final vacía y reconstruir de forma restringida un título desplazado por una coma junto a una URI reconocida.
- Abrir otro CSV o sesión reemplaza la revisión en memoria tras confirmación. Guarda antes el `.pwc` si necesitas conservarla.
- El guardado cifrado incluye los datos originales, incluidos secretos y notas. Protege el archivo y su contraseña como un respaldo sensible.

## Propuestas para validar con personas

Las siguientes son metas de diseño, no resultados medidos ni funciones garantizadas. Se propone observar a 4–6 personas con credenciales ficticias, incluyendo navegación por teclado y uso en pantalla pequeña.

| Tarea | Qué observar |
| --- | --- |
| Importar CSV de distintos navegadores | Comprensión de errores, procedencia y reemplazo de sesión |
| Distinguir conflicto de reutilización | Si se conservan cuentas diferentes y se entiende la diferencia |
| Comparar y editar una variante | Si se reconoce la procedencia y se entiende que editar no cambia el servicio |
| Guardar y abrir una sesión | Si se conservan el archivo y su contraseña y se entienden las limitaciones |
| Exportar con conflictos | Si se entiende qué registros se incluyen y que Bitwarden puede crear duplicados |
| Usar la interfaz con teclado o móvil | Foco, acceso a controles, legibilidad y dificultades de navegación |

Entre las mejoras por explorar figuran una comparación más completa de originales, una vista previa de exportación, continuidad de filtros, accesibilidad y un mecanismo seguro de acceso móvil. No se han validado estas propuestas con usuarios.
