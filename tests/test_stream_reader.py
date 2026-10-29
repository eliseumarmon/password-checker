"""Reader contract: path and in-memory stream must have identical behavior."""
import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditar_contrasenas_local import read_export


class StreamReaderTests(unittest.TestCase):
    def test_same_rows_from_stringio_and_file(self):
        text = ('name,url,username,password,note\n'
                'Ejemplo,https://example.invalid/login,user,"fake,secret",nota\n')
        with tempfile.TemporaryDirectory() as folder:
            filename = Path(folder) / 'test.csv'
            filename.write_text(text, encoding='utf-8')
            expected = read_export('chrome', filename)
        actual = read_export('chrome', io.StringIO(text, newline=''))
        self.assertEqual(expected, actual)
        self.assertEqual(actual[0].password, 'fake,secret')


if __name__ == '__main__':
    unittest.main()
