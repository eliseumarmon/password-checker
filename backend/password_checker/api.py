"""Loopback-only HTTP adapter; no secrets in logs, storage or URLs."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .sessions import MAX_SESSION_BYTES, decrypt_session, encrypt_session
from .workspace import Workspace

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_TOTAL_SIZE = 20 * 1024 * 1024
MAX_FILES = 15

app = FastAPI(title='Password Checker', docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost'])
workspace = Workspace()


@app.middleware('http')
async def origin_guard(request: Request, call_next):
    # Cross-site browser requests cannot mutate or read the local workspace.
    if request.url.path.startswith('/api/'):
        origin = request.headers.get('origin')
        if origin:
            parsed = urlsplit(origin)
            if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost')
                    or parsed.port not in (8000, 5173)):
                return Response('Origen no autorizado', status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return Response('Origen no autorizado', status_code=403)
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
    return response


class EditRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = Field(default=None, max_length=1024)
    url: Optional[str] = Field(default=None, max_length=4096)
    username: Optional[str] = Field(default=None, max_length=1024)
    password: Optional[str] = Field(default=None, max_length=8192)
    note: Optional[str] = Field(default=None, max_length=100_000)
    included: Optional[bool] = None
    review: Optional[str] = None


@app.get('/api/workspace')
def get_workspace():
    return workspace.snapshot()


@app.post('/api/import')
async def import_files(files: list[UploadFile] = File(...)):
    if not 1 <= len(files) <= MAX_FILES:
        raise HTTPException(400, 'Selecciona entre 1 y 15 archivos')
    total = 0
    incoming = []
    for uploaded in files:
        if not (uploaded.filename or '').lower().endswith('.csv'):
            raise HTTPException(400, 'Solo se admiten archivos CSV')
        data = await uploaded.read(MAX_FILE_SIZE + 1)
        total += len(data)
        if len(data) > MAX_FILE_SIZE or total > MAX_TOTAL_SIZE:
            raise HTTPException(413, 'El archivo o el conjunto supera el límite de tamaño')
        incoming.append((Path(uploaded.filename or 'import.csv').name, data))
    try:
        return workspace.import_files(incoming)
    except (ValueError, UnicodeError, OSError) as error:
        raise HTTPException(422, str(error)) from None


@app.get('/api/records/{record_id}')
def get_record(record_id: str):
    try:
        return workspace.get(record_id)
    except KeyError:
        raise HTTPException(404, 'Credencial no encontrada') from None


@app.patch('/api/records/{record_id}')
def edit_record(record_id: str, edit: EditRecord):
    changes = edit.model_dump(exclude_unset=True)
    if any(value is None for value in changes.values()):
        raise HTTPException(422, 'No se permiten valores nulos')
    try:
        return workspace.change(record_id, changes)
    except KeyError:
        raise HTTPException(404, 'Credencial no encontrada') from None
    except ValueError as error:
        raise HTTPException(422, str(error)) from None


@app.post('/api/merge-exact')
def merge_exact():
    return workspace.merge_exact()


@app.post('/api/undo')
def undo():
    try:
        return workspace.undo()
    except ValueError as error:
        raise HTTPException(409, str(error)) from None


class SessionPassphrase(BaseModel):
    passphrase: str = Field(min_length=12, max_length=1024)


@app.post('/api/session/save')
def save_session(credentials: SessionPassphrase):
    try:
        content = encrypt_session(workspace.serialize(), credentials.passphrase)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    return Response(content, media_type='application/octet-stream', headers={
        'Content-Disposition': 'attachment; filename="password-checker-session.pwc"',
    })


@app.post('/api/session/load')
async def load_session(file: UploadFile = File(...), passphrase: str = Form(...)):
    if not (file.filename or '').endswith('.pwc'):
        raise HTTPException(400, 'Selecciona un archivo de sesión .pwc')
    content = await file.read(MAX_SESSION_BYTES + 1)
    try:
        return workspace.restore(decrypt_session(content, passphrase))
    except ValueError as error:
        raise HTTPException(422, str(error)) from None


@app.get('/api/export')
def export_csv():
    try:
        content, count = workspace.export_csv()
    except ValueError as error:
        raise HTTPException(409, str(error)) from None
    return Response(content, media_type='text/csv; charset=utf-8', headers={
        'Content-Disposition': 'attachment; filename="bitwarden_import.csv"',
        'X-Credential-Count': str(count),
    })


# Built Vue app; no remote assets. Dev server uses Vite proxy instead.
DIST = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
if DIST.is_dir():
    app.mount('/assets', StaticFiles(directory=DIST / 'assets'), name='assets')


@app.get('/{path:path}', include_in_schema=False)
def frontend(path: str):
    if path.startswith('api/'):
        raise HTTPException(404)
    if DIST.is_dir() and (DIST / 'index.html').is_file():
        return HTMLResponse((DIST / 'index.html').read_text(encoding='utf-8'), headers={
            'Cache-Control': 'no-store',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; connect-src 'self'; form-action 'none'; base-uri 'self'; frame-ancestors 'none'",
            'Referrer-Policy': 'no-referrer',
        })
    return HTMLResponse('<h1>Password Checker</h1><p>Compila el frontend: cd frontend &amp;&amp; npm ci &amp;&amp; npm run build</p>')
