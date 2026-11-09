# Trabajo pendiente

Este documento reúne lo que la aplicación todavía no hace: limitaciones conocidas, trabajo pendiente, ideas de diseño sin implementar y la validación con personas. Para saber cómo funciona hoy, consulta el [flujo de usuario](flujo-usuario.md); para los criterios de diseño, la [guía visual](guia-visual.md).

## Limitaciones conocidas

- El progreso solo se conserva mientras el backend está activo o si se descarga una sesión cifrada. No hay guardado automático, bloqueo por inactividad ni recuperación de contraseña.
- El comparador muestra coincidencias y procedencia, pero no ofrece una comparación completa de contraseñas y notas originales. Cada registro se abre por separado para editarlo. No hay una vista previa detallada de la exportación.
- El identificador de paquete Android no garantiza un enlace para abrir la aplicación. El acceso desde móvil mediante ADB requiere configuración adicional.
- «Abrir sitio» abre el origen y la ruta de la URL guardada, sin parámetros ni fragmento (D9). Una página de acceso con parámetros imprescindibles, como algunos inicios de sesión centralizados, puede no abrirse igual; la URL completa sigue visible en la ficha para copiarla. Hay además un caso anómalo de normalización de URL pendiente de reproducir con un ejemplo ficticio equivalente ([site-link-navigation](../odd/tasks/site-link-navigation.md), T3).

## Trabajo pendiente

- Validación con usuarios: no se han realizado entrevistas ni pruebas observadas con personas ni con contraseñas reales (véase [Validación con personas](#validación-con-personas)).
- Accesibilidad en móvil, hallazgos no aprobados de la [revisión de teclado](../odd/done/keyboard-accessibility.md) (L6 y L8): botones y campos de 36 a 43 px de alto, cuando la guía pide 44, y casilla «Solo pendientes» de 18 px; icono de papelera de 16 px, cuando la guía pide 18-24, y «Guardar» y «Cancelar» fuera de la vista al abrir la ficha o la sesión en pantallas muy bajas. Falta además probar con un lector de pantalla y un teclado virtual reales.
- Prueba automática de contraste: medir los pares de texto, borde de control y foco en uso, y exigir 4,5:1 al texto y 3:1 a lo demás (WCAG 1.4.3 y 1.4.11), sin fijar los valores exactos de los colores. Antes hay que decidir qué hacer con los seis bordes de control que no llegan a 3:1 ([css-tokens](../odd/done/css-tokens.md), L7); corregirlos es un cambio visual.
- Dependencias: el endurecimiento está completado ([auditoría de dependencias](auditoria-dependencias.md) y plan en [dependency-hardening](../odd/done/dependency-hardening.md)). Las medidas que quedaban tienen su propio plan, enlazado desde la [hoja de ruta](hoja-de-ruta.md#fase-0--endurecimiento-de-dependencias).
- Una evaluación local de fortaleza más completa.
- Identidad de servicios y duplicados: definir si las credenciales se identifican por la URL/URI encontrada al importar o si se vinculan a un servicio lógico común (web, Android, iOS). Conservar las asociaciones originales y evaluar las consecuencias para la detección de duplicados; pertenecer al mismo servicio no implica fusionarlas automáticamente.

## Funcionalidades planificadas

No hay ninguna en curso. Las fases, los planes de cada funcionalidad y las decisiones pendientes están en la [hoja de ruta](hoja-de-ruta.md); solo la planificación de la Fase 1 está aprobada. La última funcionalidad completada, el [soporte de Safari](../odd/done/safari-support.md) (exportación de Safari o de la app Contraseñas con sus códigos 2FA hasta Bitwarden y contenido de sesión `.pwc` v2), se completó con T8.

## Ideas de diseño sin implementar

Este apartado reúne tanto las mejoras de la propuesta visual inicial como las ideas debatidas para evolucionar Password Checker de consolidador de CSV a gestor de secretos. **No son funcionalidades disponibles ni un plan de trabajo aprobado.** Su estado se indica expresamente: «dirección acordada» describe una intención de producto; «propuesta» es una opción por diseñar; «decisión pendiente» requiere investigación o acuerdo antes de crear tareas. No se han validado con usuarios.

### Mejoras de la interfaz actual

- **Interfaz general:** tema claro; ajustes de idioma, tema y caducidad por inactividad, y una sección de ayuda; botón «Ocultar todo» en la cabecera; filtro por estado y selector de orden junto a la búsqueda; en «Todas», orden por riesgo y por URL, con los grupos de una misma URL contiguos; continuidad de filtros y de la ordenación de cada tabla, al cambiar de pantalla y al recargar; atajo `Ctrl/Cmd+Z` para el «Deshacer» de la aplicación (hoy solo funciona el deshacer nativo dentro de los campos de texto).
- **Comparación:** revelar contraseñas de forma individual dentro de la comparación; panel comparativo que muestre de cada registro la URL original, el nombre, el usuario, la contraseña oculta, las notas y el estado, y permita conservar A, B o ambos, fusionar notas y editar el candidato final, distinguiendo los datos originales (inmutables) de la salida editable; en móvil, acciones «Elegir para exportación», «Conservar ambas» y «Fusionar notas»; una comparación más completa de originales.
  - Antes, hacerla comprensible: agrupar por sitio y, dentro, por usuario, en lugar de comparar cada registro con el primero mediante chips «URL ✓», «Usuario ≠» o «Clave ≠».
  - Identificar con letras (Clave A, B, C) las contraseñas distintas de cada cuenta, sin mostrarlas. Las equivalencias las calcula el backend.
  - Distinguir duplicados exactos, conflictos reales (mismo sitio y usuario, contraseñas distintas) y cuentas distintas, que no son un conflicto.
  - Un indicador «Tiene nota» que se activa al pulsarlo, no al pasar el ratón.
  - Que el estado «En la papelera» ocupe una sola línea.
  - Plan: [compare-resolution](../odd/tasks/compare-resolution.md), Etapa A.
- **Auditoría:** en escritorio, mantener la cuadrícula 2×2 y poder ampliar cualquier categoría a todo el ancho y el alto disponibles; en móvil, un acordeón con una categoría abierta a la vez ([audit-layout](../odd/tasks/audit-layout.md)).
- **Ficha:** en móvil, detalle a pantalla completa con navegación «Anterior / Siguiente pendiente»; botón para copiar la contraseña con aviso de portapapeles; fecha local al confirmar manualmente y acciones «Marcar revisada» y «Acceso verificado» separadas; aviso de edición con deshacer e indicación de qué cambió.
- **Exportación:** modal con resultados incluidos y excluidos, conflictos pendientes, destino y formato Bitwarden, en lugar de la confirmación actual con recuentos; resumen y vista previa antes de exportar.
- **Procedencia de las importaciones (propuesta, Fase 3):** sustituir la lista cerrada de orígenes (`chrome`, `brave`, `firefox`, `safari`, `unknown`) por dos datos.
  - **Formato de exportación**, el que ya se detecta por las cabeceras: `chromium`, `firefox`, `safari` o `generic`. Son nombres de formato y no de motor (Chromium, Gecko, WebKit), porque el CSV con `OTPAuth` también lo exporta la app Contraseñas de Apple, y un CSV de otro gestor con columna de nombre se lee como `chromium`.
  - **Etiqueta** tomada del nombre del archivo, por ejemplo «Portátil del trabajo». Se muestra con ancho fijo y elipsis si no cabe, con el nombre completo al pasar el ratón y en la ficha. Falta resolver los nombres repetidos o que empiezan igual, que recortados se verían idénticos.
  - **Motivo:** con la lista cerrada, reconocer otro navegador (por ejemplo, Vivaldi) exige cambiar el código, y quitar un origen impide abrir las sesiones que lo usaban. Ningún código decide nada según el origen: solo se muestra. Con la etiqueta libre tampoco hace falta un endpoint para añadir orígenes.
  - **Cambia el `.pwc`:** hoy cada credencial guarda solo el origen y la línea, no el archivo del que viene, y al cargar la sesión se exigen exactamente sus campos. Va en el salto de versión de la Fase 3 (D8 y D3). Las reglas de validación de la etiqueta podrán relajarse más adelante, pero no endurecerse, para no invalidar sesiones guardadas.
- **Sesión:** bloqueo tras una inactividad configurada que oculte la interfaz y exija reabrir la sesión cifrada; en la cabecera móvil, un indicador de sesión local o bloqueada.
- **Android:** en el teléfono, «Abrir aplicación (si existe mecanismo compatible)», «Buscar en tienda» y «Marcar verificada».
- **Acceso móvil:** un mecanismo seguro que no dependa de configurar ADB a mano.

### Evolución futura: gestor de secretos con bóveda persistente

La evolución planteada conserva la revisión y auditoría de credenciales que ya existen. No implica sustituirlas ni alterar ahora el funcionamiento de importación, fusión o exportación.

#### Bóveda, almacenamiento y copias de seguridad

- **Dirección acordada — bóveda persistente:** pasar del workspace temporal en memoria a una bóveda que conserve los elementos entre ejecuciones, cifrada en reposo y accesible desde la interfaz. **SQLite es una candidata** para la persistencia, no una arquitectura de almacenamiento ni una elección criptográfica cerrada. Estudiar esquema, migraciones, claves, índices y qué metadatos pueden quedar visibles sin desbloquearla.
- **Dirección acordada — `.pwc` como respaldo portable:** mantener el archivo cifrado para exportar, transportar, verificar y restaurar copias de la bóveda, en lugar de usarlo como único mecanismo de persistencia. La futura copia debería poder incluir diferentes tipos de elementos, sus adjuntos y metadatos necesarios, con comprobación de integridad y restauración atómica. Decidir si restaurar reemplaza la bóveda, permite fusionar o presenta conflictos; nunca sobrescribir secretos silenciosamente.
- **Decisión pendiente — versiones y migraciones:** definir la evolución del contenido de `.pwc` y las migraciones de la futura base de datos. **Estado actual:** el envoltorio cifrado del archivo sigue en versión 1; el contenido de la sesión es versión 2 y rechaza el contenido v1 tras descifrarlo. No prometer compatibilidad retrospectiva ni reintroducir la lectura de v1 sin una decisión nueva.
- **Propuesta — contraseña maestra y ciclo de bloqueo:** desbloquear la bóveda con un secreto maestro y bloquearla por inactividad o a petición del usuario; estudiar derivación de claves, exposición de secretos en memoria, cambio de contraseña, reautenticación para operaciones sensibles y comportamiento ante pérdida de la contraseña. Un diseño de recuperación no debe crear una puerta trasera.
- **Propuesta — historial y auditoría:** registrar cambios de elementos, accesos y operaciones sensibles con fecha, actor y resultado cuando exista identidad de usuario; valorar versiones y recuperación de cambios sin guardar secretos en registros de actividad ni mostrar valores anteriores por defecto. Separar el historial de modificaciones del actual estado «Pendiente/Revisada/Verificada».

#### Modelo de datos y relación entre servicios

- **Propuesta — elemento de bóveda extensible:** un modelo conceptual como `VaultItem`, separado de los registros temporales de importación, con tipo, nombre, identificador estable, etiquetas/colección, notas, campos públicos y campos secretos. Admitir **campos personalizados** y, cuando proceda, adjuntos binarios cifrados. La estructura definitiva, las validaciones y los límites de tamaño están pendientes.
- **Decisión pendiente — servicio, cuenta y acceso:** distinguir una cuenta de sus accesos web, Android, iOS y, quizá, escritorio. Una misma cuenta podría tener varias URL, dominios afiliados o identificadores de paquete, conservando siempre las referencias originales importadas. Estudiar relaciones con servicios lógicos para reducir falsos duplicados y reutilizaciones aparentes; **compartir servicio no autoriza una fusión automática**. Extensiones a accesos SSH, bases de datos o red serían tipos o relaciones nuevas, no categorías disponibles hoy.
  - Hay dos casos que distinguir:
    - una institución cuyo sistema de autenticación común sirve a varios portales: es una cuenta con varias URI, no varias cuentas;
    - un servicio con varias credenciales distintas y de dominios que ni siquiera comparten el registrable, como agrupa el gestor de Google bajo «firefox.com» las de `accounts.firefox.com` y `firefox.mozilla.org`.
  - El servicio lógico es distinto del dominio, y agrupar no es fusionar. Se estudia en [vault-discovery](../odd/tasks/vault-discovery.md) T4.
- **Propuesta — agrupación manual de servicios:** que el usuario cree, renombre y deshaga grupos de servicios, y añada o quite servicios, sin borrar ninguna contraseña. Por ejemplo, reunir varios portales de una institución bajo su nombre.
  - Las agrupaciones manuales prevalecen sobre las sugerencias automáticas, sin cambiar por sí mismas las reglas de seguridad.
  - Se empezaría con grupos simples, sin anidar.
  - Agrupar servicios es una decisión de organización. Asociar varias URI a una credencial afecta a la seguridad si llega el autocompletado.
- **Propuesta — organización y búsqueda:** colecciones personales o de equipo, carpetas/etiquetas, búsqueda en metadatos permitidos, filtros por tipo, estado y pertenencia, y fichas adaptadas a los datos de cada elemento. Determinar qué metadatos podrían usarse en índices sin filtrar información sensible.

#### Tipos de secretos considerados

- **Credenciales de acceso:** usuario, contraseña, URL/identificadores de aplicaciones, TOTP y notas. La importación desde navegadores y la auditoría actuales serían una vía de entrada a la bóveda; generación de códigos TOTP, autocompletado de formularios y comprobación de validez son funciones distintas, **no implementadas ni aprobadas como parte de Safari**.
- **Notas seguras y secretos técnicos:** textos privados, tokens de API, credenciales de servicios, conexiones a bases de datos y redes, contraseñas de servidores y datos de desarrollo. Diseñar sus campos y permisos sin convertir cada caso en un modelo rígido.
- **Tarjetas de pago — propuesta:** tipo distinto de una credencial web, con alias, titular, número, entidad/marca, caducidad y notas. Mostrar el número enmascarado (por ejemplo, los cuatro últimos dígitos) y exigir una acción explícita para revelar o copiar. **No almacenar inicialmente PIN ni CVV** es una cautela propuesta, no una política ya decidida. Importar datos de Google/Wallet o proporcionar autocompletado se estudiaría después de comprobar qué formatos y campos se pueden obtener legítimamente.
- **Archivos secretos y material criptográfico:** claves SSH, certificados, pares de claves, keystores `.jks`/`.p12`/`.pfx`, claves de firma y otros adjuntos. Un elemento debe poder agrupar **archivo cifrado + contraseñas/alias secretos + metadatos de uso** (propósito, proyecto, huellas o fechas), evitando dispersarlos en entradas inconexas. Caso ilustrativo discutido: un keystore de firma de Android, como `app-dev.jks`, junto con su alias, contraseñas y huella; nunca incluir archivos o claves reales en pruebas ni documentación.
- **Decisión pendiente — importadores y exportadores:** evaluar otros formatos o servicios y la futura importación de elementos no basados en contraseñas. Hoy solo deben darse por disponibles las importaciones y la exportación realmente documentadas en el [flujo de usuario](flujo-usuario.md). Cualquier extensión debe preservar secretos no reconocidos o avisar de su descarte; no asumir que los CSV de terceros incluyen toda la información.

#### Compartición, equipos y verificación en dos pasos

- **Propuesta — multiusuario y roles:** estudiar bóvedas personales y de organización, usuarios, grupos/departamentos, colecciones compartidas y permisos por elemento o colección. Caso de uso planteado: informática accede a credenciales de servidores; marketing, a cuentas de Google/SEO/YouTube; la dirección podría tener acceso más amplio. Aplicar mínimo privilegio, distinguir lectura, modificación, compartición y administración, y no confundir «ser administrador» con poseer automáticamente todos los secretos sin definirlo.
- **Propuesta — seguridad de las cuentas compartidas:** resolver la dependencia de códigos SMS o recuperación vinculados al teléfono particular de una persona. Investigar autenticadores TOTP compartidos cuando el servicio lo permita, códigos de recuperación, passkeys/FIDO2, cuentas o delegación institucional y procedimientos de alta, baja y sustitución de empleados. Esto **no implica saltarse verificaciones 2FA** ni que todos los proveedores permitan compartirlas.
- **Decisión pendiente — arquitectura de claves y recuperación empresarial:** definir quién puede descifrar qué en un sistema multiusuario, cómo se conceden y revocan accesos, qué ocurre al cambiar miembros o contraseñas y si existe recuperación organizativa. Resolver el modelo de amenazas antes de elegir cifrado, servidor o sincronización. La seguridad de una bóveda compartida no se consigue solo con filtrar elementos en la interfaz.
- **Propuesta — trazabilidad organizativa:** historial de cambios y accesos, atribución a usuarios, permisos auditables, rotación/traspaso de secretos y aviso de accesos sensibles, sin registrar contraseñas, TOTP ni contenidos de adjuntos en claro.

#### Dispositivos, sincronización e integraciones

- **Decisión pendiente — modo local o centralizado:** valorar primero la experiencia local y después un servicio autohospedado para acceso desde varios equipos, incluso fuera de la LAN mediante un canal seguro. Estudiar sincronización, conflictos, copias, modo sin conexión, disponibilidad del servidor y separación entre cifrado del lado del cliente y almacenamiento del servidor; no hay arquitectura de red ni proveedor seleccionado.
  - **Conexión al servidor autoalojado**, del usuario: «La app permitiría acceder mediante "nombre del servidor" url o cualquier identificador más usuario y contraseña». Los clientes (web, escritorio y las apps móviles) eligen el servidor y se identifican en él, como en los gestores con servidor propio.
  - **Condición de seguridad:** la contraseña de acceso no debe permitir al servidor descifrar la bóveda. El cliente deriva de la contraseña maestra una prueba para iniciar sesión y, por separado, la clave de cifrado. El servidor solo recibe la prueba y guarda la bóveda cifrada, de modo que quien controle el servidor o robe su base de datos no pueda leer los secretos. La arquitectura de claves se estudia en [vault-discovery](../odd/tasks/vault-discovery.md) (T5).
- **Propuesta — experiencia multiplataforma:** acceso seguro desde Windows, Linux y móvil, con bloqueo, protección al revelar/copiar secretos y, si se justifica, integración con navegadores o autocompletado. No presuponer que una GUI servida localmente puede exponerse directamente a Internet sin autenticación, autorización y controles adicionales.
- **Horizonte previsto — extensión de navegador y autocompletado seguro:** una extensión que, con la bóveda desbloqueada, ofrezca las credenciales de la página visitada y rellene usuario y contraseña, como hace Bitwarden. Llega después de la primera bóveda local y es independiente de la evolución empresarial: sirve también con una bóveda personal en el propio equipo.
  - **Primera versión:** el usuario elige la credencial antes de rellenar; sin autocompletado automático. La extensión no guarda contraseñas descifradas de forma persistente.
  - **Canal con la bóveda, sin decidir:** una API local autenticada en `127.0.0.1`, que exige emparejamiento y protección frente a sitios y procesos no autorizados, o Native Messaging, que exige registrar un componente auxiliar por navegador. Se decide con el modelo de amenazas. Ese componente auxiliar no supone recuperar la CLI eliminada.
  - **Condiciones de seguridad:**
    - no enviar credenciales con la bóveda bloqueada;
    - comprobar el origen real de la página (esquema, dominio y puerto);
    - evitar autocompletar en páginas de phishing, formularios no fiables o marcos de otros dominios;
    - que ninguna página web pueda consultar la API local;
    - pedir una acción explícita para usar credenciales de un dominio distinto del asociado.
  - **Agrupar no es autorizar:** agrupar servicios no autoriza el autocompletado en todos ellos.
  - **Navegadores:** primero Chrome y Brave (WebExtensions, Manifest V3); después Edge y Firefox; Safari, más adelante.
  - **Fuera de la primera versión:** copiar TOTP, guardar o actualizar contraseñas nuevas y el autocompletado automático configurable. Passkeys/WebAuthn quedan como investigación futura.
  - Su encaje en la bóveda se prepara en [vault-discovery](../odd/tasks/vault-discovery.md) (T1, T4 y T5).
- **Propuesta — apps para Android e iOS:** del usuario: «Añade como pendiente crear app para android e ios.» Sin diseñar ni planificar.
  - Hoy el uso desde el móvil depende de `adb reverse`, que solo existe en Android, y el backend solo escucha en `127.0.0.1`. En iPhone no hay forma de usarlo.
  - Una app necesita acceder a la bóveda: una bóveda propia en el teléfono o sincronización con la del ordenador. Depende de la primera bóveda (Fase 6) y de la decisión sobre modo local o centralizado; con un servidor autoalojado, la app se conectaría a él con su identificador, usuario y contraseña.
  - Podría sustituir el acceso móvil con ADB y, más adelante, ofrecer el autocompletado del sistema operativo, con las mismas condiciones de seguridad que la extensión de navegador.
- **Restricción vigente — sin CLI:** la interfaz y la arquitectura de la bóveda son el camino actual. **No reintroducir la CLI eliminada**, ni comandos de extracción de secretos o de inyección/ejecución (`run`), como dependencia de estas ideas. Solo reconsiderarlo si el usuario cambia expresamente esta decisión.

#### Preguntas a resolver antes de elaborar un plan

- Elegir el primer alcance útil: bóveda personal local, tipos de elementos básicos y respaldos, o requisitos empresariales desde el inicio; evitar mezclar estas fases en una sola implementación.
- Concretar modelo de amenazas, cifrado autenticado, derivación y rotación de claves, tratamiento de adjuntos, recuperación, límites y protección frente a exposición en API, logs, portapapeles y archivos temporales.
- Definir migración de registros actuales a elementos persistentes; esquema, IDs, identidades de servicio, conflictos y garantías de no perder TOTP u otros campos durante cambios de modelo.
- Investigar las implicaciones de compartir secretos y 2FA, gestionar permisos y revocaciones y elegir cómo probar todo ello con datos ficticios antes de utilizarlo con credenciales empresariales.

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
