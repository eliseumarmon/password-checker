# Password Checker

Herramienta local (Python 3.9+, sin dependencias) para **auditar y consolidar exportaciones CSV de Chrome, Brave y Firefox** en un único CSV para **Bitwarden**. Funciona en Windows y Linux y **no accede a Internet**.

## Seguridad y modos

- **Dry-run por defecto**: muestra estadísticas y avisos; no crea ni cambia archivos. Con --report RUTA.md puedes guardar solo el informe de revisión, sin exportar contraseñas.
- `--apply --output RUTA`: crea un CSV nuevo para Bitwarden y un informe `RUTA_informe.md`. No sobrescribe ficheros, ni siquiera los de entrada.
- Las contraseñas **no se imprimen**, transmiten ni incluyen en los informes. El informe Markdown muestra nombres de servicios y usuarios enmascarados. Los enlaces web apuntan solo a la página principal del dominio, sin rutas ni parámetros que pudieran contener tokens.
- **Todos los CSV de entrada y salida contienen contraseñas en texto plano**. No compartir, subir al repositorio, ni guardar en carpetas de sincronización o copias inseguras. El `.gitignore` es una última barrera, no una protección suficiente frente a `git add -f`.
- `--apply` conserva **todas las contraseñas en conflicto**; no adivina cuál sigue siendo válida.

## Uso

Exporta un archivo CSV desde cada navegador. No hace falta exportar por sistema operativo si las cuentas del navegador están sincronizadas.

Linux:

```bash
python3 auditar_contrasenas_local.py --chrome chrome.csv --brave brave.csv --firefox firefox.csv --dry-run --report informe_revision.md
python3 auditar_contrasenas_local.py --chrome chrome.csv --brave brave.csv --firefox firefox.csv --apply --output bitwarden_import.csv
```

Windows PowerShell:

```powershell
py .\auditar_contrasenas_local.py --chrome chrome.csv --brave brave.csv --firefox firefox.csv --dry-run --detalle
py .\auditar_contrasenas_local.py --chrome chrome.csv --brave brave.csv --firefox firefox.csv --apply --output bitwarden_import.csv
```

La opción `--dry-run` es redundante: **es el comportamiento predeterminado**. `--detalle` es opcional. Selecciona el formato **Bitwarden (csv)** al importar el fichero generado.

## Informe Markdown de revisión

- Tabla de **todas las credenciales deduplicadas**, una por registro de Bitwarden (incluidas variantes conflictivas, identificadas por número).
- Columnas: número, prioridad (**Alta / Media / Baja**), página enlazada con el nombre, usuario enmascarado, motivo y **acción recomendada**.
- Ordenadas por prioridad: primero conflictos y contraseñas reutilizadas o evidentemente débiles, después otros avisos y finalmente accesos sin incidencias.
- Incluye resumen con recuentos de duplicados, conflictos y otras incidencias, además de avisos de reparación CSV.
- Nunca incluye contraseñas ni notas. Los enlaces web **solo apuntan al origen del dominio**, no a rutas de recuperación ni parámetros que podrían incluir tokens. Las aplicaciones Android aparecen con su nombre, sin enlace web artificial.
- El informe Markdown es **texto plano**, extensión .md o .txt. Aunque no contiene contraseñas, revela servicios y usuarios parcialmente ocultos; mantenlo en local.

**Modos:** sin --report y en --dry-run no se escribe nada. Con --dry-run --report informe_revision.md solo se guarda la tabla, no se genera CSV de contraseñas. --apply --output bitwarden_import.csv crea automáticamente bitwarden_import_informe.md; usa --report OTRO.md para elegir otra ruta. El script rechaza sobrescribir archivos existentes.

## Formatos de entrada

Chrome y Brave suelen exportar `name,url,username,password,note` (dependiendo de la versión pueden variar). Firefox puede exportar exactamente estas columnas:

```text
url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged
```

El script identifica las columnas por su nombre y acepta BOM UTF-8 y valores entrecomillados, incluidas comas o saltos de línea en notas y contraseñas. En Firefox conserva el `httpRealm` no vacío en las notas. Otros metadatos de Firefox (`guid`, `timeCreated`, etc.) **no tienen correspondencia directa en Bitwarden (csv)** y se descartan.

### Aplicaciones Android

Las URI de apps Android de Chrome/Brave (android://FIRMA@paquete/) no son errores: se convierten a androidapp://paquete igual que el importador de Chrome de Bitwarden: se conserva el paquete tal cual, se descarta la firma y las notas no se modifican. Si una coma sin entrecomillar en el nombre desplaza la URI, el programa puede reconstruirla de forma restringida y mostrar un aviso. Las filas ambiguas se rechazan, nunca se modifican contraseñas silenciosamente.

### Error «número de columnas incorrecto»

Con una exportación CSV válida, una nota que contiene comas o saltos de línea entrecomillados **no causa errores**. Si Chrome muestra, por ejemplo, `chrome: linea 170: 6 columnas, esperadas 5`, el archivo puede estar **mal formado**. Comprueba primero que sea la exportación original, sin editar en Excel/LibreOffice, y prueba a exportarlo otra vez.

Como opción excepcional, si compruebas que **las columnas sobrantes corresponden a comas sin entrecomillar dentro de la última columna `note`**, puedes autorizar la reconstrucción:

```bash
python3 auditar_contrasenas_local.py --chrome chrome.csv --brave brave.csv --firefox firefox.csv --dry-run --repair-extra-notes
```

Tras revisar las líneas indicadas en el informe, ejecuta el mismo comando con `--apply --output bitwarden_import.csv`. **Riesgo:** si las comas no escapadas estaban dentro de la **contraseña**, esta reconstrucción dejaría una contraseña incorrecta. Por eso no se aplica automáticamente y hay que revisar el CSV original de forma privada. Las filas con faltantes ambiguos siguen bloqueando la exportación. Nunca se omiten filas malformadas en silencio.

## Criterios de análisis

- Duplicado exacto: misma URL normalizada, **usuario exacto** y contraseña idéntica; fusiona notas distintas y conserva un registro.
- Conflicto: misma URL + usuario, pero contraseñas diferentes; **conserva ambas**.
- Posibles relacionados: mismo dominio y usuario, pero URLs distintas; avisa, **no fusiona** automáticamente.
- Reutilización: contraseña idéntica utilizada en más de una cuenta. Una cuenta es **origen (esquema + host + puerto) o paquete Android + usuario**: las rutas de una misma web cuentan como una sola cuenta y las apps locales en puertos distintos, como cuentas diferentes. La CLI y la interfaz aplican la misma regla.
- Fortaleza orientativa: longitud y patrones evidentes. **No es una estimación criptográfica ni una comprobación de filtraciones**.
- Riesgos: contraseñas vacías, usuarios vacíos, `http://`, URLs no reconocidas y credenciales incrustadas en URL.
- No fusiona automáticamente credenciales incompletas o ambiguas.

**Limitación de seguridad importante:** la herramienta no determina si una contraseña funciona y no consulta filtraciones ni servicios externos. La importación puede crear entradas duplicadas cuando cambian las rutas del mismo servicio, porque se prioriza no perder contraseñas.

## Arquitectura

`auditar_contrasenas_local.py` es solo el punto de entrada de la CLI. Las reglas se comparten con la interfaz gráfica para que ambas den el mismo resultado:

| Capa | Ruta | Contenido |
| --- | --- | --- |
| Dominio | `backend/password_checker/domain/` | Identidad de URL y cuentas, apps Android, duplicados, conflictos, reutilización, fortaleza y fusión de notas. Sin E/S ni dependencias externas. |
| Infraestructura | `backend/password_checker/infrastructure/` | Lectura de exportaciones CSV (también subidas desde la GUI), formato Bitwarden, cifrado de sesiones y creación exclusiva de archivos privados. |
| Aplicación | `backend/password_checker/application/` | Espacio de revisión de la GUI (estado, deshacer, edición, papelera y fusión), lo que muestra la pantalla de revisión, el volcado de sesión y el informe Markdown. Solo depende del dominio. |
| Adaptadores | `backend/password_checker/cli.py`, `api.py` | Línea de comandos y API local; conectan la aplicación con la infraestructura. |

Las dependencias solo apuntan hacia el dominio; `tests/test_architecture.py` lo comprueba. El dominio, la infraestructura y la CLI funcionan con Python 3.9 sin dependencias.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```

Los tests utilizan únicamente **credenciales ficticias** y nunca dependen de exportaciones reales.

### Tests E2E de la interfaz

```bash
cd frontend
npm ci
npx playwright install chromium   # solo la primera vez
npm run e2e
```

Playwright compila el frontend y arranca un backend propio en el puerto 5173 con el Python de `.venv` (otro intérprete: variable `E2E_PYTHON`), así no toca la sesión de `app.py` en el 8000. No ejecutes a la vez `npm run dev`, que usa el mismo puerto. Los CSV ficticios se generan en memoria dentro de `frontend/e2e/`.

## Después de importar

Verifica las entradas y conflictos en Bitwarden, conserva un respaldo seguro mientras confirmas que todo funciona y elimina los archivos CSV en texto plano. Revisa también copias temporales, carpetas de descargas y sincronización.

## Interfaz gráfica local (primer incremento)

Consulta [la guía de instalación y ejecución](README-GUI.md). Se ha incorporado una interfaz FastAPI + Vue 3 para revisar y editar credenciales. El guardado de sesiones cifradas es **manual** mediante archivos `.pwc` (Argon2id + AES-256-GCM): antes de realizar una revisión larga, consulta las [limitaciones actuales](docs/implementacion-v0.1.md).
