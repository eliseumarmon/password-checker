# Password Checker — Guía visual y de interacción

> **Propuesta de diseño v0.1 · 29 de octubre de 2026 · Pendiente de aprobación.**
>
> Este documento define la experiencia prevista, **no declara funcionalidad implementada**. Se complementa con [Flujo de usuario y validación](flujo-usuario.md).

## 1. Concepto estético

**Personalidad:** herramienta de trabajo privada, precisa, sobria y amable. Inspiración funcional: agrupaciones claras de Google Password Manager, **sin reproducir su marca ni su interfaz**.

**Principios de producto:**

1. **La información antes que la decoración.** Mostrar primero el problema que hay que resolver, no un panel de cifras sin salida.
2. **Comparación a la vista.** Registros relacionados se muestran juntos antes de sugerir fusionarlos.
3. **Acción reversible.** Una decisión de limpieza no destruye ni edita el CSV original.
4. **Privacidad predecible.** Contraseñas ocultas al iniciar; revelación individual y explícita. El nombre de usuario aparece completo para poder comprobar la identidad de la cuenta.
5. **Continuidad.** La revisión de cientos de registros debe poder retomarse sin repetir trabajo.
6. **Sin falsear certezas.** «Revisado» no significa «Acceso verificado»; no haber consultado filtraciones no significa «Sin filtraciones».

**Lenguaje de interfaz:** español sencillo, acciones concretas: «Comparar», «Conservar ambos», «Descartar» (a la papelera), «Restaurar», «Deshacer», «Guardar sesión cifrada». Evitar etiquetas ambiguas como «Arreglar» y «Seguro» cuando no se haya comprobado nada.

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
| Duplicado exacto | Indicador neutro «3 copias» | URL canónica, usuario exacto y contraseña iguales; pueden diferir notas y procedencia |
| Conflicto | Icono alerta y texto «Contraseñas diferentes» | Misma cuenta aparente, variantes que requieren comprobación |
| Cuenta distinta | Indicador «Otro usuario» | Mismo sitio, distinta identidad; normalmente conservar |
| Reutilización | Icono advertencia + «Usada en N cuentas» | Misma contraseña en cuentas distintas; **no** equivale a duplicado |
| Pendiente | Punto + texto «Pendiente» | No revisado |
| Revisado | Check de revisión + texto | Inspeccionado sin confirmar acceso |
| Verificado | Check de acceso + texto «Acceso comprobado» | El usuario declara que ha iniciado sesión correctamente |
| Incorrecto | Icono X + texto «No permite acceder» | Requiere corrección manual |
| En la papelera | Icono de basura y sección «Papelera» | No saldrá en el CSV; se restaura desde la papelera |

El estado de **revisión** y el estado de **seguridad** son independientes. Las ediciones de URL/usuario/contraseña invalidan la verificación previa; una edición de notas no.

## 3. Arquitectura de información

Tres destinos de primer nivel:

- **Credenciales:** subpestañas `Duplicados` (por defecto tras importar) y `Todas`; comparación, filtro web/Android, edición, origen, decisiones y vista previa.
- **Auditoría:** `Reutilizadas`, `Poco seguras`, `Datos por revisar`, `Filtraciones: no comprobadas`. Agrupación desplegable, estilo de las capturas de referencia. No mezclar duplicados con reutilización.
- **Ajustes:** idioma, tema, privacidad, caducidad por inactividad, exportación, sesión cifrada y ayuda.

Acción transversal visible: **Guardar sesión cifrada** (cuando haya una sesión abierta) y, al final del proceso, **Exportar a Bitwarden** con resumen previo.

## 4. Vista de escritorio: comparación intensiva

**Ancho de diseño:** 1280–1600 px (referencia 1440); disposición adaptable a pantallas ≥ 1100 px. El escritorio es la herramienta principal de consolidación, no una versión móvil estirada.

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Password Checker    Sesión local · 312/480 revisadas          [Ocultar todo] [Guardar] [Exportar]  │
├──────────────────┬──────────────────────────────────────────────────────────────────────────────────┤
│ Credenciales     │ Duplicados       36 grupos  ·  18 pendientes                                 │
│  ├ Duplicados    │ [Buscar nombre, URL o usuario]  [Web/Android ▾] [Estado ▾] [Orden ▾]          │
│  └ Todas         │                                                                                  │
│ Auditoría        │  Sitio ↕      Usuario ↕        Coincide URL  Usuario  Clave   Estado          │
│ Ajustes          │  Example.org   cuenta@example…      ✓         ✓       ≠    Conflicto   >     │
│                  │  Example.org   cuenta@example…      ✓         ✓       =    2 copias    >     │
│                  │  Otra web      otro usuario          ✓         ≠       —    Dos cuentas >     │
│                  │                                                                                  │
│                  │             Seleccionar grupo → panel de comparación                             │
└──────────────────┴──────────────────────────────────────────────────────────────────────────────────┘
```

**Estructura:** barra lateral de **220–240 px**, contraíble a iconos (**64 px**); cabecera de **64–72 px**; contenido central flexible. Tabla de datos con encabezado fijo y ordenación explícita (`asc/desc/ninguna`). La edición de una fila se abre en un diálogo centrado (hasta **760 px**); la comparación de duplicados, en panel lateral de **380–460 px**.

**Tabla por defecto (Duplicados):** sitio, tipo, usuario, cantidad de registros, coincidencias URL/usuario/contraseña, fuentes, estado y acción. **No mostrar la contraseña en texto en la tabla**. Comparaciones solo dentro del grupo, con controles individuales para revelarla. El valor real de usuario es visible (truncar solo visualmente; tooltip/copia accesible).

**Panel comparativo:** registros originales lado a lado o apilados, encabezados «Chrome», «Brave», «Firefox» y número de fila. Visualizar URL original, nombre, usuario, contraseña oculta, notas y estado. Selección de conservar A/B/ambos, fusionar notas y edición en el candidato final. Distinguir datos originales (inmutables) de la salida editable. Mostrar el motivo técnico de coincidencia, sin exponer contraseñas.

**Vista Todas:** tabla ordenable por nombre, URL, usuario, tipo, origen, riesgo y estado, con filtro `Solo pendientes` y grupos de URL contiguos al ordenar. Edición en panel, no en una cuadrícula de inputs siempre visible; evita cambios accidentales.

**Interacción teclado:** `Tab` recorre controles, `Enter` abre registro, `Esc` cierra panel/cancela edición sin guardar, `Ctrl/Cmd+Z` deshace una operación dentro del editor; confirmar de forma explícita las acciones destructivas. No utilizar atajos para revelar contraseñas globalmente.

## 5. Vista móvil: verificación y continuidad

**Anchos de referencia:** 360, 390 y 430 px; diseño compacto < 720 px. Optimizar para una mano, zoom y teclados virtuales. **No comprimir la tabla de escritorio** ni imponer desplazamiento horizontal.

```text
┌─────────────────────────────────┐
│ Password Checker   [● Local] [⋯]│
│ Revisar duplicados               │
│ 312 de 480 revisadas             │
│ [██████████░░░░░] 65 %           │
│ [Buscar sitio o usuario         ]│
│ [Pendientes ▾] [Web / Android ▾] │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Example.org       Conflicto │ │
│ │ cuenta@example.com           │ │
│ │ URL ✓  Usuario ✓  Clave ≠   │ │
│ │ 2 variantes      [Comparar] │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ App Android     3 registros │ │
│ │ paquete.example.app          │ │
│ │ Revisada          [Abrir]   │ │
│ └─────────────────────────────┘ │
│                                 │
├─────────────────────────────────┤
│ Credenciales   Auditoría Ajustes│
└─────────────────────────────────┘
```

**Navegación:** barra inferior fija con 3 opciones, respetando `safe-area-inset-bottom`; cabecera con sesión local/bloqueada. Tarjetas compactas en lugar de filas, con 1 acción principal por tarjeta. Al entrar, detalle de pantalla completa (no modal estrecho): identidad, URL y botón «Abrir web», contraseña oculta con ojo individual, notas editables, fuentes, riesgos, verificación y navegación `Anterior / Siguiente pendiente`.

**Comparación móvil:** tarjetas A y B apiladas, con indicadores de coincidencia siempre visibles; acción `Elegir para exportación`, `Conservar ambas`, `Fusionar notas`. Confirmación y deshacer. Usar acordeones para metadatos secundarios, pero **no esconder la razón del conflicto**.

**Android:** filtro `Aplicaciones Android` y nombre del paquete; no representar `androidapp://` como enlace web. En teléfono mostrar `Abrir aplicación (si existe mecanismo compatible)` / `Buscar en tienda` / `Marcar verificada`. Nunca suponer que el esquema identifica una actividad Android lanzable; el identificador del paquete por sí solo no garantiza un enlace de apertura. Para `127.0.0.1` mostrar el aviso «Esta dirección apunta a este dispositivo».

**Acceso móvil a la app:** primera solución de diseño mediante conexión USB + ADB reverse manteniendo el backend en `127.0.0.1` del PC; no habilitar el servidor en LAN por defecto. No considerar el acceso mediante Wi-Fi inseguro como característica lista para usar.

**Usabilidad táctil:** controles ≥44 px, barra de acción inferior cuando se edita, teclado no tapa guardar/cancelar, no exigir arrastrar archivos (botón nativo «Seleccionar archivos»). Mostrar progreso, pendiente y capacidad de reanudar.

## 6. Biblioteca de componentes

1. **Dropzone + selector de archivos:** admite varios CSV; identifica navegador por cabecera, no solo por nombre de fichero; muestra recuento y errores específicos; los originales quedan intactos.
2. **Chip de coincidencia:** «URL ✓ / Usuario ✓ / Clave ≠» sin mostrar secretos. `≠` no implica contraseña incorrecta.
3. **Comparador de registros:** original inmutable frente a candidato editable; procedencia visible.
4. **Campo secreto:** oculto por defecto, ojo con etiqueta «Mostrar contraseña», botón copiar opcional con aviso de portapapeles; nunca revelar todas al cargar.
5. **Enlace de servicio:** clic explícito abre **pestaña nueva** solo para URL web `http(s)` validada, con `noopener noreferrer`; si hay credenciales en URL, exigir revisión y no abrirla tal cual. No usar favicons remotos.
6. **Ficha de revisión:** estado, fecha local si se confirma manualmente, acciones «Marcar revisada» y «Acceso verificado» separadas.
7. **Aviso de edición:** cambios pendientes, deshacer, indicación de qué cambió; no autoaplicar sobre originales.
8. **Desglose de auditoría:** grupos por contraseña reutilizada con número de cuentas, pero **sin el valor de la contraseña en el encabezado**.
9. **Modal de exportación:** resultados incluidos/excluidos, conflictos pendientes, destino y formato Bitwarden; exige confirmación explícita.
10. **Bloqueo de sesión:** tras inactividad configurada; oculta la UI y exige reabrir la sesión cifrada cuando proceda.

## 7. Diseño de datos sensibles

- **No guardar credenciales en `localStorage`, `sessionStorage`, `IndexedDB` ni cachés del navegador**. Mantener sesión activa en el proceso local; se requerirá modelo de amenazas y controles del servidor antes de implementarlo.
- Una sesión para reanudar debe persistirse **cifrada con criptografía estándar autenticada y derivación robusta de clave**, con frase de paso elegida por el usuario. No inventar cifrado; no guardar la frase en el proyecto. Es una **propuesta de requisito**, no una funcionalidad existente.
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

**Estado:** diseño propuesto para aprobación, sin implementación de UI ni cambios de comportamiento aprobados por esta guía.