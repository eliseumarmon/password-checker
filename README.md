# Password Checker

Herramienta local para revisar exportaciones CSV de Chrome, Brave y Firefox y preparar su importación en Bitwarden. La interfaz usa FastAPI y Vue, funciona en Windows y Linux y no requiere acceso a Internet durante la revisión.

## Instalación y ejecución

Se necesita Python 3.12+, Node.js 22+ y npm. Desde la raíz del repositorio:

```bash
python -m venv .venv
# Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cd frontend
npm install
npm run build
cd ..
python app.py
```

Abre `http://127.0.0.1:8000` en el mismo ordenador. El servidor escucha en loopback; no lo expongas en `0.0.0.0`, ya que maneja contraseñas.

Para desarrollo, ejecuta `python app.py` y, en otra terminal, `cd frontend && npm run dev`. Vite crea un proxy de `/api` y muestra la interfaz en `http://127.0.0.1:5173`.

## Uso y sesiones

Importa las exportaciones CSV, revisa duplicados y conflictos, edita o excluye las credenciales necesarias y descarga el CSV para importar como **Bitwarden (csv)**. La fusión de duplicados se realiza solo cuando se solicita.

La revisión permanece en memoria y el guardado es manual. Para continuar otro día, pulsa **Guardar sesión cifrada** e introduce una contraseña nueva de al menos 12 caracteres; descarga y conserva `password-checker-session.pwc`. Para reanudar, pulsa **Abrir sesión cifrada anterior**, selecciona el archivo y escribe la misma contraseña. El archivo utiliza Argon2id y AES-256-GCM y contiene las credenciales y notas originales: protégelo como un respaldo sensible. No hay recuperación si olvidas la contraseña. Las modificaciones sin guardar se pierden al cerrar el backend y el historial de deshacer no se conserva al reabrir.

## Seguridad y limitaciones

- Los CSV de entrada y salida contienen contraseñas en texto plano. No los compartas, subas al repositorio ni guardes en carpetas sincronizadas o copias inseguras.
- Las contraseñas se ocultan al abrir las fichas y no aparecen en las listas generales. Los datos se intercambian entre el navegador y el servidor del mismo equipo; no se requiere Internet durante la revisión ni se realiza seguimiento. La API valida el origen y el host de las peticiones y envía cabeceras `no-store`. Lo único que se guarda en el navegador es la preferencia de menú contraído (`localStorage`), sin credenciales.
- El lector CSV procesa los datos en memoria sin escribir archivos temporales explícitos. Durante subidas HTTP grandes, el parser multipart del framework puede utilizar almacenamiento temporal; evita discos y carpetas sincronizados para el entorno de trabajo.
- La aplicación conserva las variantes conflictivas para revisión. No determina si una contraseña funciona, no automatiza inicios de sesión ni consulta filtraciones.
- Después de importar, comprueba las entradas en Bitwarden, conserva un respaldo seguro mientras confirmas que todo funciona y elimina las copias CSV en texto plano.

Consulta el [flujo de usuario](docs/flujo-usuario.md) para el funcionamiento detallado, el [trabajo pendiente](docs/pendiente.md) para las limitaciones y las ideas sin implementar, y la [guía visual](docs/guia-visual.md) para los criterios de diseño.

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

Playwright compila el frontend y arranca un backend propio en el puerto 5173 con el Python de `.venv` (otro intérprete: variable `E2E_PYTHON`). No ejecutes `npm run dev` al mismo tiempo porque usa el mismo puerto. GitHub Actions ejecuta estas mismas pruebas en el job `e2e` con `E2E_PYTHON=python`; si fallan, sube las trazas de Playwright como artefacto `playwright-traces`. Para revisarlas en local: `npx playwright show-trace <traza>.zip`.
