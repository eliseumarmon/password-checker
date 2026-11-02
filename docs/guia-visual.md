# Password Checker — Guía visual y de interacción

Criterios de diseño e interacción: qué debe cumplir la interfaz y por qué. No describe cómo funciona hoy la aplicación, que está en el [flujo de usuario](flujo-usuario.md), ni las ideas aún sin implementar, que están en el [trabajo pendiente](pendiente.md). Nació como propuesta de diseño el 29 de octubre de 2026.

## 1. Concepto estético

**Personalidad:** herramienta de trabajo privada, precisa, sobria y amable. Inspiración funcional: agrupaciones claras de Google Password Manager, **sin reproducir su marca ni su interfaz**.

**Principios de producto:**

1. **La información antes que la decoración.** Mostrar primero el problema que hay que resolver, no un panel de cifras sin salida.
2. **Comparación a la vista.** Registros relacionados se muestran juntos antes de sugerir fusionarlos.
3. **Acción reversible.** Una decisión de limpieza no destruye ni edita el CSV original.
4. **Privacidad predecible.** Contraseñas ocultas al iniciar; revelación individual y explícita. El nombre de usuario aparece completo para poder comprobar la identidad de la cuenta.
5. **Continuidad.** La revisión de cientos de registros debe poder retomarse sin repetir trabajo.
6. **Sin falsear certezas.** «Revisado» no significa «Acceso verificado»; no haber consultado filtraciones no significa «Sin filtraciones».

**Lenguaje de interfaz:** español sencillo, acciones concretas: «Comparar», «Descartar» (a la papelera), «Restaurar», «Deshacer», «Guardar sesión cifrada». Evitar etiquetas ambiguas como «Arreglar» y «Seguro» cuando no se haya comprobado nada.

## 2. Sistema visual

### 2.1 Paleta propuesta

| Token | Oscuro predeterminado | Claro alternativo | Función |
|---|---|---|---|
| `surface/page` | `#0B1017` | `#F6F8FB` | Fondo general |
| `surface/card` | `#141C27` | `#FFFFFF` | Tarjetas y paneles |
| `surface/raised` | `#1B2635` | `#EEF2F7` | Menús y capas |
| `text/primary` | `#F1F5F9` | `#172437` | Texto principal |
| `text/secondary` | `#B6C4D5` | `#506176` | Metadatos y ayudas |
| `accent` | `#7CC4FF` | `#125CA8` | Foco, enlaces, selección |
| `success` | `#61D6B1` | `#167450` | Comprobado / terminado |
| `warning` | `#FFD07A` | `#935500` | Reutilización / revisión |
| `danger` | `#FF929D` | `#AD3043` | Conflicto / alerta |
| `border/control` | `#62758F` | `#7F8DA0` | Contornos interactivos |

Colores **propuestos**, sujetos a mediciones automáticas de contraste en implementación: AA en texto normal (≥ 4,5:1), ≥ 3:1 para componentes/indicadores significativos y foco visible. Los estados siempre se identifican además con **texto e icono**, nunca solo color.

No utilizar verde para indicar que una contraseña es «segura» si únicamente ha superado reglas locales básicas. «Sin alertas locales» es más preciso.

### 2.2 Tipografía, dimensiones y ritmo

- Tipografía del sistema (sin fuentes remotas): `Segoe UI`, `Roboto`, `Noto Sans`, `Arial`, sans-serif. Contraseñas y fragmentos técnicos en monoespaciada del sistema **solo cuando estén revelados**.
- Escala: título de pantalla **24–28 px**; título de sección **18–20 px**; cuerpo **16 px**; datos de tabla **14–15 px**; ayuda **13–14 px**; evitar textos inferiores a 13 px.
- Espaciado base **4 px**; intervalos 8, 12, 16, 24 y 32 px. Radio **8 px** controles, **12 px** tarjetas, **16 px** paneles.
- Controles táctiles: objetivo **44 × 44 px o mayor**, salvo controles de escritorio claramente diferenciados. El mínimo WCAG 2.2 AA es 24 × 24 px con excepciones.
- Iconos de **18–24 px**, siempre acompañados de etiqueta accesible. Iconografía sencilla y consistente, sin depender de favicons externos.
- Movimiento: transiciones discretas **120–180 ms**, sin animación obligatoria. Respetar `prefers-reduced-motion`.
- Foco de teclado destacado (contorno sólido de 2 px, color contrastado). Componentes tabulares navegables con teclado.

### 2.3 Tipos de información y estados visuales

| Tipo | Forma | Qué significa |
|---|---|---|
| Duplicado exacto | Indicador neutro «Copia exacta» | URL canónica, usuario exacto y contraseña iguales; pueden diferir notas y procedencia |
| Conflicto | Icono alerta y texto «Contraseñas diferentes» | Misma cuenta aparente, variantes que requieren comprobación |
| Cuenta distinta | Indicador «Varias cuentas» | Mismo sitio, distinta identidad; normalmente conservar |
| Reutilización | Icono advertencia + «Usada en N cuentas» | Misma contraseña en cuentas distintas; **no** equivale a duplicado |
| Pendiente | Punto + texto «Pendiente» | No revisado |
| Revisado | Check de revisión + texto «Revisada» | Inspeccionado sin confirmar acceso |
| Verificado | Check de acceso + texto «Verificada» | El usuario declara que ha iniciado sesión correctamente |
| Incorrecto | Icono X + texto «No funciona» | Requiere corrección manual |
| En la papelera | Icono de basura y sección «Papelera» | No saldrá en el CSV; se restaura desde la papelera |

El estado de **revisión** y el estado de **seguridad** son independientes. Las ediciones de URL/usuario/contraseña invalidan la verificación previa; una edición de notas no.

## 3. Arquitectura de información

Las pantallas actuales se describen en el [flujo de usuario](flujo-usuario.md). Criterios:

- Duplicados y reutilización son problemas distintos y no se mezclan: los duplicados se tratan en **Credenciales** y la reutilización en **Auditoría**.
- La auditoría no falsea certezas: las filtraciones aparecen como «no comprobadas», nunca como «0».
- Las acciones transversales, **Guardar sesión cifrada** (con una sesión abierta) y **Exportar a Bitwarden**, están siempre visibles.

## 4. Vista de escritorio: comparación intensiva

**Ancho de diseño:** 1280–1600 px (referencia 1440); disposición adaptable a pantallas ≥ 1100 px. El escritorio es la herramienta principal de consolidación, no una versión móvil estirada.

**Estructura:** barra lateral de **220–240 px**, contraíble a iconos (**64 px**); cabecera de **64–72 px**; contenido central flexible. Tabla de datos con encabezado fijo y ordenación explícita (`asc/desc/ninguna`). La edición (hasta **760 px**) y la comparación de duplicados (hasta **900 px**, registros lado a lado) se abren en diálogos centrados. La cabecera con título, acciones y estadísticas y la barra lateral quedan fijas al desplazarse.

**Tabla por defecto (Duplicados):** sitio, tipo, usuario, cantidad de registros, coincidencias URL/usuario/contraseña, fuentes, estado y acción. **No mostrar la contraseña en texto en la tabla**. Las contraseñas solo se comparan dentro del grupo y sin mostrarlas. El valor real de usuario es visible (truncar solo visualmente; tooltip/copia accesible).

**Panel comparativo:** registros lado a lado o apilados, con su procedencia (navegador y número de fila). Mostrar el motivo técnico de coincidencia, sin exponer contraseñas.

**Vista Todas:** tabla ordenable y filtrable. Edición en panel, no en una cuadrícula de inputs siempre visible; evita cambios accidentales.

**Interacción teclado:** `Tab` recorre controles, `Enter` abre registro, `Ctrl/Cmd+Z` deshace una operación dentro del editor; confirmar de forma explícita las acciones destructivas. El comportamiento de `Esc` y del cierre de diálogos se describe en el [flujo de usuario](flujo-usuario.md). No utilizar atajos para revelar contraseñas globalmente.

## 5. Vista móvil: verificación y continuidad

**Anchos de referencia:** 360, 390 y 430 px; diseño compacto < 720 px. Optimizar para una mano, zoom y teclados virtuales. **No comprimir la tabla de escritorio** ni imponer desplazamiento horizontal.

**Navegación:** barra inferior fija, respetando `safe-area-inset-bottom`. Tarjetas compactas en lugar de filas, con 1 acción principal por tarjeta. El detalle muestra identidad, URL y botón para abrir la web, contraseña oculta con revelado individual, notas editables, procedencia y estado.

**Comparación móvil:** tarjetas apiladas, con indicadores de coincidencia siempre visibles. Confirmación y deshacer. Usar acordeones para metadatos secundarios, pero **no esconder la razón del conflicto**.

**Android:** filtro `Aplicaciones Android` y nombre del paquete; no representar `androidapp://` como enlace web. Nunca suponer que el esquema identifica una actividad Android lanzable; el identificador del paquete por sí solo no garantiza un enlace de apertura.

**Acceso móvil a la app:** primera solución de diseño mediante conexión USB + ADB reverse manteniendo el backend en `127.0.0.1` del PC; no habilitar el servidor en LAN por defecto. No considerar el acceso mediante Wi-Fi inseguro como característica lista para usar.

**Usabilidad táctil:** controles ≥44 px, barra de acción inferior cuando se edita, teclado no tapa guardar/cancelar, no exigir arrastrar archivos (botón nativo «Seleccionar archivos»). Mostrar progreso, pendiente y capacidad de reanudar.

## 6. Biblioteca de componentes

1. **Dropzone + selector de archivos:** admite varios CSV; identifica navegador por cabecera, no solo por nombre de fichero; muestra recuento y errores específicos; los originales quedan intactos.
2. **Chip de coincidencia:** «URL ✓ / Usuario ✓ / Clave ≠» sin mostrar secretos. `≠` no implica contraseña incorrecta.
3. **Comparador de registros:** original inmutable frente a candidato editable; procedencia visible.
4. **Campo secreto:** oculto por defecto, control con etiqueta «Mostrar contraseña»; nunca revelar todas al cargar.
5. **Enlace de servicio:** clic explícito abre **pestaña nueva** solo para URL web `http(s)` validada, con `noopener noreferrer`; si hay credenciales en URL, exigir revisión y no abrirla tal cual. No usar favicons remotos.
6. **Ficha de revisión:** muestra y cambia el estado de revisión; «Revisada» y «Verificada» son estados distintos.
7. **Aviso de edición:** advertir antes de perder cambios sin guardar; no autoaplicar sobre originales.
8. **Desglose de auditoría:** grupos por contraseña reutilizada con número de cuentas, pero **sin el valor de la contraseña en el encabezado**.
9. **Confirmación de exportación:** recuento de credenciales incluidas y de conflictos pendientes; exige confirmación explícita.
10. **Aviso de error:** muestra el motivo concreto, permanece hasta cerrarlo y nunca queda oculto detrás de un diálogo.
11. **Diálogo de confirmación:** propio de la aplicación, no el del navegador; el botón de confirmar nombra la acción y cancelar es la opción que recibe el foco.

## 7. Diseño de datos sensibles

- **No guardar credenciales en `localStorage`, `sessionStorage`, `IndexedDB` ni cachés del navegador**. La sesión activa reside en el proceso local.
- Una sesión para reanudar debe persistirse **cifrada con criptografía estándar autenticada y derivación robusta de clave**, con frase de paso elegida por el usuario. No inventar cifrado; no guardar la frase en el proyecto.
- No guardar contraseñas en trazas, logs, informes Markdown, telemetría ni URLs. Escapar todos los datos CSV antes de pintarlos en el DOM (el CSV es entrada no confiable). Proteger contra peticiones de otras páginas al servicio local.
- No hacer peticiones a Internet para iconos, fuentes, analítica, imágenes o JS; las pruebas de acceso web solo ocurren tras clic explícito en el enlace.
- No añadir botón «Comprobar todas las cuentas automáticamente»: evita bloqueos, CAPTCHAs y exposición de credenciales.
- Exposición temporal: solo una credencial revelada por decisión del usuario; botón «Ocultar» claro, limpieza en bloqueo de sesión y al salir de ficha. Un hombro mirando no debería leer credenciales sin esa acción.
- Los informes y sesiones de revisión pueden contener nombres, URL y usuarios: tratarlos como privados aunque no incluyan contraseñas.

## 8. Criterios de aceptación visual (antes de código)

| Escenario | Debe verse / poder hacerse |
|---|---|
| Escritorio 1440 × 900 | Comparar dos registros y decidir con los originales visibles, sin desplazamiento horizontal de la página |
| Portátil 1280 × 720 | Tabla utilizable con controles de orden/filtro sin superposición |
| Móvil 390 × 844 | Abrir un registro, revelar/ocultar individualmente, editar y marcar estado sin zoom ni desplazamiento lateral |
| Móvil 360 px con teclado abierto | Guardar/cancelar siempre accesible |
| Zoom 200 % y teclado | Foco visible, navegación y controles no ocultos |
| Tema claro y oscuro | Contrastan textos y componentes, nunca depender solo del color |
| 500+ credenciales | Filtros, ordenación y progreso siguen siendo legibles y receptivos |
| Archivo malformado | Mensaje concreto por archivo y fila, sin alterar campos de contraseña silenciosamente |

**Fuentes de criterios generales:** [WCAG 2.2](https://www.w3.org/TR/WCAG22/), [WAI-ARIA: data grid](https://www.w3.org/WAI/ARIA/apg/patterns/grid/), [OWASP: HTML5 Storage](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html), [OWASP: prevención XSS](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

## 9. Fuera de alcance para la primera iteración

- Verificar filtraciones en bases externas (estado **No comprobado**, jamás «0»).
- Comprobar automáticamente la validez de contraseñas iniciando sesión en servicios.
- Acceso en LAN sin autenticación/HTTPS y sin evaluación de riesgos.
- Sincronización con Bitwarden mediante API; primera etapa es CSV.
- Iconos/favicons descargados de servicios externos.
