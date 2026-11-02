# Importación: formato y origen separados

Separar cómo se lee un CSV (formato) de dónde viene (origen), dejar de inventar un origen y avisar de las columnas con datos que se descartan.
Va antes del soporte de Safari (`odd/tasks/safari-support.md`), que se apoyará en esta separación.
Una rama por tarea desde `main`, encadenadas cuando compartan archivos; test primero; solo credenciales ficticias.

## Specs

- S1. Formato por cabeceras: el formato (`chromium`, `firefox` o `generic`) se decide solo con las cabeceras normalizadas, nunca con el nombre del archivo, con prioridad Firefox (cabeceras distintivas) > Chromium (cabeceras distintivas) > genérico (solo las imprescindibles); el origen se infiere después, sin intervenir en el formato, y es lo único que elige las reglas de lectura (reparaciones de Chromium, `httpRealm` de Firefox).
- S2. Origen como metadato: el origen (`chrome`, `brave`, `firefox` o `unknown`) describe la procedencia y no condiciona la lectura. Formato `firefox` → origen `firefox`; formato `chromium` → `brave` si el nombre contiene «brave», `chrome` si contiene «chrome» y `unknown` en otro caso; formato `generic` → `unknown`. No se inventa un origen sin evidencia.

  | Archivo | Formato | Origen |
  | --- | --- | --- |
  | `brave.csv` | `chromium` | `brave` |
  | `chrome.csv` | `chromium` | `chrome` |
  | `mis_contrasenas.csv` | `chromium` | `unknown` |
  | CSV de Firefox renombrado `brave.csv` | `firefox` | `firefox` |
  | `url,username,password` sin más | `generic` | `unknown` |

- S3. Renombrar un CSV no cambia las credenciales importadas (solo puede cambiar el origen inferido).
- S4. `unknown` es un origen válido en todo el flujo: importación, sesión `.pwc` (ida y vuelta) e interfaz, donde se muestra como «Desconocido».
- S5. Columnas en tres categorías:

  | Categoría | Comportamiento |
  | --- | --- |
  | Reconocida e importada | Se procesa normalmente |
  | Reconocida e ignorada a propósito, según el formato (en `firefox`: `formActionOrigin`, `guid`, `timeCreated`, `timeLastUsed`, `timePasswordChanged`) | Se descarta sin aviso |
  | Desconocida con algún valor no vacío | Se importa el resto y se avisa |

  La lista de ignoradas es de cada formato: `guid` en un CSV `generic` sí avisa. «Con datos» significa no vacío tras quitar espacios exteriores (solo para decidirlo; el contenido no se modifica). Una columna desconocida vacía en todas las filas no genera aviso; cada columna desconocida con datos genera su propio aviso con su recuento.
- S6. Avisos: la respuesta de la importación incluye un canal explícito de avisos con archivo, nombre de columna y número de filas con datos, nunca los valores. Ejemplo: «Se han importado 35 credenciales. La columna «extra_secret» contiene datos en 12 filas que no se han importado.» La interfaz lo muestra visible y persistente hasta que el usuario lo cierra, también al cambiar de pantalla.
- S7. Avisos frente a errores: las columnas desconocidas con datos solo avisan; la falta de columnas imprescindibles o una estructura CSV inválida siguen siendo errores que impiden importar (todo o nada).

## Tareas

- [ ] T1. Detección (S1-S3): una función devuelve formato y origen a partir de las cabeceras y del nombre; `read_export` recibe el formato en lugar del origen; tests con la tabla de S2, el CSV de Firefox renombrado, la regresión de Brave por nombre, un nombre largo que contiene «brave» por casualidad y que renombrar no cambia las credenciales.
- [ ] T2. Origen `unknown` (S4): constante con los orígenes válidos (los navegadores más `unknown`) usada por `ImportedFile` y la validación de sesiones; `labelOrigin` en `labels.ts` con «Desconocido» en la tabla, la papelera, la comparación y la ficha; tests de ida y vuelta `.pwc` con `unknown` y E2E de la etiqueta.
- [ ] T3. Columnas y avisos en el backend (S5-S7): clasificar columnas, contar filas con datos en las desconocidas y devolver los avisos en la respuesta de `/api/import`; tests: el valor ficticio de la columna desconocida no aparece en la respuesta, Firefox no genera avisos, `guid` en un CSV genérico sí avisa, columna desconocida vacía o solo con espacios sin aviso, dos columnas desconocidas con avisos y recuentos separados, y los errores de S7 se mantienen.
- [ ] T4. Avisos en la interfaz (S6): mostrar los avisos de importación, persistentes hasta cerrarlos, con aspecto de aviso y no de error; E2E de importación con una columna desconocida y de que el aviso sigue visible al cambiar de pantalla.
- [ ] T5. Documentación: README (formato frente a origen, avisos de columnas) y `docs/flujo-usuario.md`.

Fuera de alcance: elegir el navegador a mano; formatos de gestores (KeePass, 1Password, Bitwarden); Safari, que va en su propia lista.
Relación: `odd/tasks/reliability-hardening.md` T2 (errores de lectura CSV como 422) cubre parte de S7; si se hace antes, T3 lo reutiliza.

## Registro

- L1. Comprobado con CSV ficticios: un CSV de Firefox llamado `brave.csv` ya se detecta como `firefox`; renombrar un CSV de Chromium no cambia la lectura; un archivo de origen desconocido se etiqueta como `chrome`; y una columna `extra_secret` con valor se descarta sin aviso.
- L2. Decisiones del usuario: separar formato y origen antes de Safari; columnas desconocidas con datos → avisar sin bloquear, con nombre de columna y número de filas y nunca valores, aviso persistente hasta cerrarlo; origen desconocido como `unknown`, mostrado «Desconocido»; `chromium` es un formato, no un origen.
- L3. Precisiones de la revisión del plan: prioridad de detección explícita, lista de ignoradas por formato, definición de «con datos» y un aviso por columna, aviso persistente entre pantallas, test de «brave» casual en el nombre.
