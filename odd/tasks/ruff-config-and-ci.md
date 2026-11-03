# Ruff: configuración explícita, limpieza y CI

Objetivo: que `ruff` compruebe en local y en CI exactamente las mismas reglas, sin avisos, y que la CI impida que vuelvan a acumularse (DT3 de [reliability-hardening](reliability-hardening.md#deuda-técnica-registrada)).
Rama: `chore/ruff-clean-and-ci` desde `main`. Entrega: una rama, un commit por tarea; T4 (CI) en su propio commit por tocar la entrega. Pruebas: `python -m unittest discover -s tests`, `ruff check .`.

## Specs

- **S1 — Reglas explícitas y versión fija.** «Fija Ruff 0.17.3 y Python 3.12. Antes de definir `select`, identifica las reglas realmente activas y procura conservar inicialmente el mismo alcance que produce los 80 avisos actuales.» «No actives familias adicionales indiscriminadamente.» Aceptación: el conjunto de reglas activas con la nueva configuración es idéntico, regla a regla, al que activaba Ruff 0.17.3 por defecto; `requirements-dev.txt` fija `ruff==0.17.3`; `target-version = "py312"`.
- **S2 — Configuración compartida.** «La configuración debe compartirse entre el desarrollo local y CI.» Aceptación: un único archivo de configuración en el repositorio que usan tanto `ruff check .` en local como la CI.
- **S3 — Corregir los avisos.** «Corrige los avisos existentes, revisa los cambios automáticos y ejecuta todas las pruebas antes de integrar.» «Revisa especialmente B023 y las excepciones justificadas de FastAPI, como B008.» Aceptación: `ruff check .` sin avisos; cada cambio automático revisado en el diff; B023 analizado a mano; B008 de FastAPI resuelto con una excepción justificada y acotada; backend y E2E en verde.
- **S4 — CI.** Ruff se ejecuta en `.github/workflows/tests.yml` y falla el trabajo si hay avisos.
- **S5 — Documentación.** «Documenta cómo ampliar las reglas y actualizar Ruff de forma deliberada.»

## Tasks

- [x] T1 — S1, S2, S5: `ruff.toml` con `select` explícito y `py312`, versión fija y documentación. Ruta: inline. Commit `e96860d`.
- [x] T2 — S3: arreglos automáticos seguros, revisados. Ruta: inline. Commit: el de «apply Ruff's safe fixes».
- [ ] T3 — S3: avisos manuales (B023, F841, TRY004, PERF102, UP030, UP035, B008). Ruta: inline.
- [ ] T4 — S4: paso de Ruff en CI. Ruta: inline. Riesgo: apartado 5 (CI).

Ruta: todo inline; ningún disparador de escritor (cambios pequeños y dependientes entre sí sobre el mismo árbol).

## Log

- **L1 (2026-11-03):** petición, literal: «Sí» a «¿Empiezo [Ruff + CI] en una rama nueva?». Comprobación previa: no hay configuración de Ruff en el repositorio; Ruff 0.17.3 aplica por defecto 407 reglas de 34 familias (la mayoría solo en parte) con destino Python 3.11: 80 avisos (66 con arreglo automático); con `--target-version py312`, 82. `requirements-dev.txt` admite `ruff>=0.9,<1`, así que la CI podría aplicar otras reglas. Respuesta del usuario, literal: «Selecciona «Reglas explícitas». Fija Ruff 0.17.3 y Python 3.12. Antes de definir `select`, identifica las reglas realmente activas y procura conservar inicialmente el mismo alcance que produce los 80 avisos actuales. No actives familias adicionales indiscriminadamente. Revisa especialmente B023 y las excepciones justificadas de FastAPI, como B008. La configuración debe compartirse entre el desarrollo local y CI. Corrige los avisos existentes, revisa los cambios automáticos y ejecuta todas las pruebas antes de integrar. Documenta cómo ampliar las reglas y actualizar Ruff de forma deliberada.»
- **L2 (2026-11-03):** T1. `select` generado a partir de las 407 reglas que Ruff 0.17.3 activa por defecto (`ruff check --show-settings`), agrupadas por familia; comprobado que el conjunto activo con `ruff.toml` es idéntico regla a regla (diff vacío) y que el archivo de configuración resuelto es `ruff.toml`. Con `py312`: 82 avisos, los mismos que las reglas por defecto con `--target-version py312`. `ruff==0.17.3` en `backend/requirements-dev.txt`; README («Pruebas») explica cómo ampliar reglas y actualizar Ruff.
- **L3 (2026-11-03):** T2. Primer `ruff check --fix` descartado: con la longitud por defecto (88) isort partía en vertical imports que el código mantiene en una línea; el código usa líneas de hasta ~120 (31 líneas >100 en el backend). `line-length = 120` en `ruff.toml` (no cambia reglas: E501 no está seleccionada). Segundo `--fix` (solo arreglos seguros): 77 avisos corregidos en 19 archivos: anotaciones `X | None` y genéricos integrados (UP006/UP045/UP035/UP037), `str.format` a f-string (UP032), orden de imports (I001), `encode()` sin `'utf-8'` (UP012) y 13 `# noqa: E402` sin uso retirados (RUF100: E402 no está en el conjunto). Revisado el diff; una f-string nueva de 151 caracteres partida a mano; las dos de `csv_reader.py` ya superaban 120 antes y ahora son más cortas. Backend 138 OK. Quedan 9 avisos manuales (B008 ×2, UP047 ×2, TRY004 ×2, B023, PERF102, F841).
