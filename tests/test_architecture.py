"""Dependency rule: the domain stays pure and adapters never import the CLI entry script."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_MODULES = ('accounts', 'consolidation', 'credential', 'notes', 'reuse', 'strength', 'urls')


def loaded_modules(module):
    """Import *module* in a fresh interpreter and return every loaded module name."""
    code = 'import sys, {0}; print("\\n".join(sorted(sys.modules)))'.format(module)
    result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True, check=True)
    return set(result.stdout.split())


class ArchitectureTests(unittest.TestCase):
    def test_domain_has_no_adapter_or_framework_dependencies(self):
        forbidden = ('backend.password_checker.infrastructure', 'backend.password_checker.application',
                     'backend.password_checker.cli', 'backend.password_checker.workspace',
                     'auditar_contrasenas_local', 'fastapi', 'starlette', 'pydantic',
                     'cryptography', 'argon2', 'csv')
        for name in DOMAIN_MODULES:
            loaded = loaded_modules('backend.password_checker.domain.' + name)
            leaked = sorted(m for m in loaded if any(m == p or m.startswith(p + '.') for p in forbidden))
            self.assertEqual(leaked, [], name)

    def test_workspace_does_not_import_the_cli_entry_script(self):
        self.assertNotIn('auditar_contrasenas_local', loaded_modules('backend.password_checker.workspace'))


if __name__ == '__main__':
    unittest.main()
