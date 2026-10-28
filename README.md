# Password Checker

Herramienta local (Python 3.9+, sin dependencias) para **auditar y consolidar exportaciones CSV de Chrome, Brave y Firefox** en un único CSV para **Bitwarden**. Funciona en Windows y Linux y **no accede a Internet**.

## Seguridad y modos

- **Dry-run por defecto**: muestra estadísticas y avisos; no crea ni cambia archivos.
- `--apply --output RUTA`: crea un CSV nuevo para Bitwarden. No sobrescribe ficheros, ni siquiera los de entrada.
- Las contraseñas **no se imprimen**, transmiten ni incluyen en los informes. Los nombres de sitios y usuarios se muestran solo con `--detalle` (usuarios parcialmente ocultos).
- **Todos los CSV de entrada y salida contienen contraseñas en texto plano**. No compartir, subir al repositorio, ni guardar en carpetas de sincronización o copias inseguras. El `.gitignore` es una última barrera, no una protección suficiente frente a `git add -f`.
- `--apply` conserva **todas las contraseñas en conflicto**; no adivina cuál sigue siendo válida.

## Uso

Exporta un archivo CSV desde cada navegador. No hace falta exportar por sistema operativo si las cuentas del navegador están sincronizadas.

Linux:

```bash
python3 auditar_contrasenas_local.py --chrome chrome.csv --brave brave.csv --firefox firefox.csv --dry-run --detalle
python3 auditar_contrasenas_local.py --chrome chrome.csv --brave brave.csv --firefox firefox.csv --apply --output bitwarden_import.csv
```

Windows PowerShell:

```powershell
py .\auditar_contrasenas_local.py --chrome chrome.csv --brave brave.csv --firefox firefox.csv --dry-run --detalle
py .\auditar_contrasenas_local.py --chrome chrome.csv --brave brave.csv --firefox firefox.csv --apply --output bitwarden_import.csv
```

La opción `--dry-run` es redundante: **es el comportamiento predeterminado**. `--detalle` es opcional. Selecciona el formato **Bitwarden (csv)** al importar el fichero generado.

## Formatos de entrada

Chrome y Brave suelen exportar `name,url,username,password,note` (dependiendo de la versión pueden variar). Firefox puede exportar exactamente estas columnas:

```text
url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged
```

El script identifica las columnas por su nombre y acepta BOM UTF-8 y valores entrecomillados, incluidas comas o saltos de línea en notas y contraseñas. En Firefox conserva el `httpRealm` no vacío en las notas. Otros metadatos de Firefox (`guid`, `timeCreated`, etc.) **no tienen correspondencia directa en Bitwarden (csv)** y se descartan.

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
- Reutilización: contraseña idéntica utilizada en más de una cuenta, agrupadas por dominio + usuario.
- Fortaleza orientativa: longitud y patrones evidentes. **No es una estimación criptográfica ni una comprobación de filtraciones**.
- Riesgos: contraseñas vacías, usuarios vacíos, `http://`, URLs no reconocidas y credenciales incrustadas en URL.
- No fusiona automáticamente credenciales incompletas o ambiguas.

**Limitación de seguridad importante:** la herramienta no determina si una contraseña funciona y no consulta filtraciones ni servicios externos. La importación puede crear entradas duplicadas cuando cambian las rutas del mismo servicio, porque se prioriza no perder contraseñas.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```

Los tests utilizan únicamente **credenciales ficticias** y nunca dependen de exportaciones reales.

## Después de importar

Verifica las entradas y conflictos en Bitwarden, conserva un respaldo seguro mientras confirmas que todo funciona y elimina los archivos CSV en texto plano. Revisa también copias temporales, carpetas de descargas y sincronización.