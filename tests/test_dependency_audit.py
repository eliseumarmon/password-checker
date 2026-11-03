"""The dependency audit report never turns a failed or partial audit into a pass. Report shapes follow real
pip-audit 2.10 and npm audit (auditReportVersion 2) output; package names and advisories are public data."""
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

# The script lives with the CI workflows, outside any package; dataclasses need it registered before it runs.
SCRIPT = Path(__file__).resolve().parents[1] / '.github' / 'scripts' / 'dependency_audit.py'
spec = importlib.util.spec_from_file_location('dependency_audit', SCRIPT)
audit = importlib.util.module_from_spec(spec)
sys.modules['dependency_audit'] = audit
spec.loader.exec_module(audit)

CONSTRAINTS = '# header\ncryptography==50.0.2\nfastapi==0.162.0\ntomli==2.5.0 ; python_version < "3.11"\n'
REQUIREMENTS = '-r requirements.txt\ncryptography>=50.0.2\nfastapi[standard]>=0.115,<1  # web\n'


def python_report(*dependencies):
    return {'dependencies': list(dependencies), 'fixes': []}


def dep(name, version, *vulns):
    return {'name': name, 'version': version, 'vulns': list(vulns)}


CLEAN_PYTHON = python_report(dep('cryptography', '50.0.2'), dep('fastapi', '0.162.0'))
CRYPTO_VULN = {'id': 'PYSEC-2026-3552', 'fix_versions': ['50.0.0'],
               'aliases': ['CVE-2026-69247', 'GHSA-g6cj-pr64-35w5'], 'description': 'PKCS#7 oracle'}
OPENSSL_VULN = {'id': 'GHSA-537c-gmf6-5ccf', 'fix_versions': ['48.0.1'], 'aliases': [], 'description': 'OpenSSL'}

LOCKFILE = {'packages': {'': {'name': 'probe'}, 'node_modules/lodash': {'version': '4.17.20'},
                         'node_modules/minimist': {'version': '1.2.5', 'dev': True}}}


def npm_report(total, **vulnerabilities):
    return {'auditReportVersion': 2, 'vulnerabilities': vulnerabilities,
            'metadata': {'vulnerabilities': {'total': len(vulnerabilities)}, 'dependencies': {'total': total}}}


LODASH = {'name': 'lodash', 'severity': 'high', 'isDirect': True, 'range': '<=4.17.23', 'nodes': ['node_modules/lodash'],
          'via': [{'source': 1106913, 'title': 'Command Injection in lodash',
                   'url': 'https://github.com/advisories/GHSA-35jh-r3h4-6jhm'}],
          'fixAvailable': {'name': 'lodash', 'version': '4.18.1', 'isSemVerMajor': False}}
MINIMIST = {'name': 'minimist', 'severity': 'critical', 'isDirect': True, 'range': '1.0.0 - 1.2.5',
            'nodes': ['node_modules/minimist'],
            'via': [{'source': 1097678, 'title': 'Prototype Pollution in minimist',
                     'url': 'https://github.com/advisories/GHSA-xvch-5gv4-984h'}],
            'fixAvailable': {'name': 'minimist', 'version': '1.2.8', 'isSemVerMajor': False}}


class PythonAuditTests(unittest.TestCase):
    def test_a_clean_report_covering_every_pin_passes(self):
        self.assertEqual(audit.python_findings(CLEAN_PYTHON, CONSTRAINTS, REQUIREMENTS, 0), [])

    def test_vulnerabilities_are_reported_once_per_advisory_with_their_fix(self):
        report = python_report(dep('cryptography', '46.0.7', CRYPTO_VULN, OPENSSL_VULN, CRYPTO_VULN),
                               dep('fastapi', '0.162.0'))
        findings = audit.python_findings(report, CONSTRAINTS.replace('50.0.2', '46.0.7'), REQUIREMENTS, 1)
        self.assertEqual([(f.package, f.version, f.scope) for f in findings], [('cryptography', '46.0.7', 'production')])
        self.assertEqual(findings[0].advisories, ['GHSA-537c-gmf6-5ccf', 'PYSEC-2026-3552 (CVE-2026-69247, GHSA-g6cj-pr64-35w5)'])
        self.assertEqual(findings[0].fix, '48.0.1, 50.0.0')

    def test_an_audit_of_no_dependencies_is_not_a_pass(self):
        # pip-audit exits 0 with "No known vulnerabilities found" when the input lists nothing.
        with self.assertRaisesRegex(audit.UntrustedReport, 'cryptography'):
            audit.python_findings(python_report(), CONSTRAINTS, REQUIREMENTS, 0)

    def test_constraints_without_packages_are_not_a_pass(self):
        # An emptied constraints file made pip-audit analyse nothing, and CI passed (test branch, L20).
        with self.assertRaisesRegex(audit.UntrustedReport, 'no packages'):
            audit.python_findings(python_report(), '# header only\n', '', 0)

    def test_a_direct_requirement_missing_from_the_constraints_is_not_a_pass(self):
        with self.assertRaisesRegex(audit.UntrustedReport, 'fastapi'):
            audit.python_findings(python_report(dep('cryptography', '50.0.2')), '# header\ncryptography==50.0.2\n',
                                  REQUIREMENTS, 0)

    def test_a_pinned_package_missing_from_the_report_is_not_a_pass(self):
        with self.assertRaisesRegex(audit.UntrustedReport, 'fastapi'):
            audit.python_findings(python_report(dep('cryptography', '50.0.2')), CONSTRAINTS, REQUIREMENTS, 0)

    def test_a_package_audited_at_another_version_is_not_a_pass(self):
        report = python_report(dep('cryptography', '49.0.0'), dep('fastapi', '0.162.0'))
        with self.assertRaisesRegex(audit.UntrustedReport, 'cryptography'):
            audit.python_findings(report, CONSTRAINTS, REQUIREMENTS, 0)

    def test_a_skipped_package_is_not_a_pass(self):
        skipped = {'name': 'fastapi', 'skip_reason': 'Dependency not found on PyPI'}
        with self.assertRaisesRegex(audit.UntrustedReport, 'fastapi'):
            audit.python_findings(python_report(dep('cryptography', '50.0.2'), skipped), CONSTRAINTS, REQUIREMENTS, 0)

    def test_a_failing_tool_with_a_clean_report_is_not_a_pass(self):
        with self.assertRaisesRegex(audit.UntrustedReport, 'exit code 1'):
            audit.python_findings(CLEAN_PYTHON, CONSTRAINTS, REQUIREMENTS, 1)

    def test_a_missing_or_malformed_report_is_not_a_pass(self):
        for report in (None, {'fixes': []}, {'dependencies': 'none'}):
            with self.subTest(report=report), self.assertRaises(audit.UntrustedReport):
                audit.python_findings(report, CONSTRAINTS, REQUIREMENTS, 0)


class NpmAuditTests(unittest.TestCase):
    def test_a_clean_report_covering_the_lockfile_passes(self):
        self.assertEqual(audit.npm_findings(npm_report(2), npm_report(2), LOCKFILE, 0, 0), [])

    def test_vulnerabilities_are_split_into_production_and_development(self):
        findings = audit.npm_findings(npm_report(2, lodash=LODASH, minimist=MINIMIST), npm_report(2, lodash=LODASH),
                                      LOCKFILE, 1, 1)
        self.assertEqual([(f.package, f.version, f.scope, f.severity) for f in findings],
                         [('lodash', '4.17.20', 'production', 'high'), ('minimist', '1.2.5', 'development', 'critical')])
        self.assertEqual(findings[0].advisories,
                         ['Command Injection in lodash (https://github.com/advisories/GHSA-35jh-r3h4-6jhm)'])
        self.assertEqual(findings[0].fix, 'lodash 4.18.1')

    def test_a_vulnerability_reached_through_another_package_names_it(self):
        transitive = dict(MINIMIST, via=['mkdirp'], isDirect=False, fixAvailable=True)
        findings = audit.npm_findings(npm_report(2, minimist=transitive), npm_report(2), LOCKFILE, 1, 0)
        self.assertEqual((findings[0].advisories, findings[0].fix), (['via mkdirp'], 'npm audit fix'))

    def test_an_audit_of_fewer_packages_than_the_lockfile_is_not_a_pass(self):
        for total in (0, 1):
            with self.subTest(total=total), self.assertRaisesRegex(audit.UntrustedReport, 'analysed'):
                audit.npm_findings(npm_report(total), npm_report(total), LOCKFILE, 0, 0)

    def test_an_empty_lockfile_is_not_a_pass(self):
        # npm audit exits 0 with a total of 0 for a project without dependencies.
        with self.assertRaisesRegex(audit.UntrustedReport, 'no packages'):
            audit.npm_findings(npm_report(0), npm_report(0), {'packages': {'': {'name': 'probe'}}}, 0, 0)

    def test_an_npm_error_report_is_not_a_pass(self):
        error = {'message': 'audit endpoint returned an error', 'error': {'summary': '', 'detail': ''}}
        with self.assertRaisesRegex(audit.UntrustedReport, 'audit endpoint returned an error'):
            audit.npm_findings(npm_report(2), error, LOCKFILE, 0, 1)

    def test_an_unknown_report_format_is_not_a_pass(self):
        with self.assertRaisesRegex(audit.UntrustedReport, 'auditReportVersion'):
            audit.npm_findings(dict(npm_report(2), auditReportVersion=3), npm_report(2), LOCKFILE, 0, 0)

    def test_a_failing_tool_with_a_clean_report_is_not_a_pass(self):
        with self.assertRaisesRegex(audit.UntrustedReport, 'exit code 1'):
            audit.npm_findings(npm_report(2), npm_report(2), LOCKFILE, 1, 0)


class CommandLineTests(unittest.TestCase):
    """CI relies on the exit status and on the printed table."""

    def run_main(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            status = audit.main(list(args))
        return status, output.getvalue()

    def test_python_command_fails_on_a_missing_report_and_passes_on_a_clean_one(self):
        with tempfile.TemporaryDirectory() as folder:
            constraints = Path(folder, 'constraints.txt')
            constraints.write_text(CONSTRAINTS)
            requirements = Path(folder, 'requirements.txt')
            requirements.write_text(REQUIREMENTS)
            report = Path(folder, 'report.out')
            status, output = self.run_main('python', '--report', str(report), '--constraints', str(constraints),
                                           '--requirements', str(requirements), '--exit-code', '1')
            self.assertEqual(status, 1)
            self.assertIn('cannot be trusted', output)
            report.write_text(json.dumps(CLEAN_PYTHON))
            status, output = self.run_main('python', '--report', str(report), '--constraints', str(constraints),
                                           '--requirements', str(requirements), '--exit-code', '0')
            self.assertEqual(status, 0)
            self.assertIn('No known vulnerabilities in 2 packages', output)

    def test_npm_command_fails_and_lists_the_affected_packages(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = {name: Path(folder, f'{name}.out') for name in ('full', 'production', 'lockfile')}
            paths['full'].write_text(json.dumps(npm_report(2, lodash=LODASH, minimist=MINIMIST)))
            paths['production'].write_text(json.dumps(npm_report(2, lodash=LODASH)))
            paths['lockfile'].write_text(json.dumps(LOCKFILE))
            status, output = self.run_main('npm', '--full', str(paths['full']), '--production', str(paths['production']),
                                           '--lockfile', str(paths['lockfile']), '--exit-full', '1',
                                           '--exit-production', '1')
            self.assertEqual(status, 1)
            self.assertIn('| lodash | 4.17.20 | production | high |', output)
            self.assertIn('| minimist | 1.2.5 | development | critical |', output)


if __name__ == '__main__':
    unittest.main()
