# Un papel por documento

Que cada documento de `docs/` y el README tengan un único papel, para que el comportamiento de la aplicación se describa en un solo sitio y no aparezcan contradicciones.
Una rama por tarea desde `main`, encadenadas porque comparten archivos. Solo documentación: no hay tests ejecutables; se comprueba con el inventario de T1, `grep` de enlaces y una comprobación de que los enlaces relativos apuntan a archivos existentes.

## Specs

- S1. Papeles (propuesta aceptada con «Sí»):
  - `docs/flujo-usuario.md`: única fuente de cómo funciona hoy la aplicación (manual de uso y casos límite). Sin plan de validación ni ideas futuras.
  - `docs/guia-visual.md`: criterios de diseño (principios, lenguaje de interfaz, sistema visual, estados, datos sensibles, accesibilidad), propuestas no implementadas, marcadas como tales, y el plan de validación con personas. No describe comportamiento implementado concreto; cuando un componente existe, remite a `flujo-usuario.md`.
  - `README.md`: instalación, uso resumido, seguridad, limitaciones, formatos, arquitectura y pruebas. Supuesto: absorbe `docs/implementacion-v0.1.md`, que se elimina (lo de «v0.1» ya no corresponde a ninguna versión).
- S2. Sin pérdida: cada afirmación de los tres documentos de `docs/` termina en un único sitio, o se elimina por estar duplicada u obsoleta, y queda anotado en el inventario de T1.
- S3. Sin contradicciones: el comportamiento concreto (diálogos, confirmaciones, avisos, atajos) solo se describe en `flujo-usuario.md`; el README lo resume y enlaza, y la guía remite a él.
- S4. Enlaces: ningún enlace apunta a `implementacion-v0.1.md`, y todos los enlaces relativos de `README.md` y `docs/` llevan a archivos existentes.

## Tasks

- [ ] T1. S2, inline. Inventario: tabla con cada sección o afirmación de `implementacion-v0.1.md`, `flujo-usuario.md` y `guia-visual.md` (y sus solapes con el README) y su destino: flujo, guía, README, eliminar por duplicado o eliminar por obsoleto. Se añade a este documento y el usuario lo revisa antes de T2.
- [ ] T2. S1, S3, inline. `flujo-usuario.md`: queda solo el comportamiento actual; recibe del inventario el comportamiento que hoy está en la guía (por ejemplo, el componente 12 y el aviso de error) y en `implementacion-v0.1.md`; el plan de validación y las mejoras por explorar pasan a la guía.
- [ ] T3. S1, S3, inline. `guia-visual.md`: se quitan los detalles de comportamiento implementado o se sustituyen por un enlace a `flujo-usuario.md`; nueva sección «Propuestas no implementadas»; recibe el plan de validación; la cabecera describe su papel.
- [ ] T4. S1, S4, inline. README absorbe `implementacion-v0.1.md` según el inventario; se elimina ese archivo; se actualizan todos los enlaces (`grep -rn "implementacion-v0.1"`) y se comprueba que los enlaces relativos existen.

## Fuera de alcance

Cambiar la aplicación, reescribir el estilo de los textos más allá de moverlos, y los documentos de `odd/tasks/`, que son registro histórico y conservan sus menciones.

## Log

- L1 (2026-11-02). Pregunta original: «Cuál es la verdadera finalidad de los archivos en docs ahora mismo». Respuesta: `implementacion-v0.1.md` es una lista de lo que funciona y sus límites, repetida en parte en el README y en el flujo; `flujo-usuario.md` mezcla un manual fiable con un plan de validación nunca ejecutado; `guia-visual.md` era la especificación previa al código y ha ido acumulando detalles implementados, de modo que mezcla deseos y realidad. El comportamiento queda descrito en tres sitios, lo que provocó las contradicciones de `Esc` y del aviso de error. Propuesta de un papel por documento; al preguntar si se planificaba: «Sí».
- L2. Previsión: unas 250 líneas movidas o reescritas, casi todo traslado; estrategia de entrega `ask-on-risk`, una rama por tarea.
