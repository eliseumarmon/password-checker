# Workspace en capas

Rama: `refactor/workspace-layers`, encadenada sobre `refactor/shared-display-name` (ambas tocan `workspace.py`).

## Specs

- S1. `application/` solo depende de `domain/`: ni `infrastructure/`, ni FastAPI, ni criptografía.
- S2. Una responsabilidad por módulo:
  - `application/workspace.py`: estado, historial y casos de uso (editar, papelera, fusionar, deshacer).
  - `application/review_state.py`: lo que ve la interfaz (resumen, grupos, auditoría).
  - `application/session_snapshot.py`: volcado y validación del estado de una sesión.
  - `infrastructure/csv_reader.py`: lectura de CSV subidos (bytes, origen, codificación).
  - `infrastructure/bitwarden.py`: bytes del CSV de exportación.
  - `infrastructure/sessions.py`: cifrado de sesiones.
- S3. `api.py` compone los adaptadores; el comportamiento HTTP no cambia.

## Tareas

- [x] T1. `sessions.py` pasa a `infrastructure/`.
- [x] T2. Lectura de CSV subidos y bytes de exportación en `infrastructure/`; `Workspace` recibe credenciales ya leídas y entrega las filas a exportar.
- [ ] T3. Test de arquitectura (RED) y división de `workspace.py` en los tres módulos de `application/`.

## Registro
