"""Mandatory dependencies fail loudly: a missing package must never turn the crypto or API tests into skips."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent

# Discovers one test module, as CI does, in a fresh interpreter where a mandatory package cannot be imported.
PROBE = '''
import io, json, sys, unittest
sys.modules[sys.argv[1]] = None
suite = unittest.defaultTestLoader.discover(sys.argv[3], pattern=sys.argv[2] + '.py')
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(json.dumps({'errors': [text for _, text in result.errors], 'skipped': len(result.skipped)}))
'''


class RequiredDependencyTests(unittest.TestCase):
    def outcome_without(self, package, module):
        completed = subprocess.run([sys.executable, '-c', PROBE, package, module, str(TESTS)],
                                   capture_output=True, text=True, timeout=120, check=True)
        return json.loads(completed.stdout.strip().splitlines()[-1])

    def test_a_missing_mandatory_dependency_is_an_error_not_a_skip(self):
        for package, module in [('cryptography', 'test_sessions'), ('argon2', 'test_sessions'),
                                ('cryptography', 'test_session_limits'), ('fastapi', 'test_api'),
                                ('httpx', 'test_api')]:
            with self.subTest(package=package, module=module):
                outcome = self.outcome_without(package, module)
                self.assertEqual(outcome['skipped'], 0)
                self.assertTrue(outcome['errors'])
                # Each error is caused by the blocked package, not by an unrelated collection problem.
                for error in outcome['errors']:
                    self.assertIn(package, error)


if __name__ == '__main__':
    unittest.main()
