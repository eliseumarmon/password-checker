# Interfaz local de Password Checker (primera versión)

La CLI `auditar_contrasenas_local.py` sigue disponible sin cambios. Esta interfaz es un primer incremento de la arquitectura FastAPI + Vue 3 + TypeScript + PrimeVue.

## Instalar

Se necesita Python 3.12+, Node.js 22+ y npm. Desde la raíz del repositorio:

```bash
python -m venv .venv
# Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd frontend
npm install
npm run build
cd ..
python app.py
```

Abrir `http://127.0.0.1:8000` en el mismo ordenador. El proceso solo escucha en loopback. No uses `--host 0.0.0.0`: la interfaz maneja contraseñas.

Desarrollo: ejecutar `python app.py` y, en otra terminal, `cd frontend && npm run dev`; Vite crea un proxy de `/api` y muestra la interfaz en `http://127.0.0.1:5173`.

Pruebas del motor sin instalar la interfaz:

```bash
python -m unittest discover -s tests -v
```

## Reanudar entre sesiones

Durante la revisión, pulsa **Guardar sesión cifrada** e introduce una contraseña nueva de al menos 12 caracteres. Descarga y conserva el archivo `password-checker-session.pwc`. Para reanudar, abre Password Checker, pulsa **Abrir sesión cifrada anterior**, selecciona el archivo y escribe la misma contraseña. No hay recuperación si olvidas la clave. La sesión cifrada incluye también las credenciales y notas originales; protégela como un respaldo sensible.

**Importante:** el guardado es manual. Si cierras el backend antes de descargar el `.pwc`, perderás las modificaciones no guardadas. Al restaurar se reanuda la revisión, pero no el historial de deshacer.

## Seguridad y limitaciones actuales

- Datos en memoria durante la ejecución. **Guardar sesión cifrada** permite descargar un archivo `.pwc` protegido por contraseña (Argon2id + AES-256-GCM); **Abrir sesión cifrada** lo recupera. No existe guardado automático: guarda antes de cerrar. El historial de deshacer no se conserva al reabrir.
- Las credenciales se envían exclusivamente entre el navegador y el backend **del mismo equipo**; no se requiere Internet ni se realiza seguimiento.
- El lector CSV admite flujos en memoria y no escribe archivos temporales explícitos. En subidas HTTP de gran tamaño, el parser multipart del framework puede usar almacenamiento temporal. Evita discos o carpetas sincronizados para el entorno de trabajo.
- Las contraseñas están ocultas al abrir las fichas y no se incluyen en las listas generales.
- `Exportar Bitwarden` descarga un CSV en texto plano; elimina su copia cuando hayas verificado la migración.
- No hay comprobación de filtraciones de datos ni automatización de logins.

Ver [estado de implementación](docs/implementacion-v0.1.md), [guía visual](docs/guia-visual.md) y [flujo de usuario](docs/flujo-usuario.md).
