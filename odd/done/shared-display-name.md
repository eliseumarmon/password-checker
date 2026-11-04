# Nombre visible único

Rama: `refactor/shared-display-name` (desde `main`).

## Specs

- S1. Un nombre vacío o de solo espacios se sustituye por el paquete Android, el dominio o «Acceso sin nombre», igual en la interfaz y en la CLI.
- S2. La regla vive en el dominio (`display_name`) y la usan `workspace.py` y `merge_group`.

## Tareas

- [x] T1. Test que falla: importar en la interfaz un registro con nombre de solo espacios da el dominio como nombre.
- [x] T2. `display_name` en el dominio; `Candidate.from_source` y `merge_group` la usan.

## Registro

- L1. Había tres copias: `workspace.py`, `consolidation.py` y `review_report.py` («Sin nombre»); la del informe no se alcanzaba porque recibe filas consolidadas.
