import copy
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from informe import InputError, validate, html_report, waiting_text, main

EXAMPLE=Path(__file__).resolve().parents[1]/'examples'/'causa_demo.json'


class InformeTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(EXAMPLE.read_text(encoding='utf-8'))

    def test_example_and_elapsed_days(self):
        validate(self.data)
        self.assertIn('11 días corridos',waiting_text(self.data))

    def test_impossible_and_future_dates(self):
        for invalid in ['2026-02-30','2026-06-01','15/05/2026']:
            data=copy.deepcopy(self.data);data['events'][0]['date']=invalid
            with self.assertRaises(InputError):validate(data)

    def test_source_integrity(self):
        self.data['events'][0]['source_id']='missing'
        with self.assertRaises(InputError):validate(self.data)

    def test_unsafe_source_url(self):
        self.data['sources'][0]['url']='javascript:alert(1)'
        with self.assertRaises(InputError):validate(self.data)

    def test_html_is_escaped_and_events_sorted(self):
        self.data['case']['summary']='<script>alert("x")</script>'
        self.data['events'].reverse()
        html=html_report(validate(self.data))
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertLess(html.index('Ingreso de demanda'),html.index('Citación para oír sentencia'))

    def test_draft_and_validated_review(self):
        self.assertIn('BORRADOR',html_report(self.data))
        self.data['case']['review_status']='validated'
        with self.assertRaises(InputError):validate(self.data)
        self.data['case'].update(reviewed_by='Profesional de ejemplo',reviewed_at='2026-05-15')
        self.assertIn('REVISADO por',html_report(validate(self.data)))

    def test_generate_html_and_prevent_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=[str(EXAMPLE),'--format','html','--output',tmp]
            self.assertEqual(0,main(args))
            files=list(Path(tmp).glob('*.html'))
            self.assertEqual(1,len(files))
            self.assertEqual(2,main(args))
            self.assertEqual(0,main(args+['--overwrite']))

    def test_pdf_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(0,main([str(EXAMPLE),'--format','pdf','--output',tmp]))
            pdf=next(Path(tmp).glob('*.pdf'))
            self.assertTrue(pdf.read_bytes().startswith(b'%PDF-'))


if __name__=='__main__':unittest.main()
