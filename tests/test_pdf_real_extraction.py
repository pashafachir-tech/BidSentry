"""Tests validating extraction and deterministic evaluation on real multi-page PDF documents."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest
from bidsentry.services.document_extraction_service import DocumentExtractionService
from bidsentry.evaluators.engine import EvaluationEngine, EvaluationRequest

PDF_DIR = ROOT / "data" / "sample_tenders" / "pdf_tenders"


class RealPdfExtractionTests(unittest.TestCase):
    def setUp(self):
        self.extractor = DocumentExtractionService()
        self.engine = EvaluationEngine()

    def test_extract_multipage_rab_pdf(self):
        pdf_path = PDF_DIR / "paket_konstruksi_rab_kompleks.pdf"
        self.assertTrue(pdf_path.is_file(), f"File {pdf_path} not found")
        content = pdf_path.read_bytes()

        result = self.extractor.extract(pdf_path.name, content)
        self.assertIn("filename", result)
        self.assertIn("text", result)
        text = result["text"]

        # Assert key table lines extracted across pages
        self.assertIn("Mobilisasi dan Demobilisasi", text)
        self.assertIn("Galian Saluran Drainase", text)
        self.assertIn("Lapis Pondasi Agregat", text)
        self.assertIn("Laston Lapis Aus (AC-WC)", text)
        self.assertIn("10.238.418.000", text)
        self.assertGreater(result["characters"], 500)

    def test_evaluate_extracted_kak_pdf_catches_fatal_flaws(self):
        pdf_path = PDF_DIR / "paket_pengadaan_it_server_kak.pdf"
        self.assertTrue(pdf_path.is_file(), f"File {pdf_path} not found")
        content = pdf_path.read_bytes()

        result = self.extractor.extract(pdf_path.name, content)
        text = result["text"]

        # Run evaluation on extracted PDF text
        request = EvaluationRequest(
            package_name="Pengadaan Server Data Center",
            dok_pemilihan=text,
            pustaka="",
        )
        eval_res = self.engine.evaluate(request)

        # Must flag NO-GO due to vendor lock-in, compressed timeline, and uncapped penalty
        self.assertEqual(eval_res["verdict"], "NO-GO")
        finding_ids = {f["id"] for f in eval_res["findings"]}
        self.assertTrue("SPEC-LOCKIN-CPU" in finding_ids or "SPEC-LOCKIN-MGMT" in finding_ids)
        self.assertIn("CON-PENALTY", finding_ids)
        self.assertIn("PROC-TIMELINE-COMPRESSED", finding_ids)


if __name__ == "__main__":
    unittest.main()
