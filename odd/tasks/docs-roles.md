# Un papel por documento

Que cada documento de `docs/` y el README tengan un único papel, para que el comportamiento de la aplicación se describa en un solo sitio y no aparezcan contradicciones. `docs/` sigue con tres archivos: cambia su contenido, no su número.
Una rama por tarea desde `main`, encadenadas porque comparten archivos. Solo documentación: no hay tests ejecutables; se comprueba con el inventario de T1 (archivo de trabajo local, fuera de git), `grep` de enlaces y una comprobación de que los enlaces relativos apuntan a archivos existentes.

## Specs

- S1. Papeles (reparto aceptado con «Sí» tras las correcciones de L2-L4):
  - `docs/flujo-usuario.md`: única fuente de cómo funciona hoy la aplicación (manual de uso y casos límite). Sin plan de validación ni ideas futuras.
  - `docs/guia-visual.md`: solo criterios de diseño (principios, lenguaje de interfaz, sistema visual, estados, datos sensibles, accesibilidad). No describe comportamiento implementado concreto, que remite a `flujo-usuario.md`, ni propuestas pendientes.
  - `docs/pendiente.md`: lo que falta. Es `docs/implementacion-v0.1.md` renombrado (`git mv`), sin su lista de lo implementado, y reúne las limitaciones conocidas, el trabajo pendiente, las ideas no implementadas que hoy están en la guía y en el flujo, y el plan de validación con personas.
  - `README.md`: instalación, uso resumido, seguridad, formatos, arquitectura y pruebas. De sus limitaciones conserva las de seguridad y enlaza a `docs/pendiente.md` para el resto.
- S2. Sin pérdida: cada afirmación de los tres documentos de `docs/` termina en un único sitio, o se elimina por estar duplicada u obsoleta, según el inventario de T1. El inventario es un archivo de trabajo local, `inventario-docs.md` en la raíz, excluido en `.git/info/exclude`: nunca se hace commit y se borra cuando el usuario termine su comprobación externa.
- S3. Sin contradicciones: el comportamiento concreto (diálogos, confirmaciones, avisos, atajos) solo se describe en `flujo-usuario.md`; el README lo resume y enlaza, y la guía remite a él.
- S4. Enlaces: fuera de `odd/tasks/`, ningún enlace apunta a `implementacion-v0.1.md`, y todos los enlaces relativos de `README.md` y `docs/` llevan a archivos existentes.

## Tasks

- [x] T1. S2, inline. Inventario: tabla con cada sección o afirmación de `implementacion-v0.1.md`, `flujo-usuario.md` y `guia-visual.md` (y sus solapes con el README) y su destino: flujo, guía, pendiente, README, eliminar por duplicado o eliminar por obsoleto. Va en `inventario-docs.md` (local, excluido de git) y el usuario lo revisa antes de T2.
- [x] T2. S1, S2, inline. `git mv docs/implementacion-v0.1.md docs/pendiente.md`; se quita la lista de lo implementado y recibe, según el inventario, limitaciones, trabajo pendiente, ideas no implementadas y el plan de validación; cabecera con su papel.
- [x] T3. S1, S3, inline. `flujo-usuario.md`: queda solo el comportamiento actual; recibe el comportamiento que hoy está en la guía (por ejemplo, el componente 12 y el aviso de error) y en la lista de lo implementado; el plan de validación y las mejoras por explorar ya están en `pendiente.md`.
- [ ] T4. S1, S3, inline. `guia-visual.md`: solo criterios; se quitan los detalles de comportamiento implementado (o se sustituyen por un enlace a `flujo-usuario.md`) y las propuestas pendientes, ya en `pendiente.md`; la cabecera describe su papel.
- [ ] T5. S1, S4, inline. README: conserva las limitaciones de seguridad y enlaza a `docs/pendiente.md`; se actualizan todos los enlaces (`grep -rn "implementacion-v0.1"` fuera de `odd/tasks/`) y se comprueba que los enlaces relativos existen. Al cerrar, se comprueba que todas las filas del inventario están aplicadas. `inventario-docs.md` y su línea de `.git/info/exclude` se borran cuando el usuario confirme que ha terminado su comprobación externa.

## Fuera de alcance

Cambiar la aplicación, reescribir el estilo de los textos más allá de moverlos, y los documentos de `odd/tasks/`, que son registro histórico y conservan sus menciones.

## Log

- L1 (2026-11-02). Pregunta original: «Cuál es la verdadera finalidad de los archivos en docs ahora mismo». Respuesta: `implementacion-v0.1.md` es una lista de lo que funciona y sus límites, repetida en parte en el README y en el flujo; `flujo-usuario.md` mezcla un manual fiable con un plan de validación nunca ejecutado; `guia-visual.md` era la especificación previa al código y ha ido acumulando detalles implementados, de modo que mezcla deseos y realidad. El comportamiento queda descrito en tres sitios, lo que provocó las contradicciones de `Esc` y del aviso de error. Propuesta de un papel por documento; al preguntar si se planificaba: «Sí».
- L2 (2026-11-02). Corrección: «guia visual no iba a tener otro papel?». La primera versión del plan daba a la guía, además de los criterios, las propuestas no implementadas y el plan de validación, lo que contradecía «solo criterios de diseño».
- L3 (2026-11-02). Pregunta: «Implementacion que papel tiene entonces?». En la primera versión desaparecía dentro del README. Se propone reaprovecharlo como documento de lo que falta (`pendiente.md`) en lugar de crear uno nuevo.
- L4 (2026-11-02). «Entonces no quedaría un archivo más quedarían 3 archivos iguañ»: confirmado, `docs/` mantiene tres archivos. Al preguntar si se rehacía el plan con este reparto: «Sí». Se reescriben S1, S4 y las tareas T2-T5.
- L5. Previsión: unas 250 líneas movidas o reescritas, casi todo traslado; estrategia de entrega `ask-on-risk`, una rama por tarea.
- L6 (2026-11-02). Corrección: «No, quiero mantener solo 3 archivos lo mantenemos para controlar que no se nos escapa nada, pero finalmente no se hará commit del archivo». El inventario pasa a ser un archivo de trabajo local excluido de git y se borra al terminar; tras borrarlo no queda registro de a dónde fue cada texto, salvo los diffs.
- L7 (2026-11-02). Inventario revisado: «Adelante. Luego usare una comprobación externa para comprobar que no se ha perdido información». El inventario se conserva hasta que el usuario termine esa comprobación. Filas abiertas resueltas: CI ejecuta los tests del backend y compila el frontend, pero no lanza E2E (pendiente: «Ejecutar las pruebas E2E en CI»); «Todas» no ordena por riesgo ni por URL (pendiente). T2 en `docs/t2-pending-doc` (encadenada sobre el plan): `git mv docs/implementacion-v0.1.md docs/pendiente.md`, sin la lista de lo implementado, con limitaciones, trabajo pendiente, ideas sin implementar y la validación con personas (tabla copiada literalmente del flujo). El flujo y la guía conservan esos textos hasta T3 y T4.
- L8 (2026-11-02). T3 en `docs/t3-flow-doc` (encadenada sobre T2). `flujo-usuario.md`: cabecera con su papel y enlaces a `pendiente.md` y a la guía; las cuatro pantallas y tablas frente a tarjetas; editar URL, usuario o contraseña devuelve el registro a pendiente (comprobado en `workspace.py`: vuelve a pendiente desde cualquier estado, no solo desde verificada); aviso de direcciones locales en Android; detalles del diálogo de confirmación y que los demás diálogos no se cierran con `Esc`; aviso de error (comprobado en `ErrorNotice.vue` y `errorHost`). Se quitan la validación con personas y las mejoras, ya en `pendiente.md`.
