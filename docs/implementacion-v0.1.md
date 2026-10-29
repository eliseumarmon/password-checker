# Primer incremento funcional (v0.1)

**Estado:** funcionalidad implementada, no equivale a completar toda la propuesta de UX. No se ha probado todavía con personas ni con contraseñas reales.

## Implementado

- FastAPI exclusivamente en `127.0.0.1:8000`, origen comprobado, host permitido, sin telemetría, cabeceras `no-store`.
- Vue 3 + TypeScript + PrimeVue, diseño oscuro adaptable a móvil y escritorio.
- Selección múltiple de CSV; importación transaccional; compatibilidad mediante el parser existente.
- Credenciales de origen inmutables y candidatos editables; claves ocultas al iniciar cada editor.
- Vista de duplicados y conflictos, con comparador URL/usuario/contraseña y procedencia.
- Ordenar y buscar en tabla, filtrar web/Android, solo pendientes, editar todos los campos.
- Auditoría offline de reutilización, debilidad básica y campos incompletos. Filtraciones **no comprobadas**.
- Revisada/verificada/incorrecta, edición de contraseña invalida verificación, exclusión reversible, deshacer (30 operaciones).
- Guardado voluntario de sesión cifrada `.pwc` con Argon2id + AES-256-GCM, integridad autenticada y reapertura sin pérdida de progreso.
- Fusión de copias exactas **solo bajo petición** y CSV Bitwarden descargado tras confirmación.

## Pendientes explícitos

1. **Guardado manual:** el progreso permanece en memoria mientras la aplicación está abierta. Para continuar otro día hay que descargar una sesión `.pwc` cifrada y reabrirla más tarde; **no hay autosalvado**. Perder el archivo o su contraseña implica perder ese progreso. El historial de deshacer no se guarda al cerrar.
2. Parser CSV a flujo en memoria: actualmente el adaptador utiliza archivos temporales que elimina en `finally` inmediatamente; extraer la lectura de streams del script legado para evitar escritura temporal de contraseñas.
3. Comparación A/B con más información de los originales (notas, variantes, usuario en dos paneles) y pruebas de accesibilidad/teclado.
4. Validación segura de enlaces Android: el identificador del paquete no permite abrir la app automáticamente desde cualquier navegador.
5. Mejor evaluación local de fortaleza (p.ej. zxcvbn, sin usar servicios externos).
6. Pruebas E2E, revisión de dependencia/CI frontend y validación con usuarios.
7. Refactor adicional del `auditar_contrasenas_local.py`: hoy comparte motor con la GUI y la CLI, pero el script anterior todavía contiene reglas de negocio y presentación; mover gradualmente a dominio puro sin alterar comportamiento de la CLI.

**No debe afirmarse** que se han implementado funciones pendientes. La exportación CSV y las importaciones contienen secretos en claro; almacenar y borrar de acuerdo con el modelo de amenazas documentado.
