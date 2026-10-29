"""Browser password-export reader (Chrome, Brave, Firefox).

Validates column widths without losing columns silently. Accepts a path
or an already-open text stream, so callers never need a plaintext temp file.
"""
from __future__ import annotations

import csv
import re
from contextlib import nullcontext
from pathlib import Path

from ..domain.credential import Credential
from ..domain.urls import supported_uri

URL_COLUMNS = ("url", "origin", "website", "hostname", "loginuri")
NAME_COLUMNS = ("name", "title")


def column_key(value):
    return re.sub(r"[\s_-]+", "", value.strip().casefold())


def read_export(source, filename, repair_extra_notes=False, diagnostics=None):
    """Lee una exportacion, validando anchura sin perder columnas silenciosamente.

    Solo repara comas no escapadas de una columna *note* final con permiso
    explicito. CSV con comillas bien formadas se lee de forma nativa.
    """
    if hasattr(filename, "read"):
        file_context = nullcontext(filename)
    else:
        path = Path(filename)
        if not path.is_file():
            raise ValueError("No existe el archivo de {}: {}".format(source, path))
        file_context = path.open("r", encoding="utf-8-sig", newline="")
    rows = []
    with file_context as file:
        reader = csv.reader(file, strict=True)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError("El CSV de {} esta vacio".format(source))
        headers = [h.strip() for h in headers]
        keys = {}
        for index, header in enumerate(headers):
            if not header:
                raise ValueError("Cabecera vacia en {}".format(source))
            normalized = column_key(header)
            if normalized in keys:
                raise ValueError("Columnas repetidas en {}: {}".format(source, header))
            keys[normalized] = index
        if "password" not in keys:
            separator = " ¿El CSV esta separado por punto y coma?" if len(headers) == 1 and ";" in headers[0] else ""
            raise ValueError("Falta columna 'password' en {}.{}".format(source, separator))
        if not any(k in keys for k in URL_COLUMNS):
            raise ValueError("Falta columna de URL en {}".format(source))
        expected = len(headers)
        # En CSV del navegador, una nota sin comillas puede contener comas.
        # No sabemos si la coma estaba en la contrasena, por eso opt-in.
        note_last = expected > 0 and column_key(headers[-1]) in ("note", "notes")
        url_idx = next((keys[k] for k in URL_COLUMNS if k in keys), None)
        name_idx = next((keys[k] for k in NAME_COLUMNS if k in keys), None)
        # Algunos exportadores omiten los ultimos campos vacios; SOLO el
        # campo final de nota se puede rellenar sin desplazar columnas.
        for values in reader:
            line = reader.line_num
            start_line = reader.line_num - sum(value.count("\n") for value in values)
            if not values or (len(values) == 1 and not values[0].strip()):
                continue

            # If a title contains an unquoted comma, the URI can shift into
            # the username column, even with the expected number of fields
            # when the final empty note is missing. Only repair this narrowly
            # when the next column is a recognizable, complete URI.
            if (source in ("chrome", "brave") and name_idx is not None and
                    url_idx == name_idx + 1 and len(values) > url_idx + 1 and
                    not supported_uri(values[url_idx]) and supported_uri(values[url_idx + 1])):
                if len(values) in (expected, expected + 1) and note_last:
                    values = (values[:name_idx] +
                              [values[name_idx] + "," + values[url_idx]] +
                              values[url_idx + 1:])
                    if len(values) == expected - 1:
                        values.append("")
                    if diagnostics is not None:
                        diagnostics.append((source, line, "nombre reconstruido; revisar la fila original"))
                else:
                    raise ValueError("{}: linea {}: URI desplazada; la reconstruccion de nombre es ambigua. No se importara.".format(source, line))
            if len(values) > expected:
                if url_idx is not None and not supported_uri(values[url_idx]):
                    raise ValueError("{}: linea {}: URI fuera de su columna o invalida; se cancela para proteger la contrasena.".format(source, line))
                if not (repair_extra_notes and note_last and source in ("chrome", "brave")):
                    hint = (" Revisa comas sin comillas en notas; prueba --repair-extra-notes"
                            " solo si confirmas que las comas pertenecen a notas."
                            if note_last and source in ("chrome", "brave") else
                            " Comprueba la exportacion CSV original y su separador.")
                    raise ValueError("{}: linea {}: {} columnas, esperadas {}.{}".format(
                        source, line, len(values), expected, hint))
                values = values[:expected - 1] + [",".join(values[expected - 1:])]
                if diagnostics is not None:
                    diagnostics.append((source, line, "nota reconstruida desde columnas extra"))
            elif len(values) < expected:
                # Ausencia del unico ultimo campo 'note' se interpreta como
                # nota vacia. No completar otras ausencias ambiguas.
                if len(values) == expected - 1 and note_last:
                    values.append("")
                    if diagnostics is not None:
                        diagnostics.append((source, line, "nota final vacia completada"))
                else:
                    raise ValueError("{}: linea {}: {} columnas, esperadas {}."
                                     " No se importara parcialmente.".format(source, line, len(values), expected))

            def field(*aliases):
                for alias in aliases:
                    if alias in keys:
                        return values[keys[alias]]
                return ""

            name = field(*NAME_COLUMNS)
            url = field(*URL_COLUMNS).strip()
            username = field("username", "user", "login", "loginusername")
            password = field("password")
            note = field("note", "notes")
            # Firefox no exporta 'name' ni 'note', sino realm y metadatos.
            # El realm ayuda a reconocer cuentas HTTP Basic diferentes.
            if source == "firefox":
                realm = field("httprealm")
                if realm:
                    note = (note + "\n\n" if note else "") + "Firefox HTTP realm: " + realm
            if not any((name, url, username, password, note)):
                continue
            rows.append(Credential(source, start_line, name, url, username, password, note))
    return rows
