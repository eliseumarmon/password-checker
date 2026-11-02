"""Browser password-export reader (Chrome, Brave, Firefox).

Validates column widths without losing columns silently. Accepts a path
or an already-open text stream, so callers never need a plaintext temp file.
"""
from __future__ import annotations

import csv
import io
import re
from contextlib import nullcontext
from pathlib import Path

from ..domain.credential import Credential
from ..domain.urls import supported_uri

URL_COLUMNS = ("url", "origin", "website", "hostname", "loginuri")
NAME_COLUMNS = ("name", "title")
USERNAME_COLUMNS = ("username", "user", "login", "loginusername")
NOTE_COLUMNS = ("note", "notes")
# How a CSV is read. The origin (domain ORIGINS) only says where it came from.
FORMATS = ("chromium", "firefox", "generic")


def column_key(value):
    return re.sub(r"[\s_-]+", "", value.strip().casefold())


def detect_format_and_origin(headers, file_name):
    """(format, origin): the format from the normalized headers only, with priority
    Firefox > Chromium > generic; the origin afterwards, without ever changing the format."""
    keys = {column_key(header) for header in headers}
    if "httprealm" in keys:
        return "firefox", "firefox"
    if keys & {*NAME_COLUMNS, *NOTE_COLUMNS}:
        name = file_name.casefold()
        return "chromium", "brave" if "brave" in name else "chrome" if "chrome" in name else "unknown"
    return "generic", "unknown"


def malformed_csv(line, source=None):
    """Message for Python's csv.Error: it names the line, never the cell contents."""
    where = f"El CSV de {source}" if source else "El CSV"
    return (f"{where} tiene un formato no válido en la línea {line}: revisa las comillas y los separadores, "
            "o si algún campo es demasiado largo.")


def checked_rows(reader, source):
    """Rows of *reader*, turning csv.Error into a readable ValueError."""
    while True:
        try:
            values = next(reader)
        except StopIteration:
            return
        except csv.Error:
            raise ValueError(malformed_csv(reader.line_num, source)) from None
        yield values


def read_export(fmt, filename, source):
    """Lee una exportacion, validando anchura sin perder columnas silenciosamente.

    *fmt* decide las reglas de lectura; *source* es el origen, solo para mensajes y credenciales.
    """
    if fmt not in FORMATS:
        raise ValueError(f"Formato de CSV no admitido: {fmt}")
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
        lines = checked_rows(reader, source)
        try:
            headers = next(lines)
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
        note_last = expected > 0 and column_key(headers[-1]) in NOTE_COLUMNS
        url_idx = next((keys[k] for k in URL_COLUMNS if k in keys), None)
        name_idx = next((keys[k] for k in NAME_COLUMNS if k in keys), None)
        # Algunos exportadores omiten los ultimos campos vacios; SOLO el
        # campo final de nota se puede rellenar sin desplazar columnas.
        for values in lines:
            line = reader.line_num
            start_line = reader.line_num - sum(value.count("\n") for value in values)
            if not values or (len(values) == 1 and not values[0].strip()):
                continue

            # If a title contains an unquoted comma, the URI can shift into
            # the username column, even with the expected number of fields
            # when the final empty note is missing. Only repair this narrowly
            # when the next column is a recognizable, complete URI.
            if (fmt == "chromium" and name_idx is not None and
                    url_idx == name_idx + 1 and len(values) > url_idx + 1 and
                    not supported_uri(values[url_idx]) and supported_uri(values[url_idx + 1])):
                if len(values) in (expected, expected + 1) and note_last:
                    values = (values[:name_idx] +
                              [values[name_idx] + "," + values[url_idx]] +
                              values[url_idx + 1:])
                    if len(values) == expected - 1:
                        values.append("")
                else:
                    raise ValueError("{}: linea {}: URI desplazada; la reconstruccion de nombre es ambigua. No se importara.".format(source, line))
            if len(values) > expected:
                if url_idx is not None and not supported_uri(values[url_idx]):
                    raise ValueError("{}: linea {}: URI fuera de su columna o invalida; se cancela para proteger la contrasena.".format(source, line))
                hint = (" Revisa comas sin comillas en notas; vuelve a exportar el archivo"
                        " y comprueba las columnas en privado."
                        if note_last and fmt == "chromium" else
                        " Comprueba la exportacion CSV original y su separador.")
                raise ValueError("{}: linea {}: {} columnas, esperadas {}.{}".format(
                    source, line, len(values), expected, hint))
            elif len(values) < expected:
                # Ausencia del unico ultimo campo 'note' se interpreta como
                # nota vacia. No completar otras ausencias ambiguas.
                if len(values) == expected - 1 and note_last:
                    values.append("")
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
            username = field(*USERNAME_COLUMNS)
            password = field("password")
            note = field(*NOTE_COLUMNS)
            # Firefox no exporta 'name' ni 'note', sino realm y metadatos.
            # El realm ayuda a reconocer cuentas HTTP Basic diferentes.
            if fmt == "firefox":
                realm = field("httprealm")
                if realm:
                    note = (note + "\n\n" if note else "") + "Firefox HTTP realm: " + realm
            if not any((name, url, username, password, note)):
                continue
            rows.append(Credential(source, start_line, name, url, username, password, note))
    return rows


def read_upload(file_name, content):
    """Read an uploaded export from memory as (origin, credentials): no plaintext temp file."""
    if b"\x00" in content:
        raise ValueError("Archivo con bytes nulos; se rechaza la importación")
    text = content.decode("utf-8-sig", errors="strict")
    try:
        header = next(csv.reader(io.StringIO(text)), [])
    except csv.Error:
        raise ValueError(malformed_csv(1)) from None
    fmt, source = detect_format_and_origin(header, file_name)
    return source, read_export(fmt, io.StringIO(text, newline=""), source)
