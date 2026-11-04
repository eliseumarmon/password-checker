"""Browser password-export reader (Chrome, Brave, Firefox, Safari).

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
FORMATS = ("chromium", "firefox", "generic", "safari")
# Columns each format recognizes but deliberately discards (normalized keys).
# httpRealm is read only by firefox, so it is NOT ignored a priori elsewhere.
IGNORED_COLUMNS = {
    "firefox": ("formactionorigin", "guid", "timecreated", "timelastused", "timepasswordchanged"),
}


def column_key(value):
    return re.sub(r"[\s_-]+", "", value.strip().casefold())


def detect_format_and_origin(headers, file_name):
    """(format, origin): the format from the normalized headers only, with priority
    Safari > Firefox > Chromium > generic; the origin afterwards, without ever changing the format."""
    keys = {column_key(header) for header in headers}
    if "otpauth" in keys:
        return "safari", "safari"
    if "httprealm" in keys:
        return "firefox", "firefox"
    if keys & {*NAME_COLUMNS, *NOTE_COLUMNS}:
        return "chromium", origin_from_name(file_name)
    return "generic", "unknown"


def origin_from_name(file_name):
    """Chromium origin from the file name: only "brave" or "chrome" as a whole word counts,
    so "bravery" or "chromebook" are no evidence. When both appear, brave wins."""
    words = set(re.split(r"[\s._-]+", file_name.casefold()))
    if "brave" in words:
        return "brave"
    if "chrome" in words:
        return "chrome"
    return "unknown"


def malformed_csv(line):
    """Message for Python's csv.Error: it names the line, never the cell contents."""
    return (f"El CSV tiene un formato no válido en la línea {line}: revisa las comillas y los separadores, "
            "o si algún campo es demasiado largo.")


def checked_rows(reader):
    """Rows of *reader*, turning csv.Error into a readable ValueError."""
    while True:
        try:
            values = next(reader)
        except StopIteration:
            return
        except csv.Error:
            raise ValueError(malformed_csv(reader.line_num)) from None
        yield values


def read_columns(fmt):
    """Normalized keys *fmt* reads and imports (aliases plus format-specific ones)."""
    keys = {*URL_COLUMNS, *NAME_COLUMNS, *USERNAME_COLUMNS, *NOTE_COLUMNS, "password"}
    if fmt == "firefox":
        keys.add("httprealm")
    if fmt == "safari":
        keys.add("otpauth")
    return keys


def read_export(fmt, filename, origin):
    """Lee una exportacion, validando anchura sin perder columnas silenciosamente.

    Devuelve (credenciales, avisos): *fmt* decide las reglas de lectura; *origin*
    identifica la procedencia de las credenciales. Los avisos listan cada columna
    desconocida con datos (cabecera original y numero de filas), nunca sus valores.
    """
    if fmt not in FORMATS:
        raise ValueError(f"Formato de CSV no admitido: {fmt}")
    if hasattr(filename, "read"):
        file_context = nullcontext(filename)
    else:
        path = Path(filename)
        if not path.is_file():
            raise ValueError(f"No existe el archivo CSV: {path}")
        file_context = path.open("r", encoding="utf-8-sig", newline="")
    rows = []
    with file_context as file:
        reader = csv.reader(file, strict=True)
        lines = checked_rows(reader)
        try:
            headers = next(lines)
        except StopIteration:
            raise ValueError("El CSV está vacío")
        headers = [h.strip() for h in headers]
        keys = {}
        for index, header in enumerate(headers):
            if not header:
                raise ValueError("Cabecera vacía en el CSV")
            normalized = column_key(header)
            if normalized in keys:
                raise ValueError(f"Columnas repetidas en el CSV: {header}")
            keys[normalized] = index
        if "password" not in keys:
            separator = " ¿El CSV esta separado por punto y coma?" if len(headers) == 1 and ";" in headers[0] else ""
            raise ValueError(f"Falta columna 'password' en el CSV.{separator}")
        if not any(k in keys for k in URL_COLUMNS):
            raise ValueError("Falta columna de URL en el CSV")
        expected = len(headers)
        # Unknown columns (not read, not deliberately ignored by this format) are
        # reported per data row; recognized-but-ignored ones stay silent.
        known = read_columns(fmt) | set(IGNORED_COLUMNS.get(fmt, ()))
        unknown = [index for index, header in enumerate(headers) if column_key(header) not in known]
        unknown_counts = dict.fromkeys(unknown, 0)
        note_last = expected > 0 and column_key(headers[-1]) in NOTE_COLUMNS
        url_idx = next((keys[k] for k in URL_COLUMNS if k in keys), None)
        name_idx = next((keys[k] for k in NAME_COLUMNS if k in keys), None)

        def field(values, *aliases):
            for alias in aliases:
                if alias in keys:
                    return values[keys[alias]]
            return ""

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
                    raise ValueError(f"CSV: línea {line}: URI desplazada; la reconstruccion de nombre es ambigua. No se importara.")
            if len(values) > expected:
                if url_idx is not None and not supported_uri(values[url_idx]):
                    raise ValueError(f"CSV: línea {line}: URI fuera de su columna o invalida; se cancela para proteger la contrasena.")
                hint = (" Revisa comas sin comillas en notas; vuelve a exportar el archivo"
                        " y comprueba las columnas en privado."
                        if note_last and fmt == "chromium" else
                        " Comprueba la exportacion CSV original y su separador.")
                raise ValueError(f"CSV: línea {line}: {len(values)} columnas, esperadas {expected}.{hint}")
            elif len(values) < expected:
                # Ausencia del unico ultimo campo 'note' se interpreta como
                # nota vacia. No completar otras ausencias ambiguas.
                if len(values) == expected - 1 and note_last:
                    values.append("")
                else:
                    raise ValueError(f"CSV: línea {line}: {len(values)} columnas, esperadas {expected}."
                                     " No se importara parcialmente.")

            # Count after row validation/repairs and before skipping empty credentials:
            # a row that yields no credential still counts if the unknown column has data.
            for index in unknown:
                if values[index].strip():
                    unknown_counts[index] += 1

            name = field(values, *NAME_COLUMNS)
            url = field(values, *URL_COLUMNS).strip()
            username = field(values, *USERNAME_COLUMNS)
            password = field(values, "password")
            note = field(values, *NOTE_COLUMNS)
            totp = field(values, "otpauth") if fmt == "safari" else ""
            # A blank cell is no secret; any other value is kept exactly as exported.
            if not totp.strip():
                totp = ""
            # Firefox no exporta 'name' ni 'note', sino realm y metadatos.
            # El realm ayuda a reconocer cuentas HTTP Basic diferentes.
            if fmt == "firefox":
                realm = field(values, "httprealm")
                if realm:
                    note = (note + "\n\n" if note else "") + "Firefox HTTP realm: " + realm
            if not any((name, url, username, password, note, totp)):
                continue
            rows.append(Credential(origin, start_line, name, url, username, password, note, totp))
    warnings = [{"column": headers[index], "rows": count}
                for index, count in unknown_counts.items() if count]
    return rows, warnings


def read_upload(file_name, content):
    """Read an uploaded export from memory as (origin, credentials, warnings).

    No plaintext temp file; warnings list the unknown columns with data per file.
    """
    if b"\x00" in content:
        raise ValueError("Archivo con bytes nulos; se rechaza la importación")
    text = content.decode("utf-8-sig", errors="strict")
    header = next(checked_rows(csv.reader(io.StringIO(text))), [])
    fmt, origin = detect_format_and_origin(header, file_name)
    credentials, warnings = read_export(fmt, io.StringIO(text, newline=""), origin)
    return origin, credentials, warnings
