# Regla única de copia exacta

Rama: `refactor/shared-duplicate-rule` (desde `main`).

## Specs

- S1. La interfaz (grupos «Copia exacta» y «Fusionar copias exactas») usa la regla del dominio `duplicate_key`: misma URL normalizada, mismo usuario exacto y misma contraseña, todo no vacío.
- S2. Un grupo solo es «Copia exacta» si «Fusionar copias exactas» puede fusionarlo.

## Tareas

- [x] T1. Test que falla: dos registros sin usuario con misma URL y contraseña no se marcan como copia exacta.
- [x] T2. `workspace.py` deriva la identidad del registro y delega en `duplicate_key`; se elimina la regla duplicada.

## Registro

- L1. Antes del cambio, dos registros sin usuario salían como «Copia exacta» pero la fusión no los tocaba.
