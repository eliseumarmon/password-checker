"""Markdown review report through its public function; fictional credentials only."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.application.review_report import make_markdown_report  # noqa: E402
from backend.password_checker.domain.consolidation import consolidate  # noqa: E402
from backend.password_checker.domain.credential import Credential  # noqa: E402


def report_rows(*credentials):
    """Map each page name to its (priority, reason) cells."""
    cleaned, stats = consolidate([Credential('chrome', n, *c) for n, c in enumerate(credentials, 2)])
    cells = {}
    for line in make_markdown_report(cleaned, stats).splitlines():
        if line.startswith('| ') and not line.startswith(('| Nº', '| ---')):
            parts = [p.strip() for p in line.strip('|').split(' | ')]
            cells[parts[2]] = (parts[1], parts[4])
    return cells


class ReviewReportTests(unittest.TestCase):
    def test_priority_and_reason_per_strength_level(self):
        cells = report_rows(
            ('Empty', 'https://empty.invalid', 'u1', '', ''),
            ('Obvious', 'https://obvious.invalid', 'u2', 'qwerty123', ''),
            ('Short', 'https://short.invalid', 'u3', 'fake-1234', ''),
            ('Moderate', 'https://moderate.invalid', 'u4', 'fake-12345678', ''),
            ('Strong', 'https://strong.invalid', 'u5', 'fake-1234567890', ''))
        self.assertEqual(cells['[Empty](https://empty.invalid/)'], ('Alta', 'Sin contraseña'))
        self.assertEqual(cells['[Obvious](https://obvious.invalid/)'], ('Alta', 'Patrón de contraseña débil'))
        self.assertEqual(cells['[Short](https://short.invalid/)'], ('Media', 'Contraseña corta (\\<12 caracteres)'))
        self.assertEqual(cells['[Moderate](https://moderate.invalid/)'], ('Media', 'Contraseña de 12-13 caracteres'))
        self.assertEqual(cells['[Strong](https://strong.invalid/)'], ('Baja', 'Sin incidencias detectadas'))

    def test_blank_names_fall_back_to_package_host_or_placeholder(self):
        cells = report_rows(
            ('  ', 'https://blank.invalid/login', 'u1', 'fake-1234567890', ''),
            ('', 'android://FAKE@com.example.blank/', 'u2', 'fake-1234567891', ''),
            (' ', '', 'u3', 'fake-1234567892', ''))
        self.assertIn('[blank.invalid](https://blank.invalid/)', cells)
        self.assertIn('com.example.blank', cells)
        self.assertIn('Acceso sin nombre', cells)

    def test_url_findings_and_unlinked_unsafe_urls(self):
        cells = report_rows(
            ('Plain', 'http://plain.invalid/login', 'u1', 'fake-1234567890', ''),
            ('Embedded', 'https://u:pw@embedded.invalid/x', 'u2', 'fake-0987654321', ''))
        self.assertEqual(cells['[Plain](http://plain.invalid/)'], ('Media', 'URL HTTP'))
        self.assertEqual(cells['Embedded'], ('Alta', 'URL con credenciales incrustadas'))

    def test_reused_password_is_high_priority_for_every_account(self):
        cells = report_rows(
            ('A', 'https://a.invalid', 'alice', 'fake-shared-123456', ''),
            ('B', 'https://b.invalid', 'bob', 'fake-shared-123456', ''))
        self.assertEqual(cells['[A](https://a.invalid/)'], ('Alta', 'Contraseña reutilizada'))
        self.assertEqual(cells['[B](https://b.invalid/)'], ('Alta', 'Contraseña reutilizada'))


if __name__ == '__main__':
    unittest.main()
