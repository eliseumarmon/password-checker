#!/usr/bin/env python3
"""Audita y unifica CSV de Chrome, Brave y Firefox para importar en Bitwarden.

Python 3.9+; solo biblioteca estandar; no accede a Internet.
Por defecto SOLO simula e informa. --apply --output RUTA crea un unico CSV
SIN sobrescribir archivos existentes. Conserva las contrasenas en conflicto
como registros separados para que puedas decidir cual es valida.

IMPORTANTE: Tanto los CSV originales como el CSV resultante contienen
contrasenas en texto plano. No los subas a repositorios, chats ni nubes.
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

BITWARDEN_FIELDS = (
    "folder", "favorite", "type", "name", "notes", "fields", "reprompt",
    "login_uri", "login_username", "login_password", "login_totp",
)
COMMON = {
    "123456", "12345678", "123456789", "1234567890", "123456789123",
    "password", "password1", "password123", "qwerty", "qwerty123",
    "admin", "admin123", "letmein", "welcome", "welcome1", "abc123",
    "111111", "000000", "iloveyou", "contrasena", "contraseña", "1234",
    "12345", "dragon", "monkey", "123123", "qwertyuiop",
}


@dataclass(frozen=True)
class Credential:
    source: str
    line: int
    name: str
    url: str
    username: str
    password: str
    note: str


def column_key(value):
    return re.sub(r"[\s_-]+", "", value.strip().casefold())


def read_export(source, filename, repair_extra_notes=False, diagnostics=None):
    """Lee una exportacion, validando anchura sin perder columnas silenciosamente.

    Solo repara comas no escapadas de una columna *note* final con permiso
    explicito. CSV con comillas bien formadas se lee de forma nativa.
    """
    path = Path(filename)
    if not path.is_file():
        raise ValueError("No existe el archivo de {}: {}".format(source, path))
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
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
        if not any(k in keys for k in ("url", "origin", "website", "hostname", "loginuri")):
            raise ValueError("Falta columna de URL en {}".format(source))
        expected = len(headers)
        # En CSV del navegador, una nota sin comillas puede contener comas.
        # No sabemos si la coma estaba en la contrasena, por eso opt-in.
        note_last = expected > 0 and column_key(headers[-1]) in ("note", "notes")
        # Algunos exportadores omiten los ultimos campos vacios; SOLO el
        # campo final de nota se puede rellenar sin desplazar columnas.
        for values in reader:
            start_line = reader.line_num - ("\n".join(values).count("\n"))
            line = reader.line_num
            if not values or (len(values) == 1 and not values[0].strip()):
                continue
            if len(values) > expected:
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

            name = field("name", "title")
            url = field("url", "origin", "website", "hostname", "loginuri").strip()
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


def url_parts(raw):
    """(clave exacta prudente, host, http_inseguro, invalida, tiene_usuario_en_url)."""
    url = raw.strip()
    if not url:
        return "", "", False, True, False
    try:
        # No aceptar esquemas inventados ni resolver URLs con peticiones externas.
        parsed = urlsplit(url if "://" in url else "https://" + url)
        scheme = parsed.scheme.casefold()
        host = (parsed.hostname or "").casefold()
        port = parsed.port  # Valida puertos malformados.
        if scheme not in ("http", "https") or not host:
            return url, "", False, True, bool(parsed.username or parsed.password)
        # Mantener subdominios, rutas, parametros, fragmentos, puertos y esquemas.
        # Solo normalizamos mayusculas y el / vacio en la raiz.
        default_port = 80 if scheme == "http" else 443
        network = host if port in (None, default_port) else "{}:{}".format(host, port)
        # Compatibilidad con IPv6 al reconstruir la autoridad.
        if ":" in host:
            network = "[{}]".format(host)
            if port not in (None, default_port):
                network += ":{}".format(port)
        path = parsed.path or "/"
        canonical = (scheme, network, path, parsed.query, parsed.fragment)
        return canonical, host, scheme == "http", False, bool(parsed.username or parsed.password)
    except ValueError:
        return url, "", False, True, False


def account_key(rec):
    key, _, _, invalid, embedded_auth = url_parts(rec.url)
    if not rec.url or not rec.username or invalid or embedded_auth:
        return None  # No fusionar cuentas ambiguas o sin usuario.
    return key, rec.username  # No cambiar mayusculas de usuarios potencialmente sensibles.


def duplicate_key(rec):
    account = account_key(rec)
    return (account, rec.password) if account and rec.password else None


def masked_username(username):
    if not username:
        return "(sin usuario)"
    if "@" in username:
        local, domain = username.rsplit("@", 1)
        return (local[:2] + "***@" + domain) if local else "***@" + domain
    return username[:2] + "***" if len(username) > 2 else "**"


def label(rec):
    _, host, _, invalid, _ = url_parts(rec.url)
    site = host if host else ("(URL no reconocida)" if invalid else "(sin URL)")
    return "{} / {}".format(site, masked_username(rec.username))


def simple_weak(password):
    lower = password.casefold()
    return (lower in COMMON or
            bool(re.fullmatch(r"(.)\1{5,}", password)) or
            bool(re.fullmatch(r"(12345|123456|qwerty|asdf|abcd)[a-z0-9]*", lower)))


def merge_group(records):
    """Preserva notas distintas sin exponerlas en los informes."""
    first = records[0]
    chosen = next((r.name for r in records if r.name.strip()), "")
    if not chosen:
        _, host, _, _, _ = url_parts(first.url)
        chosen = host or "Acceso sin nombre"
    notes = list(dict.fromkeys(r.note for r in records if r.note.strip()))
    if len(notes) > 1:
        merged_note = "\n\n----- Nota adicional -----\n\n".join(notes)
    else:
        merged_note = notes[0] if notes else ""
    return Credential(first.source, first.line, chosen, first.url,
                      first.username, first.password, merged_note)


def process(rows):
    """Devuelve las credenciales unificadas y metricas; sin tocar el disco."""
    groups = {}
    unique = []
    for row in rows:
        key = duplicate_key(row)
        if key is None:
            unique.append([row])
        elif key in groups:
            groups[key].append(row)
        else:
            group = [row]
            groups[key] = group
            unique.append(group)
    output_rows = [merge_group(group) for group in unique]
    notes_merged = sum(len(set(r.note for r in g if r.note.strip())) > 1 for g in unique)
    accounts = defaultdict(list)
    for row in output_rows:
        key = account_key(row)
        if key is not None:
            accounts[key].append(row)
    conflicts = [group for group in accounts.values()
                 if len({r.password for r in group}) > 1]

    # Posibles registros relacionados en rutas diferentes del mismo dominio:
    # solo avisar, nunca fusionar por el dominio ni sobreescribir contrasenas.
    by_host_user = defaultdict(list)
    for row in output_rows:
        _, host, _, invalid, _ = url_parts(row.url)
        if host and not invalid and row.username:
            by_host_user[(host, row.username)].append(row)
    possible_related = [g for g in by_host_user.values()
                        if len({account_key(r) for r in g}) > 1]

    by_password = defaultdict(set)
    for row in output_rows:
        if row.password:
            _, host, _, invalid, _ = url_parts(row.url)
            if host and not invalid and row.username:
                by_password[row.password].add((host, row.username))
    reused = [group for group in by_password.values() if len(group) > 1]
    distinct_passwords = set(r.password for r in output_rows if r.password)
    stats = {
        "originals": len(rows),
        "by_source": Counter(row.source for row in rows),
        "final": len(output_rows),
        "duplicates": len(rows) - len(output_rows),
        "notes_merged": notes_merged,
        "conflicts": conflicts,
        "possible_related": possible_related,
        "reused_groups": len(reused),
        "reused_accounts": len(set().union(*reused)) if reused else 0,
        "short": sum(len(password) < 12 for password in distinct_passwords),
        "moderate": sum(12 <= len(password) < 14 for password in distinct_passwords),
        "obvious": sum(simple_weak(password) for password in distinct_passwords),
        "empty_password": sum(not r.password for r in output_rows),
        "empty_username": sum(not r.username for r in output_rows),
        "empty_url": sum(not r.url for r in output_rows),
        "http": sum(url_parts(r.url)[2] for r in output_rows),
        "invalid_url": sum(url_parts(r.url)[3] for r in output_rows if r.url),
        "url_credentials": sum(url_parts(r.url)[4] for r in output_rows),
        "undedupeable": sum(duplicate_key(r) is None for r in rows),
    }
    return output_rows, stats


def report(stats, details, dry_run, diagnostics=()):
    print("AUDITORIA LOCAL / {}".format("DRY RUN - SIN ESCRITURA" if dry_run else "EXPORTACION"))
    print("=" * 49)
    print("Filas de entrada:              {}".format(stats["originals"]))
    print("Filas CSV reconstruidas/completadas: {}".format(len(diagnostics)))
    for browser, count in sorted(stats["by_source"].items()):
        print("  {:<10} {:>8}".format(browser + ":", count))
    print("Credenciales repetidas fusionadas (URL + usuario + clave): {}".format(stats["duplicates"]))
    print("Registros finales previstos:   {}".format(stats["final"]))
    print("Grupos con notas combinadas:   {}".format(stats["notes_merged"]))
    print("Conflictos (misma URL + usuario; distinta clave): {}".format(len(stats["conflicts"])))
    print("Posibles relacionados (mismo dominio + usuario; otra URL): {}".format(len(stats["possible_related"])))
    print("Contrasenas reutilizadas entre cuentas (grupos): {}".format(stats["reused_groups"]))
    print("Cuentas afectadas por reutilizacion: {}".format(stats["reused_accounts"]))
    print("Contrasenas distintas con menos de 12 caracteres: {}".format(stats["short"]))
    print("Contrasenas distintas de 12-13 caracteres: {}".format(stats["moderate"]))
    print("Contrasenas distintas de patron obvio: {}".format(stats["obvious"]))
    print("Registros con contrasena vacia: {}".format(stats["empty_password"]))
    print("Registros sin usuario: {}".format(stats["empty_username"]))
    print("Registros sin URL: {}".format(stats["empty_url"]))
    print("Registros con URL http: {}".format(stats["http"]))
    print("Registros con URL no reconocida: {}".format(stats["invalid_url"]))
    print("Registros con usuario/clave incrustados en URL: {}".format(stats["url_credentials"]))
    print("Filas sin deduplicacion segura: {}".format(stats["undedupeable"]))
    print("\nLos conflictos NO se descartan: ambas claves se conservan para revision.")
    print("Las notas diferentes se conservan. No se fusionan URLs distintas por dominio.")
    print("La fortaleza es orientativa: no se consultan filtraciones ni se verifica vigencia.")
    print("Ninguna contrasena se muestra en pantalla ni se envia a Internet.")
    if details:
        print("\n--- CONFLICTOS: revisar cual es la clave valida ---")
        for group in stats["conflicts"]:
            print("  {} ({} variantes)".format(label(group[0]), len(group)))
        print("\n--- POSIBLES RELACIONADOS: mismo dominio, URLs diferentes ---")
        for group in stats["possible_related"]:
            print("  {} ({} registros)".format(label(group[0]), len(group)))
        print("\nNo compartas esta salida: contiene dominios y usuarios parcialmente ocultos.")
    elif stats["conflicts"] or stats["possible_related"]:
        print("Usa --detalle para identificar en tu terminal los casos que revisar.")
    if diagnostics:
        print("\n--- AVISOS DE FORMATO CSV ---")
        for source, line, reason in diagnostics:
            print("  {} linea {}: {}".format(source, line, reason))
        print("Comprueba manualmente estos registros antes de importar: una coma sin")
        print("comillas tambien podria pertenecer a una contrasena, no a la nota.")
    if dry_run:
        print("\nDRY RUN: no se ha creado ni modificado ningun archivo.")


def write_export(path, inputs, rows):
    output = Path(path)
    if any(output.resolve() == Path(filename).resolve() for filename in inputs):
        raise ValueError("La salida no puede ser ninguno de los CSV originales")
    if not output.parent.is_dir():
        raise ValueError("La carpeta de salida no existe: {}".format(output.parent))
    # Creacion exclusiva: no sobreescribir archivos ni seguir enlaces simbolicos.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(output, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=BITWARDEN_FIELDS, lineterminator="\n")
            writer.writeheader()
            for item in rows:
                writer.writerow({
                    "folder": "", "favorite": "", "type": "login",
                    "name": item.name, "notes": item.note, "fields": "",
                    "reprompt": "0", "login_uri": item.url,
                    "login_username": item.username,
                    "login_password": item.password, "login_totp": "",
                })
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audita y unifica CSV de Chrome, Brave y Firefox sin Internet."
    )
    for name in ("chrome", "brave", "firefox"):
        parser.add_argument("--" + name, metavar="ARCHIVO.csv", required=True,
                            help="Exportacion CSV de {}".format(name))
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true", help="Simula y muestra informe (predeterminado)")
    modes.add_argument("--apply", action="store_true", help="Escribe CSV final; requiere --output")
    parser.add_argument("--output", metavar="RUTA.csv", help="Ruta nueva para el CSV de Bitwarden")
    parser.add_argument("--repair-extra-notes", action="store_true",
                        help="Reconstruye comas sin citar en la ultima columna de notas de Chrome/Brave; requiere revision")
    parser.add_argument("--detalle", action="store_true",
                        help="Muestra dominios y usuarios enmascarados de conflictos")
    args = parser.parse_args(argv)
    if args.apply and not args.output:
        parser.error("--apply necesita --output RUTA.csv")
    if args.output and not args.apply:
        parser.error("--output solo se puede usar con --apply (dry run no escribe archivos)")
    files = {name: getattr(args, name) for name in ("chrome", "brave", "firefox")}
    try:
        # Una exportacion por navegador; se permite repetir el mismo contenido,
        # pero no el mismo archivo por error bajo nombres distintos.
        resolved = [Path(path).resolve() for path in files.values()]
        if len(set(resolved)) != len(resolved):
            raise ValueError("Has indicado el mismo archivo CSV para varios navegadores")
        rows = []
        diagnostics = []
        for browser, filename in files.items():
            rows.extend(read_export(browser, filename,
                                    repair_extra_notes=args.repair_extra_notes,
                                    diagnostics=diagnostics))
        if not rows:
            raise ValueError("Los CSV no contienen registros; se cancela")
        cleaned, stats = process(rows)
        report(stats, args.detalle, dry_run=not args.apply, diagnostics=diagnostics)
        if args.apply:
            filename = write_export(args.output, files.values(), cleaned)
            print("\nArchivo Bitwarden creado: {} ({} registros)".format(filename, len(cleaned)))
            print("IMPORTANTE: es texto plano. Importa como 'Bitwarden (csv)' y borra el")
            print("CSV generado y los CSV de origen cuando compruebes que todo funciona.")
            if os.name == "nt":
                print("En Windows comprueba los permisos de la carpeta de salida (ACL).")
    except (ValueError, UnicodeError, csv.Error, OSError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())