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

## Seguridad y limitaciones actuales

- Datos en memoria durante la ejecución; no se guardan sesiones cifradas todavía. Si se cierra el backend, se pierde el progreso.
- Las credenciales se envían exclusivamente entre el navegador y el backend **del mismo equipo**; no se requiere Internet ni se realiza seguimiento.
- El importador legado necesita un archivo temporal por CSV; el adaptador lo elimina al acabar o fallar. No utilices discos sincronizados para el entorno de trabajo.
- Las contraseñas están ocultas al abrir las fichas y no se incluyen en las listas generales.
- `Exportar Bitwarden` descarga un CSV en texto plano; elimina su copia cuando hayas verificado la migración.
- No hay comprobación de filtraciones de datos ni automatización de logins.

Ver [estado de implementación](docs/implementacion-v0.1.md), [guía visual](docs/guia-visual.md) y [flujo de usuario](docs/flujo-usuario.md).
