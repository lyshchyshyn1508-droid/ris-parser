"""Run with python3 test_parser.py. Tests exercise Python extracted from index.html."""
import re
import unittest
from pathlib import Path

html = Path(__file__).with_name('index.html').read_text(encoding='utf-8')
code = re.search(r'<script type="py">(.*?)</script>', html, re.S).group(1)
ns = {}
exec(code.split('from pyscript import document')[0], ns)
convert, parse, author = ns['convert'], ns['parse_ris'], ns['author_name']

class ParserTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(convert(' ')[0], [])
        self.assertTrue(convert(' ')[1])
    def test_minimal(self):
        self.assertEqual(convert('TY  - JOUR\nTI  - Назва\nER  -')[0], ['Назва.'])
    def test_author_empty(self):
        self.assertEqual(author('Smith, '), 'Smith')
    def test_author_initials(self):
        self.assertEqual(author('Smith, Jane Ann'), 'Smith J. A.')
        self.assertEqual(author('Smith, Jean-Paul'), 'Smith J.-P.')
    def test_organization(self):
        self.assertEqual(author('World Health Organization'), 'World Health Organization')
    def test_no_final_newline(self):
        self.assertEqual(convert('TY  - JOUR\nT1  - Last character')[0], ['Last character.'])
    def test_missing_optional(self):
        result, _ = convert('T1  - Тест')
        self.assertEqual(result, ['Тест.'])
        self.assertNotIn('None', result[0])
    def test_crlf_bom(self):
        self.assertEqual(convert('\ufeffTY  - BOOK\r\nTI  - Книга\r\nER  -')[0], ['Книга.'])
    def test_multiple(self):
        self.assertEqual(convert('TY  - BOOK\nTI  - One\nER  -\nTY  - JOUR\nTI  - Two\nER  -')[0], ['One.', 'Two.'])
    def test_field_reset(self):
        result,_=convert('TY  - JOUR\nTI  - One\nDO  - 10.1/a\nER  -\nTY  - JOUR\nTI  - Two\nER  -')
        self.assertNotIn('10.1/a',result[1])
    def test_continuation(self):
        self.assertEqual(convert('TY  - JOUR\nTI  - Long\n    title\nER  -')[0], ['Long title.'])
    def test_aliases_pages(self):
        result,_=convert('TY  - JOUR\nTI  - Test\nJF  - Journal\nY1  - 2026/01/02\nSP  - 10\nEP  - 20\nER  -')
        self.assertIn('Journal. 2026. С. 10–20.',result[0])
    def test_doi(self):
        result,_=convert('TY  - JOUR\nTI  - Test\nDO  - https://doi.org/10.1234/abc\nER  -')
        self.assertIn('DOI: 10.1234/abc.', result[0])
    def test_bad_line_unknown(self):
        result,warnings=convert('not RIS\nZZ  - ignored')
        self.assertEqual(result,[])
        self.assertGreaterEqual(len(warnings),2)
    def test_missing_er(self):
        records,warnings=parse('TY  - BOOK\nTI  - One\nTY  - BOOK\nTI  - Two')
        self.assertEqual(len(records),2)
        self.assertEqual(sum('немає ER' in w for w in warnings),2)
    def test_no_title(self):
        result,warnings=convert('TY  - JOUR\nER  -')
        self.assertEqual(result,['[Без назви].'])
        self.assertTrue(warnings)
    def test_html_literal(self):
        self.assertIn('<img src=x onerror=alert(1)>',convert('TY  - JOUR\nTI  - <img src=x onerror=alert(1)>\nER  -')[0][0])
        self.assertNotIn('innerHTML',html)

if __name__ == '__main__':
    unittest.main(verbosity=2)
