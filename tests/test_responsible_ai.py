"""Unit tests validating Responsible AI safeguards, PII redaction, and bias protection."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest
from decimal import Decimal

from bidsentry.audits.default_predictor import predict_default_risk
from bidsentry.config import Settings
from bidsentry.forensics.collusion import compare_proposals
from bidsentry.lib.pii import mask_text, mask_value
from bidsentry.schemas.comprehensive import DefaultRiskInput
from bidsentry.services.dispatch_service import DispatchService
from bidsentry.services.watsonx_service import WatsonxService


class ResponsibleAiTests(unittest.TestCase):
    def test_pii_masking_comprehensive(self):
        raw_text = (
            "Kontak PPK: budi@kemenkes.go.id, telp: 081234567890. "
            "Penyedia PT Maju Bersama, NPWP: 01.234.567.8-901.000, "
            "NIK Direktur: 3171012345670001, Rekening Bank: 1234567890123."
        )
        masked = mask_text(raw_text)

        self.assertNotIn("budi@kemenkes.go.id", masked)
        self.assertIn("[EMAIL-REDACTED]", masked)
        self.assertNotIn("081234567890", masked)
        self.assertIn("[PHONE-REDACTED]", masked)
        self.assertNotIn("01.234.567.8-901.000", masked)
        self.assertIn("[NPWP-REDACTED]", masked)
        self.assertNotIn("3171012345670001", masked)
        self.assertIn("[NIK-REDACTED]", masked)
        self.assertNotIn("1234567890123", masked)
        self.assertIn("[ACCOUNT-REDACTED]", masked)

    def test_watsonx_service_unconfigured_fallback_and_guardrails(self):
        settings = Settings.from_environment()
        service = WatsonxService(settings)
        status = service.status()
        self.assertEqual(status["provider"], "ibm_watsonx_ai")
        self.assertEqual(status["model_id"], "ibm/granite-3-8b-instruct")

        # Test governance guardrails simulation
        gov = service.evaluate_governance_guardrails(["MATH_MISMATCH", "HARGA_TIMPANG_HIGH"])
        self.assertEqual(gov["watsonx_governance_status"], "MONITORED")
        self.assertEqual(gov["hallucination_guard"], "LEXICAL_EXACT_SUBSTRING_ENFORCED")
        self.assertEqual(gov["pii_leakage_risk"], "ZERO_LOCAL_MASKING")

        # Without consent, extraction returns not_requested
        res_no_consent = service.generate_grounded_extraction("Doc text", consent=False)
        self.assertEqual(res_no_consent["status"], "not_requested")

    def test_collusion_legal_caveat_compliance(self):
        vendors = [
            {"vendor_id": "V1", "vendor_name": "PT Alpha", "technical_proposal_text": "Spesifikasi server cloud 64 core 256GB RAM " * 20},
            {"vendor_id": "V2", "vendor_name": "PT Beta", "technical_proposal_text": "Spesifikasi server cloud 64 core 256GB RAM " * 20},
        ]
        result = compare_proposals(vendors)
        self.assertEqual(result["status"], "screened")
        self.assertIn("legal_notice", result)
        self.assertIn("Pasal 22 UU 5/1999", result["comparisons"][0]["legal_caveat"])
        # Finding type is screening signal, not a definitive charge
        self.assertEqual(result["comparisons"][0]["screening_result"], "HIGH_SIMILARITY_REVIEW")

    def test_default_predictor_umkm_bias_protection(self):
        input_data = DefaultRiskInput(
            tender_value=Decimal("5000000000"),  # 5 Miliar (UMKM threshold package)
            skn_amount=Decimal("3000000000"),
            working_capital_amount=Decimal("1000000000"),
        )
        res = predict_default_risk(input_data)
        self.assertEqual(res["status"], "screening_score")
        self.assertIn("umkm_bias_protection", res)
        self.assertIn("Pasal 65", res["umkm_bias_protection"])


if __name__ == "__main__":
    unittest.main()
