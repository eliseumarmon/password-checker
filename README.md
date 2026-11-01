# Password Checker

Herramienta local para revisar exportaciones CSV de Chrome, Brave y Firefox y preparar su importación en Bitwarden. La interfaz usa FastAPI y Vue, funciona en Windows y Linux y no requiere acceso a Internet durante la revisión.

## Uso

Instala y arranca la aplicación siguiendo la [guía de la interfaz](README-GUI.md). Importa las exportaciones CSV, revisa duplicados y conflictos, edita o excluye las credenciales necesarias y descarga el CSV para importar como **Bitwarden (csv)**. La fusión de duplicados se realiza solo cuando se solicita.

La revisión permanece en memoria. Para reanudarla más tarde, guarda manualmente una sesión cifrada `.pwc` y conserva su contraseña. El archivo incluye credenciales y notas; trátalo como un respaldo sensible.

## Seguridad

- Los CSV de entrada y salida contienen contraseñas en texto plano. No los compartas, subas al repositorio ni guardes en carpetas sincronizadas o copias inseguras.
- Las contraseñas se ocultan al abrir las fichas y no aparecen en las listas generales. Los datos se intercambian localmente entre el navegador y el servidor.
- La aplicación conserva las variantes conflictivas para revisión. No determina si una contraseña funciona ni consulta filtraciones.
- Después de importar, comprueba las entradas en Bitwarden, conserva un respaldo seguro mientras confirmas que todo funciona y elimina las copias CSV en texto plano.

## Formatos y criterios

Chrome y Brave suelen exportar `name,url,username,password,note`; Firefox puede exportar `url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged`. El lector identifica las columnas por nombre, admite BOM UTF-8 y campos entrecomillados con comas o saltos de línea. Conserva el `httpRealm` de Firefox en las notas y descarta sus metadatos sin correspondencia directa en Bitwarden.

Las URI Android `android://FIRMA@paquete/` se convierten a `androidapp://paquete`: se conserva el paquete y se descarta la firma. El lector puede reconstruir de forma restringida un nombre con una coma sin entrecomillar cuando desplaza la URI; las filas ambiguas se rechazan. Si aparece un error de número de columnas, comprueba la exportación original y vuelve a exportarla.

La revisión identifica duplicados, conflictos, reutilización, contraseñas débiles y campos incompletos. Para la reutilización, una cuenta se identifica por origen (esquema, host y puerto) o paquete Android y usuario. La fortaleza es orientativa y no constituye una estimación criptográfica.

## Arquitectura

El dominio en `backend/password_checker/domain/` contiene las reglas puras. `application/` gestiona el espacio de revisión y las sesiones; `infrastructure/` implementa lectura CSV, exportación Bitwarden y cifrado. `api.py` conecta la aplicación con la interfaz de `frontend/`. El mínimo de Python es 3.12.

## Pruebas

```bash
python -m pip install -r backend/requirements-dev.txt
python -m unittest discover -s tests -v
```

Las pruebas utilizan credenciales ficticias. Para las pruebas E2E de la interfaz:

```bash
cd frontend
npm ci
npx playwright install chromium   # solo la primera vez
npm run e2e
```

Playwright compila el frontend y arranca un backend propio en el puerto 5173 con el Python de `.venv` (otro intérprete: variable `E2E_PYTHON`). No ejecutes `npm run dev` al mismo tiempo porque usa el mismo puerto. Consulta las [limitaciones actuales](docs/implementacion-v0.1.md).
