"""Markdown review report: one actionable row per credential, never passwords or notes."""
from __future__ import annotations

import re
from collections import Counter

from ..domain.accounts import masked_username
from ..domain.reuse import reused_password_groups
from ..domain.strength import Strength, assess_strength
from ..domain.urls import parse_url, web_origin

HIGH, MEDIUM, LOW = 0, 1, 2
PRIORITY_LABELS = ("Alta", "Media", "Baja")
STRENGTH_FINDINGS = {
    Strength.EMPTY: (HIGH, "Sin contraseña", "Comprobar si el acceso sigue siendo válido"),
    Strength.OBVIOUS: (HIGH, "Patrón de contraseña débil", "Cambiar por una contraseña larga y única"),
    Strength.SHORT: (MEDIUM, "Contraseña corta (<12 caracteres)", "Valorar cambio por una contraseña larga"),
    Strength.MODERATE: (MEDIUM, "Contraseña de 12-13 caracteres", "Revisar fortaleza en contexto"),
}


def markdown_cell(value, limit=None):
    """Escape table syntax and untrusted names; never allow new table rows."""
    value = re.sub(r"[\x00-\x1f\x7f]+", " ", str(value)).strip()
    if limit is not None and len(value) > limit:
        value = value[:limit - 1].rstrip() + "…"
    for ch in ("\\", "|", "[", "]", "*", "_", chr(96), "<", ">"):
        value = value.replace(ch, "\\" + ch)
    return value or "—"


def markdown_page(row):
    """Link to website origin only: never leak URL query, path tokens or userinfo."""
    name = markdown_cell(row.name.strip() or parse_url(row.url).host or "Sin nombre", 48)
    origin = web_origin(row.url)
    return "[{}]({})".format(name, origin) if origin else name


def _review_findings(rec, stats, conflict_ids, related_ids, reused_passwords):
    issues = []
    actions = []
    priority = LOW

    def add(level, issue, action):
        nonlocal priority
        priority = min(priority, level)
        issues.append(issue)
        if action not in actions:
            actions.append(action)

    url = parse_url(rec.url)
    if id(rec) in conflict_ids:
        add(HIGH, "Contraseñas distintas para la misma cuenta", "Verificar cuál funciona y retirar versiones obsoletas")
    if rec.password in reused_passwords and rec.password:
        add(HIGH, "Contraseña reutilizada", "Cambiar por una contraseña única")
    strength = STRENGTH_FINDINGS.get(assess_strength(rec.password))
    if strength:
        add(*strength)
    if not rec.username:
        add(MEDIUM, "Sin usuario", "Comprobar a qué cuenta corresponde")
    if not rec.url or url.invalid:
        add(MEDIUM, "URL ausente o no reconocida", "Comprobar dirección del servicio")
    if url.embedded_auth:
        add(HIGH, "URL con credenciales incrustadas", "Corregir URL y revisar exposición")
    if url.insecure_http:
        add(MEDIUM, "URL HTTP", "Localizar el acceso HTTPS")
    if id(rec) in related_ids:
        add(MEDIUM, "Mismo dominio y usuario en otras URL", "Comprobar si son accesos distintos")
    merged = stats["merged_per_row"].get(id(rec), 0)
    if merged:
        issues.append("{} duplicado(s) fusionado(s)".format(merged))
    if not actions:
        actions.append("Validar cuando se utilice")
    return priority, issues, actions


def make_markdown_report(rows, stats, diagnostics=()):
    """One actionable row per imported credential, no passwords or notes."""
    conflict_ids = {id(rec) for group in stats["conflicts"] for rec in group}
    related_ids = {id(rec) for group in stats["possible_related"] for rec in group}
    reused_passwords = {group[0].password for group in reused_password_groups(rows)}

    records = []
    for rec in rows:
        priority, issues, actions = _review_findings(rec, stats, conflict_ids, related_ids, reused_passwords)
        records.append((priority, rec, issues, actions))

    records.sort(key=lambda item: (item[0], (item[1].name or parse_url(item[1].url).host).casefold(), item[1].username.casefold()))
    counts = Counter(level for level, _, _, _ in records)
    lines = [
        "# Informe de revisión de credenciales", "",
        "> Generado localmente. Contiene nombres de servicios y usuarios enmascarados; **no compartir públicamente**.",
        "> No contiene contraseñas ni notas. Los enlaces web apuntan solo al origen (sin rutas, parámetros ni fragmentos).", "",
        "## Resumen", "",
        "- Filas originales: **{}**".format(stats["originals"]),
        "- Duplicados exactos fusionados: **{}**".format(stats["duplicates"]),
        "- Credenciales para Bitwarden: **{}**".format(stats["final"]),
        "- Cuentas con conflicto: **{}**".format(len(stats["conflicts"])),
        "- Grupos de reutilización: **{}**".format(stats["reused_groups"]),
        "- Prioridad alta: **{}**; media: **{}**; baja: **{}**".format(counts[HIGH], counts[MEDIUM], counts[LOW]),
        "", "## Revisión por credencial", "",
        "| Nº | Prioridad | Página | Usuario | Motivo | Acción recomendada |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for number, (priority, rec, issues, actions) in enumerate(records, start=1):
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            number, PRIORITY_LABELS[priority], markdown_page(rec),
            markdown_cell(masked_username(rec.username)),
            markdown_cell("; ".join(issues) if issues else "Sin incidencias detectadas"),
            markdown_cell("; ".join(actions))))
    if diagnostics:
        lines += ["", "## Avisos de lectura CSV", "",
                  "Revisa manualmente las filas reparadas antes de importar:", ""]
        for source, line, reason in diagnostics:
            lines.append("- {}: línea {} — {}".format(markdown_cell(source), line, markdown_cell(reason)))
    lines += ["", "## Alcance", "",
              "La fortaleza es orientativa y no se comprueba la validez de las cuentas ni si hubo filtraciones.",
              "Las contraseñas en conflicto se conservan en Bitwarden; no se elige ninguna automáticamente.",
              "Los duplicados exactos ya fusionados no requieren otra acción por ese solo motivo.", ""]
    return "\n".join(lines)
