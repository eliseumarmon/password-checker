# «Abrir sitio» y normalización de URL

Objetivo: que «Abrir sitio» lleve al recurso guardado (por ejemplo, la página de acceso) sin exponer datos sensibles de la URL, e investigar un caso anómalo de normalización. Son posibles errores funcionales, no mejoras visuales, así que no esperan a la Fase 2.
Rama: `fix/site-link-navigation` desde `main`, cuando se apruebe. Entrega: `ask-on-risk`. Comprobaciones: `python -m unittest discover -s tests`, `ruff check .`, `npm run build` y `npm run e2e`. Estado: planificado, sin empezar; no está aprobado para implementarse. T2 espera a la decisión D9 de la [hoja de ruta](../../docs/hoja-de-ruta.md#d9--qué-url-abre-abrir-sitio).

## Specs

- **S1 — «Abrir sitio» abre solo el origen.** Del usuario: «Cuando haces abrir sitio te lleva a la url normalizada (no a la que está guardada).» «La dirección es complicada coincido en que hay que quitar los datos sensibles al mostrarla, pero tambié te digo que en un caso concreto me ha mandado a una web que no tiene mucho que ver».
  - **Hoy:** `safeWebUrl()` (`frontend/src/api.ts`) devuelve `url.origin`, a propósito: «No potentially sensitive path/query/hash in outbound navigation.» Solo admite `http:` y `https:` y rechaza URL con usuario o contraseña incrustados. Lo usa el botón «↗ Abrir sitio en pestaña nueva» de la ficha (`EditorDialog.vue`).
  - **Caso que lo muestra** (con un dominio ficticio equivalente): la URL guardada es `https://auth.example.edu/cgi-bin/AuthServer`, la página de acceso de un sistema de autenticación, y se abre `https://auth.example.edu`, que no lleva al mismo sitio.
  - **No es la normalización del backend.** El backend normaliza para identificar duplicados (`domain/urls.py`); el frontend recorta para navegar. Son tres conceptos distintos:

    | Concepto | Tratamiento |
    |---|---|
    | URL original | Se conserva sin alterar, como dato importado |
    | URL normalizada | Sirve para identificar coincidencias y duplicados |
    | URL de navegación | Conserva lo necesario para abrir el recurso correcto, con controles de seguridad |

  - **Límite:** no hay una regla universal que sea segura y funcional a la vez. Los parámetros pueden ser necesarios para iniciar sesión o contener tokens, e incluso una ruta puede contener secretos. La regla se decide en D9.
- **S2 — Normalización anómala.** Del usuario: «He encontrado un caso extraño en la normalización […] no lo puedo mostrar aquí.»
  - Se registra como incidencia pendiente de reproducir, sin afirmar todavía que sea un fallo del normalizador.
  - No hace falta la dirección real: se construye un caso ficticio equivalente y se compara la URL original, la identidad normalizada y el enlace que se abre.
- **S3 — Pruebas.** Solo con URL ficticias: URL normales, rutas de acceso, parámetros sensibles (tokens), fragmentos, esquemas no admitidos y credenciales incrustadas.

## Tasks

- [ ] T1 — S1, S3: caracterizar el comportamiento actual con pruebas sobre `safeWebUrl()` y el botón de la ficha, y preparar las opciones de D9 con esos casos. Ruta: inline.
- [ ] T2 — S1, S3: aplicar la regla que se decida en D9. RED primero con los casos de S3. Ruta: inline. Riesgo: punto 2 (decide qué datos de una URL salen hacia otro sitio). Commit propio y verificación independiente.
  - Incluye el aviso de Android para direcciones locales, que hoy supone que solo se abre el origen (L3).
- [ ] T3 — S2: con un caso ficticio equivalente que aporte el usuario, prueba RED en el normalizador. Si no es un fallo, se cierra con la explicación en el Log. Ruta: inline.
- [ ] T4 — Documentación del comportamiento en `docs/flujo-usuario.md`. Ruta: inline.

## Log

- **L1 (2026-11-04).** Origen: anotaciones del usuario sobre una conversación externa, pegada en la sesión, con capturas de otro gestor de contraseñas. Se distribuyen en la hoja de ruta. Fragmentos que afectan a este plan en S1 y S2. La conversación recomendaba priorizar esta corrección antes del rediseño visual («No hay motivo para esperar hasta la Fase 2 para estudiarlo»).
- **L2 (2026-11-04).** Comprobado en `main` (`ec8d167`): `safeWebUrl()` devuelve `url.origin`, con el comentario citado en S1, y solo la usa `EditorDialog.vue`. Los dominios reales de las capturas se sustituyen por otros ficticios, porque el repositorio es público.
- **L3 (2026-11-04).** Segunda revisión externa de la hoja de ruta, aportada por el usuario. Pregunta del usuario: «No se podría desechar todo lo que va tras un ? que suele indicar una query y mantener el resto?» Es la opción B de D9.
  - La revisión señala que detectar datos sensibles con heurísticas «no ofrece garantías suficientes» y propone B por defecto, con la URL completa como alternativa explícita tras confirmar.
  - La recomendación de D9 pasa de C a B. La decisión sigue pendiente.
  - Comprobado en `main`: la ficha muestra la URL completa en su campo (`EditorDialog.vue`), y `window.open` abre con `noopener,noreferrer`.
  - **Nota para T2:** `openSite()` avisa en Android antes de abrir una dirección local, y lo detecta comparando `href` con `^https?://(localhost|127.0.0.1)(:puerto)?$`. Eso supone que `href` es solo el origen. Con B o C, `href` acaba al menos en `/` y el aviso dejaría de aparecer, así que debe comprobar el host.
