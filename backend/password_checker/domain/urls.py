"""URL identity rules. Never resolves or requests anything over the network."""
from __future__ import annotations

import re
from typing import Any, NamedTuple, Optional
from urllib.parse import urlsplit, urlunsplit

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
        network = host if port in (None, default_port) else "{}:{}".format(host, port)
        # Compatibilidad con IPv6 al reconstruir la autoridad.
        if ":" in host:
            network = "[{}]".format(host)
            if port not in (None, default_port):
                network += ":{}".format(port)
        path = parsed.path or "/"
        canonical = (scheme, network, path, parsed.query, parsed.fragment)
        return UrlInfo(canonical, host, scheme == "http", False,
                       bool(parsed.username or parsed.password))
    except ValueError:
        return UrlInfo(url, "", False, True, False)


def is_android_source(raw: str) -> bool:
    return ANDROID_SOURCE.fullmatch(raw.strip()) is not None


def supported_uri(raw: str) -> bool:
    """Require an explicit, known scheme when detecting shifted columns."""
    if not raw or not raw.strip() or raw != raw.strip():
        return False
    if not re.match(r"^(?:https?://|android://|androidapp://)", raw, re.IGNORECASE):
        return False
    return not parse_url(raw).invalid


def bitwarden_uri(raw: str) -> str:
    """Convert Chrome Android URIs to Bitwarden's app URI format."""
    match = ANDROID_SOURCE.fullmatch(raw.strip())
    if match:
        return "androidapp://" + match.group("package").lower()
    return raw


def web_origin(raw: str) -> Optional[str]:
    """Website origin only: never path, query, fragment or userinfo (may hold tokens)."""
    try:
        parsed = urlsplit(raw)
        scheme = parsed.scheme.lower()
        if (scheme not in ("http", "https") or not parsed.hostname
                or parsed.username is not None or parsed.password is not None):
            return None
        host = parsed.hostname.lower()
        host = "[" + host + "]" if ":" in host else host
        port = parsed.port
        if port is not None and port != _default_port(scheme):
            host += ":" + str(port)
        return urlunsplit((scheme, host, "/", "", ""))
    except ValueError:
        return None
