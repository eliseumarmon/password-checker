"""URL identity rules. Never resolves or requests anything over the network."""
from __future__ import annotations

import re
from typing import Any, NamedTuple
from urllib.parse import urlsplit

# Chrome exports Android app credentials using android://signature@package/.
# Bitwarden matches Android apps using androidapp://package.
ANDROID_SOURCE = re.compile(
    r"^android://(?P<signature>[^/@\s]+)@(?P<package>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)/?$",
    re.IGNORECASE,
)
ANDROIDAPP = re.compile(
    r"^androidapp://(?P<package>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)/?$",
    re.IGNORECASE,
)


class UrlInfo(NamedTuple):
    """Conservative identity of a login URL; also unpacks as a plain tuple."""
    key: Any
    host: str
    insecure_http: bool
    invalid: bool
    embedded_auth: bool


def _default_port(scheme: str) -> int:
    return 80 if scheme == "http" else 443


def parse_url(raw: str) -> UrlInfo:
    url = raw.strip()
    if not url:
        return UrlInfo("", "", False, True, False)
    app_source = ANDROID_SOURCE.fullmatch(url)
    if app_source:
        # Do not deduplicate different app signatures solely by package.
        package = app_source.group("package").casefold()
        return UrlInfo(("android-source", package, app_source.group("signature")),
                       package, False, False, False)
    app_uri = ANDROIDAPP.fullmatch(url)
    if app_uri:
        package = app_uri.group("package").casefold()
        return UrlInfo(("androidapp", package), package, False, False, False)
    try:
        # No aceptar esquemas inventados ni resolver URLs con peticiones externas.
        parsed = urlsplit(url if "://" in url else "https://" + url)
        scheme = parsed.scheme.casefold()
        host = (parsed.hostname or "").casefold()
        port = parsed.port  # Valida puertos malformados.
        if scheme not in ("http", "https") or not host:
            return UrlInfo(url, "", False, True, bool(parsed.username or parsed.password))
        # Mantener subdominios, rutas, parametros, fragmentos, puertos y esquemas.
        # Solo normalizamos mayusculas y el / vacio en la raiz.
        default_port = _default_port(scheme)
        network = host if port in (None, default_port) else f"{host}:{port}"
        # Compatibilidad con IPv6 al reconstruir la autoridad.
        if ":" in host:
            network = f"[{host}]"
            if port not in (None, default_port):
                network += f":{port}"
        path = parsed.path or "/"
        canonical = (scheme, network, path, parsed.query, parsed.fragment)
        return UrlInfo(canonical, host, scheme == "http", False,
                       bool(parsed.username or parsed.password))
    except ValueError:
        return UrlInfo(url, "", False, True, False)


def supported_uri(raw: str) -> bool:
    """Require an explicit, known scheme when detecting shifted columns."""
    if not raw or not raw.strip() or raw != raw.strip():
        return False
    if not re.match(r"^(?:https?://|android://|androidapp://)", raw, re.IGNORECASE):
        return False
    return not parse_url(raw).invalid


def android_package(raw: str) -> str | None:
    """Package of a Chrome android:// URI, exactly as written."""
    match = ANDROID_SOURCE.fullmatch(raw.strip())
    return match.group("package") if match else None


def bitwarden_uri(raw: str) -> str:
    """Convert Chrome Android URIs as Bitwarden's own Chrome importer does.

    The signing-key hash is dropped and the package keeps its case;
    see bitwarden/clients libs/importer/src/importers/chrome-csv-importer.ts.
    """
    package = android_package(raw)
    return "androidapp://" + package if package else raw
