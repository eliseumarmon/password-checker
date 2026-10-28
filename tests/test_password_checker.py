"""Pruebas con contrasenas FICTICIAS; nunca usar exportaciones reales en tests."""
import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditar_contrasenas_local import read_export, process  # noqa: E402


class PasswordCheckerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.chrome = self.root / 'chrome.csv'
        self.brave = self.root / 'brave.csv'
        self.firefox = self.root / 'firefox.csv'
        self._csv(self.chrome,
                  ['name', 'url', 'username', 'password', 'note'],
                  [['GitHub', 'https://github.com/login', 'alice', 'fake-correct-123456', 'nota, con coma\n y salto de linea'],
                   ['GitHub', 'https://github.com/login', 'alice', 'fake-old-123456789', 'vieja'],
                   ['Otro', 'https://service.invalid', 'bob', 'fake-correct-123456', '']])
        self._csv(self.brave,
                  ['name', 'url', 'username', 'password', 'note'],
                  [['GH', 'https://github.com/login', 'alice', 'fake-correct-123456', 'otra nota']])
        self._csv(self.firefox,
                  ['url', 'username', 'password', 'httpRealm', 'formActionOrigin', 'guid',
                   'timeCreated', 'timeLastUsed', 'timePasswordChanged'],
                  [['https://github.com/login', 'alice', 'fake-correct-123456', '',
                    'https://github.com', 'guid-ficticio', '1710000', '1720000', '1730000'],
                   ['https://basic.invalid/path', 'bob', 'fake-strong-123456', 'Area privada',
                    '', 'guid-ficticio-2', '1710001', '1720001', '1730001']])

    @staticmethod
    def _csv(path, headers, rows):
        with path.open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / 'auditar_contrasenas_local.py'),
             '--chrome', str(self.chrome), '--brave', str(self.brave),
             '--firefox', str(self.firefox), *args],
            capture_output=True, text=True, cwd=self.root)

    def test_parsing_duplicate_merge_and_conflicts(self):
        rows = sum((read_export(s, p) for s, p in
                    [('chrome', self.chrome), ('brave', self.brave), ('firefox', self.firefox)]), [])
        cleaned, info = process(rows)
        self.assertEqual(info['originals'], 6)
        self.assertEqual(info['duplicates'], 2)
        self.assertEqual(info['final'], 4)
        self.assertEqual(len(info['conflicts']), 1)
        self.assertEqual(info['reused_groups'], 1)
        self.assertEqual(info['notes_merged'], 1)
        self.assertEqual(len(cleaned), 4)
        merged = next(x for x in cleaned if x.username == 'alice' and x.password == 'fake-correct-123456')
        self.assertIn('nota, con coma\n y salto de linea', merged.note)
        self.assertIn('otra nota', merged.note)
        basic = next(x for x in cleaned if x.url == 'https://basic.invalid/path')
        self.assertIn('Firefox HTTP realm: Area privada', basic.note)

    def test_dry_run_default_no_writes_or_secrets(self):
        before = set(self.root.iterdir())
        result = self.run_cli('--detalle')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(self.root.iterdir()), before)
        self.assertIn('DRY RUN', result.stdout)
        self.assertIn('Conflictos', result.stdout)
        self.assertNotIn('fake-correct-123456', result.stdout)
        self.assertNotIn('fake-old-123456789', result.stdout)

    def test_apply_creates_bitwarden_and_refuses_overwrite(self):
        output = self.root / 'bitwarden_import.csv'
        result = self.run_cli('--apply', '--output', str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(output.is_file())
        with output.open(encoding='utf-8', newline='') as handle:
            lines = list(csv.DictReader(handle))
        self.assertEqual(len(lines), 4)
        self.assertEqual(len(lines[0]), 11)
        self.assertEqual(lines[0]['type'], 'login')
        again = self.run_cli('--apply', '--output', str(output))
        self.assertNotEqual(again.returncode, 0)
        self.assertIn('ERROR', again.stderr)
        if os.name != 'nt':
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_rejects_malformed_chrome_with_accurate_location(self):
        self.chrome.write_text('name,url,username,password,note\n'
                               'Site,https://test.invalid,alice,fake-PW,note,not-quoted\n', encoding='utf-8')
        result = self.run_cli('--dry-run')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('chrome: linea 2: 6 columnas, esperadas 5', result.stderr)
        self.assertIn('--repair-extra-notes', result.stderr)
        self.assertNotIn('fake-PW', result.stderr)

    def test_opt_in_repair_only_for_trailing_note(self):
        self.chrome.write_text('name,url,username,password,note\n'
                               'Site,https://test.invalid,alice,fake-PW,note,not-quoted\n', encoding='utf-8')
        result = self.run_cli('--repair-extra-notes', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('chrome linea 2: nota reconstruida', result.stdout)
        output = self.root / 'out.csv'
        result = self.run_cli('--repair-extra-notes', '--apply', '--output', str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        with output.open(encoding='utf-8', newline='') as f:
            lines = list(csv.DictReader(f))
        entry = next(row for row in lines if row['login_uri'] == 'https://test.invalid')
        self.assertEqual(entry['notes'], 'note,not-quoted')
        self.assertEqual(entry['login_password'], 'fake-PW')

    def test_missing_unambiguous_trailing_note(self):
        self.chrome.write_text('name,url,username,password,note\n'
                               'Site,https://test.invalid,alice,fake-PW\n', encoding='utf-8')
        result = self.run_cli('--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('nota final vacia completada', result.stdout)

    def test_refuses_ambiguous_missing_fields(self):
        self.chrome.write_text('name,url,username,password,note\n'
                               'Site,https://test.invalid,alice\n', encoding='utf-8')
        result = self.run_cli('--apply', '--output', str(self.root / 'out.csv'))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'out.csv').exists())

    def test_stays_safe_if_password_contains_valid_csv_comma(self):
        self._csv(self.chrome, ['name', 'url', 'username', 'password', 'note'],
                  [['Commas', 'https://test.invalid', 'carol', 'fake,with,commas', 'nota,comas']])
        result = self.run_cli('--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = read_export('chrome', self.chrome)
        self.assertEqual(rows[0].password, 'fake,with,commas')
        self.assertEqual(rows[0].note, 'nota,comas')


    def test_android_uri_unquoted_comma_in_title(self):
        self.chrome.write_text(
            'name,url,username,password,note\n'
            'Red social,mensajero,android://FAKE@com.example.social/,user42,fake-password-123,\n',
            encoding='utf-8')
        diagnostics = []
        rows = read_export('chrome', self.chrome, diagnostics=diagnostics)
        self.assertEqual(rows[0].name, 'Red social,mensajero')
        self.assertEqual(rows[0].username, 'user42')
        self.assertEqual(rows[0].password, 'fake-password-123')
        self.assertEqual(len(diagnostics), 1)
        cleaned, stats = process(rows)
        self.assertEqual(stats['invalid_url'], 0)
        self.assertEqual(cleaned[0].url, 'androidapp://com.example.social')
        self.assertIn('android://FAKE@com.example.social/', cleaned[0].note)

    def test_android_uri_no_title_comma(self):
        uri = 'android://FAKE@com.example.shop/'
        self._csv(self.chrome, ['name','url','username','password','note'],
                  [['Shop',uri,'user42','fake-password-123','']])
        rows = read_export('chrome', self.chrome)
        self.assertEqual(rows[0].url, uri)
        self.assertEqual(rows[0].password, 'fake-password-123')
        cleaned, stats = process(rows)
        self.assertEqual(stats['invalid_url'], 0)
        self.assertEqual(cleaned[0].url, 'androidapp://com.example.shop')

    def test_shifted_title_with_missing_trailing_note(self):
        self.chrome.write_text(
            'name,url,username,password,note\n'
            'Red social,mensajero,android://FAKE@com.example.social/,user42,fake-password-123\n',
            encoding='utf-8')
        rows = read_export('chrome', self.chrome)
        self.assertEqual(rows[0].name, 'Red social,mensajero')
        self.assertEqual(rows[0].note, '')

    def test_repair_notes_rejects_misaligned_uri(self):
        self.chrome.write_text(
            'name,url,username,password,note\n'
            'Red,social,mensajero,android://FAKE@com.example.social/,user42,fake-password-123,\n',
            encoding='utf-8')
        result = self.run_cli('--repair-extra-notes', '--dry-run')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('URI fuera de su columna', result.stderr)
        self.assertNotIn('fake-password-123', result.stderr)

    def test_dry_run_report_only_and_no_passwords(self):
        report = self.root / 'revisar.md'
        result = self.run_cli('--dry-run', '--report', str(report))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(report.exists())
        self.assertFalse((self.root / 'bitwarden_import.csv').exists())
        content = report.read_text(encoding='utf-8')
        self.assertIn('| Nº | Prioridad | Página | Usuario | Motivo | Acción recomendada |', content)
        self.assertIn('[GitHub](https://github.com/)', content)
        self.assertIn('Verificar cuál funciona', content)
        self.assertIn('Contraseña reutilizada', content)
        self.assertIn('Duplicados exactos fusionados: **2**', content)
        self.assertNotIn('fake-correct-123456', content)
        self.assertNotIn('fake-old-123456789', content)
        self.assertNotIn('nota, con coma', content)
        self.assertEqual(content.count('\n| 1 |'), 1)
        if os.name != 'nt':
            self.assertEqual(report.stat().st_mode & 0o777, 0o600)
        again = self.run_cli('--report', str(report))
        self.assertNotEqual(again.returncode, 0)
        self.assertIn('ya existe', again.stderr)

    def test_apply_generates_report_next_to_csv_by_default(self):
        output = self.root / 'bitwarden_import.csv'
        result = self.run_cli('--apply', '--output', str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.root / 'bitwarden_import_informe.md'
        self.assertTrue(report.exists())
        self.assertIn('[GitHub](https://github.com/)', report.read_text(encoding='utf-8'))
        self.assertTrue(output.exists())
        if os.name != 'nt':
            self.assertEqual(report.stat().st_mode & 0o777, 0o600)

    def test_report_markdown_links_escape_names_and_strip_tokens(self):
        from auditar_contrasenas_local import Credential, make_markdown_report
        rows = [Credential('chrome', 2, 'Site | [danger] ',
                           'https://user:secret@private.invalid/reset/token?key=secret',
                           'someone@example.invalid', 'fake-pass-1234567890', ''),
                Credential('chrome', 3, 'Safe|[label]\nsecond row',
                           'https://host.invalid/reset/TOKEN?token=abc#secret',
                           'bob', 'fake-pass-9876543210', '')]
        cleaned, stats = process(rows)
        result = make_markdown_report(cleaned, stats)
        self.assertIn('Safe\\|\\[label\\] second row', result)
        self.assertIn('[Safe\\|\\[label\\] second row](https://host.invalid/)', result)
        self.assertNotIn('token=abc', result)
        self.assertNotIn('reset/TOKEN', result)
        self.assertNotIn('user:secret', result)
        self.assertNotIn('fake-pass-1234567890', result)
        self.assertNotIn('fake-pass-9876543210', result)
        table_rows = [row for row in result.splitlines() if row.startswith('| ')]
        self.assertEqual(len(table_rows), 4)

    def test_android_app_report_uses_plain_name_not_uri(self):
        from auditar_contrasenas_local import make_markdown_report
        self._csv(self.chrome, ['name', 'url', 'username', 'password', 'note'], [
            ['VK: red social, mensajero', 'android://FAKE@com.example.social/',
             'phoneuser', 'fake-password-12345', '']])
        rows = read_export('chrome', self.chrome)
        cleaned, stats = process(rows)
        result = make_markdown_report(cleaned, stats)
        self.assertIn('VK: red social, mensajero', result)
        self.assertNotIn('FAKE@com.example.social', result)
        self.assertNotIn('androidapp://', result)

    def test_report_path_cannot_overwrite_input_or_output(self):
        output = self.root / 'bitwarden.csv'
        result = self.run_cli('--report', str(self.chrome))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no puede coincidir', result.stderr)
        result = self.run_cli('--apply', '--output', str(output), '--report', str(output))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())
        self.assertIn('no puede coincidir', result.stderr)

    def test_csv_utf8_and_semicolon_diagnostic(self):
        self.chrome.write_text('name;url;username;password;note\nSite;https://test.invalid;alice;abc;note\n', encoding='utf-8')
        result = self.run_cli('--dry-run')
        self.assertIn('punto y coma', result.stderr)


if __name__ == '__main__':
    unittest.main()
