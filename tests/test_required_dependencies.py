"""Mandatory dependencies fail loudly: a missing package must never turn the crypto or API tests into skips."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent

# Discovers one test module, as CI does, in a fresh interpreter where the given comma-separated packages cannot be
# imported.
PROBE = '''
import io, json, sys, unittest
for package in sys.argv[1].split(','):
    sys.modules[package] = None
suite = unittest.defaultTestLoader.discover(sys.argv[3], pattern=sys.argv[2] + '.py')
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(json.dumps({'errors': [text for _, text in result.errors], 'skipped': len(result.skipped)}))
'''


class RequiredDependencyTests(unittest.TestCase):
    def outcome_without(self, package, module):
        completed = subprocess.run([sys.executable, '-c', PROBE, package, module, str(TESTS)],
                                   capture_output=True, text=True, timeout=120, check=True)
        return json.loads(completed.stdout.strip().splitlines()[-1])

    def test_the_api_test_client_uses_httpx2(self):
        # Starlette silently falls back to the deprecated httpx client if httpx2 is not installed.
        import starlette.testclient
        self.assertEqual(starlette.testclient.httpx.__name__, 'httpx2')

    def test_a_missing_mandatory_dependency_is_an_error_not_a_skip(self):
        # Starlette's test client falls back to a leftover httpx when httpx2 is missing, so both are blocked;
        # with neither available it raises a RuntimeError asking for httpx2.
        for package, module, exception, named in [('cryptography', 'test_sessions', 'ModuleNotFoundError', 'cryptography'),
                                                  ('argon2', 'test_sessions', 'ModuleNotFoundError', 'argon2'),
                                                  ('cryptography', 'test_session_limits', 'ModuleNotFoundError', 'cryptography'),
                                                  ('fastapi', 'test_api', 'ModuleNotFoundError', 'fastapi'),
                                                  ('httpx2,httpx', 'test_api', 'RuntimeError', 'httpx2')]:
            with self.subTest(package=package, module=module):
                outcome = self.outcome_without(package, module)
                self.assertEqual(outcome['skipped'], 0)
                self.assertTrue(outcome['errors'])
                # The final exception of each error is caused by the blocked package, not by another collection problem.
                for error in outcome['errors']:
                    cause = [line for line in error.splitlines() if re.match(r'\w+Error: ', line)][-1]
                    self.assertTrue(cause.startswith(exception + ':'), cause)
                    self.assertRegex(cause, rf'\b{re.escape(named)}\b')


if __name__ == '__main__':
    unittest.main()
