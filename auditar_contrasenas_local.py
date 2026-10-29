#!/usr/bin/env python3
"""Audita y unifica CSV de Chrome, Brave y Firefox para importar en Bitwarden.

Python 3.9+; solo biblioteca estandar; no accede a Internet.
Por defecto SOLO simula e informa. --apply --output RUTA crea un unico CSV
SIN sobrescribir archivos existentes. Conserva las contrasenas en conflicto
como registros separados para que puedas decidir cual es valida.

IMPORTANTE: Tanto los CSV originales como el CSV resultante contienen
contrasenas en texto plano. No los subas a repositorios, chats ni nubes.

Entry point only: the rules live in backend/password_checker (domain,
infrastructure, application) and the command line in backend/password_checker/cli.py.
"""

import sys

from backend.password_checker.cli import main

# Backward-compatible names for callers of the former single-file script.
from backend.password_checker.application.review_report import make_markdown_report  # noqa: F401
from backend.password_checker.domain.consolidation import consolidate as process  # noqa: F401
from backend.password_checker.domain.credential import Credential  # noqa: F401
from backend.password_checker.infrastructure.csv_reader import read_export  # noqa: F401

# Still imported by backend/password_checker/workspace.py until it uses the domain directly.
from backend.password_checker.domain.accounts import account_key  # noqa: F401
from backend.password_checker.domain.strength import is_obviously_weak as simple_weak  # noqa: F401
from backend.password_checker.domain.urls import bitwarden_uri, parse_url as url_parts  # noqa: F401
from backend.password_checker.infrastructure.bitwarden import BITWARDEN_FIELDS  # noqa: F401

if __name__ == "__main__":
    sys.exit(main())
