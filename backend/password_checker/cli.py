"""Command-line adapter: argument parsing, console summary and file outputs.

Por defecto SOLO simula e informa. --apply --output RUTA crea un unico CSV
SIN sobrescribir archivos existentes. Conserva las contrasenas en conflicto
como registros separados para que puedas decidir cual es valida.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

from .application.review_report import make_markdown_report
from .domain.accounts import masked_username
from .domain.consolidation import consolidate
from .domain.urls import parse_url
from .infrastructure.bitwarden import write_bitwarden_csv
from .infrastructure.csv_reader import read_export
from .infrastructure.files import create_new_file

BROWSERS = ("chrome", "brave", "firefox")


def label(rec):
    url = parse_url(rec.url)
    site = url.host if url.host else ("(URL no reconocida)" if url.invalid else "(sin URL)")
    return "{} / {}".format(site, masked_username(rec.username))


def report(stats, details, dry_run, diagnostics=(), report_requested=False):
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
    print("Aplicaciones Android convertidas a formato Bitwarden: {}".format(stats["android_apps"]))
    print("Registros con URL no reconocida: {}".format(stats["invalid_url"]))
    print("Registros con usuario/clave incrustados en URL: {}".format(stats["url_credentials"]))
    print("Filas sin deduplicacion segura: {}".format(stats["undedupeable"]))
    print("\nLos conflictos NO se descartan: ambas claves se conservan para revision.")
    print("Las notas diferentes se conservan. No se fusionan URLs distintas por dominio.")
    print("Las URI android:// se convierten a androidapp:// y se conserva la original en notas.")
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
        print("\nDRY RUN: no se crea CSV de Bitwarden." if report_requested else
              "\nDRY RUN: no se ha creado ni modificado ningun archivo.")


def write_report(path, inputs, markdown):
    """Create a private Markdown/text report without overwriting anything."""
    return create_new_file(
        path, inputs, lambda file: file.write(markdown),
        same_as_protected_error="El informe no puede sobrescribir un CSV de entrada",
        missing_folder_error="No existe la carpeta del informe: {}", newline="\n")


def write_export(path, inputs, rows):
    # Creacion exclusiva: no sobreescribir archivos ni seguir enlaces simbolicos.
    return create_new_file(
        path, inputs, lambda file: write_bitwarden_csv(file, rows),
        same_as_protected_error="La salida no puede ser ninguno de los CSV originales",
        missing_folder_error="La carpeta de salida no existe: {}", newline="")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Audita y unifica CSV de Chrome, Brave y Firefox sin Internet."
    )
    for name in BROWSERS:
        parser.add_argument("--" + name, metavar="ARCHIVO.csv", required=True,
                            help="Exportacion CSV de {}".format(name))
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true", help="Simula y muestra informe (predeterminado)")
    modes.add_argument("--apply", action="store_true", help="Escribe CSV final; requiere --output")
    parser.add_argument("--output", metavar="RUTA.csv", help="Ruta nueva para el CSV de Bitwarden")
    parser.add_argument("--report", metavar="RUTA.md",
                        help="Guarda tabla Markdown de revisión (también en dry-run, sin crear CSV)")
    parser.add_argument("--repair-extra-notes", action="store_true",
                        help="Reconstruye comas sin citar en la ultima columna de notas de Chrome/Brave; requiere revision")
    parser.add_argument("--detalle", action="store_true",
                        help="Muestra dominios y usuarios enmascarados de conflictos")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.apply and not args.output:
        parser.error("--apply necesita --output RUTA.csv")
    if args.output and not args.apply:
        parser.error("--output solo se puede usar con --apply (dry run no escribe archivos)")
    files = {name: getattr(args, name) for name in BROWSERS}
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
        cleaned, stats = consolidate(rows)
        report_path = (args.report or
                       str(Path(args.output).with_name(Path(args.output).stem + "_informe.md"))
                       if args.apply else args.report)
        # Dry-run solo escribe un informe cuando se solicita explicitamente.
        if report_path:
            targets = [Path(path).resolve() for path in files.values()]
            if args.apply:
                targets.append(Path(args.output).resolve())
            if Path(report_path).resolve() in targets:
                raise ValueError("El informe no puede coincidir con ningun CSV de entrada o salida")
            if Path(report_path).exists():
                raise ValueError("El informe ya existe: {}".format(report_path))
        if args.apply and Path(args.output).exists():
            raise ValueError("El CSV de salida ya existe: {}".format(args.output))
        report(stats, args.detalle, dry_run=not args.apply, diagnostics=diagnostics,
               report_requested=bool(report_path))
        created_report = None
        if report_path:
            content = make_markdown_report(cleaned, stats, diagnostics)
            created_report = write_report(report_path, files.values(), content)
            print("\nInforme Markdown creado: {}".format(created_report))
        if args.apply:
            try:
                filename = write_export(args.output, files.values(), cleaned)
            except BaseException:
                if created_report is not None:
                    created_report.unlink(missing_ok=True)
                raise
            print("\nArchivo Bitwarden creado: {} ({} registros)".format(filename, len(cleaned)))
            print("IMPORTANTE: es texto plano. Importa como 'Bitwarden (csv)' y borra el")
            print("CSV generado y los CSV de origen cuando compruebes que todo funciona.")
            if os.name == "nt":
                print("En Windows comprueba los permisos de la carpeta de salida (ACL).")
    except (ValueError, UnicodeError, csv.Error, OSError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 1
    return 0
