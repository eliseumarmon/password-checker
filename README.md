# Password Checker

Herramienta local para revisar exportaciones CSV de Chrome, Brave y Firefox (o CSV genéricos con columna de URL y contraseña) y preparar su importación en Bitwarden. La interfaz usa FastAPI y Vue, funciona en Windows y Linux y no requiere acceso a Internet durante la revisión.

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

La interfaz necesita un navegador actual: solo usa características web [Baseline Widely Available](https://web.dev/baseline) (por ejemplo, el selector CSS `:has()`) y no incluye alternativas para navegadores que no las admitan.

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

El lector separa el **formato** (cómo se lee el CSV) del **origen** (de dónde procede). El formato se decide solo por las cabeceras normalizadas, nunca por el nombre del archivo, con prioridad Firefox (cabeceras distintivas como `httpRealm`) > Chromium (columna de nombre o de nota) > genérico. Solo se exigen una columna `password` y una columna de URL reconocida; el usuario puede faltar. El origen es solo una etiqueta de procedencia que no condiciona la lectura: formato Firefox → `firefox`; formato Chromium → `brave` o `chrome` únicamente cuando «brave» o «chrome» aparecen como palabras independientes en el nombre del archivo (separadas por espacios, guiones, guiones bajos o puntos, sin distinguir mayúsculas; si aparecen ambas, gana `brave`), y `unknown` en cualquier otro caso; formato genérico → `unknown`, que en la interfaz se muestra como «Desconocido». Renombrar un archivo no cambia las credenciales importadas, solo el origen inferido.

Chrome y Brave suelen exportar `name,url,username,password,note`; Firefox puede exportar `url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged`. El lector identifica las columnas por nombre, admite BOM UTF-8 y campos entrecomillados con comas o saltos de línea. Conserva el `httpRealm` de Firefox en las notas y descarta sin aviso sus metadatos sin correspondencia directa en Bitwarden. Toda columna desconocida con datos se descarta y genera un aviso por archivo, columna y número de filas con datos, sin mostrar sus valores; si falta `password` o la columna de URL, o el CSV es inválido, la importación se rechaza entera (todo o nada). El comportamiento detallado de la importación y de los avisos está en el [flujo de usuario](docs/flujo-usuario.md).

Las URI Android `android://FIRMA@paquete/` se convierten a `androidapp://paquete`: se conserva el paquete y se descarta la firma. El lector puede reconstruir de forma restringida un nombre con una coma sin entrecomillar cuando desplaza la URI; las filas ambiguas se rechazan. Si aparece un error de número de columnas, comprueba la exportación original y vuelve a exportarla.

La revisión identifica duplicados, conflictos, reutilización, contraseñas débiles y campos incompletos. Para la reutilización, una cuenta se identifica por origen web (esquema, host y puerto) o paquete Android y usuario; el origen de importación del navegador no interviene. La fortaleza es orientativa y no constituye una estimación criptográfica.

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
