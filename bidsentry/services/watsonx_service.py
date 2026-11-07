"""IBM watsonx.ai (Granite) client used for consented, PII-redacted extraction.

The service resolves credentials in one place, records real call telemetry
(model, latency, input/output token counts reported by watsonx) and verifies a
connection by fetching the model specification instead of assuming success.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from bidsentry.config import Settings
from bidsentry.lib.pii import contains_unmasked_pii, mask_text

LOGGER = logging.getLogger("bidsentry.watsonx")
DEFAULT_GRANITE_MODEL = "ibm/granite-3-8b-instruct"


class WatsonxService:
    """Direct access to IBM watsonx.ai foundation models."""

    def __init__(self, settings: Settings):
        self.settings = settings

    # ------------------------------------------------------------ configuration
    @property
    def default_model_id(self) -> str:
        if self.settings.llm_provider == "watsonx" and self.settings.llm_model_name:
            return self.settings.llm_model_name
        return self.settings.watsonx_model_id or DEFAULT_GRANITE_MODEL

    @property
    def api_key(self) -> str:
        """WATSONX_API_KEY wins; LLM_API_KEY is accepted when LLM_PROVIDER=watsonx."""
        if self.settings.watsonx_api_key:
            return self.settings.watsonx_api_key
        return self.settings.llm_api_key if self.settings.llm_provider == "watsonx" else ""

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.settings.watsonx_project_id)

    def status(self) -> dict[str, Any]:
        return {
            "configured": self.is_configured,
            "provider": "ibm_watsonx_ai",
            "model_id": self.default_model_id,
            "watsonx_url": self.settings.watsonx_url,
            "project_id_present": bool(self.settings.watsonx_project_id),
            "selected_for_extraction": self.settings.llm_provider == "watsonx" and not self.settings.langflow_configured,
            "mode": "configured" if self.is_configured else "not_configured",
        }

    def _model(self, params: dict[str, Any] | None = None) -> Any:
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        return ModelInference(
            model_id=self.default_model_id,
            params=params,
            credentials=Credentials(url=self.settings.watsonx_url, api_key=self.api_key),
            project_id=self.settings.watsonx_project_id,
        )

    def test_connection(self) -> dict[str, Any]:
        """Fetch the model specification; this authenticates without generating tokens."""
        if not self.is_configured:
            return {
                "status": "unconfigured",
                "configured": False,
                "model_id": self.default_model_id,
                "message": "Kredensial IBM watsonx.ai belum diatur (WATSONX_API_KEY dan WATSONX_PROJECT_ID).",
            }
        started = time.perf_counter()
        try:
            details = self._model().get_details()
            return {
                "status": "connected",
                "configured": True,
                "verified": "model_details_fetched",
                "model_id": self.default_model_id,
                "model_label": details.get("label") if isinstance(details, dict) else None,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "message": f"Terautentikasi ke IBM watsonx; spesifikasi model {self.default_model_id} berhasil diambil.",
            }
        except Exception as exc:
            return {"status": "error", "configured": True, "model_id": self.default_model_id, "error_type": type(exc).__name__, "message": f"Koneksi gagal: {exc}"}

    # --------------------------------------------------------------- inference
    def generate_json(self, prompt: str, consent: bool, max_tokens: int = 4096) -> dict[str, Any]:
        """Run a consented, already-structured prompt and return text plus telemetry.

        The caller is expected to send PII-masked text; as defence in depth the
        prompt is masked again here before it leaves the server.
        """
        telemetry: dict[str, Any] = {"provider": "watsonx", "model_id": self.default_model_id, "endpoint": f"{self.settings.watsonx_url}/ml/v1/text/generation"}
        if not consent:
            return {"status": "not_requested", "text": None, "message": "Persetujuan pengguna belum diberikan.", "telemetry": telemetry}
        if not self.is_configured:
            return {"status": "unconfigured", "text": None, "message": "Kredensial IBM watsonx.ai belum dikonfigurasi.", "telemetry": telemetry}
        safe_prompt = mask_text(prompt)
        telemetry["pii_detected_after_masking"] = contains_unmasked_pii(safe_prompt)
        started = time.perf_counter()
        try:
            from bidsentry.services.langflow_service import strip_code_fence

            model = self._model({"decoding_method": "greedy", "temperature": 0, "max_new_tokens": max_tokens})
            response = model.generate(prompt=safe_prompt)
            telemetry["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
            results = response.get("results") if isinstance(response, dict) else None
            first = results[0] if isinstance(results, list) and results else {}
            telemetry["input_tokens"] = first.get("input_token_count")
            telemetry["output_tokens"] = first.get("generated_token_count")
            telemetry["stop_reason"] = first.get("stop_reason")
            telemetry["model_id"] = response.get("model_id", self.default_model_id) if isinstance(response, dict) else self.default_model_id
            text = first.get("generated_text")
            if not isinstance(text, str) or not text.strip():
                return {"status": "empty_response", "text": None, "provider": "watsonx", "telemetry": telemetry}
            return {"status": "success", "text": strip_code_fence(text), "provider": "watsonx", "telemetry": telemetry}
        except Exception as exc:
            telemetry["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
            LOGGER.warning("IBM watsonx.ai inference failed: %s", type(exc).__name__)
            return {"status": "provider_error", "text": None, "provider": "watsonx", "error_type": type(exc).__name__, "message": f"Inferensi IBM Granite gagal: {type(exc).__name__}", "telemetry": telemetry}

    def evaluate_preflight_guardrails(
        self,
        document_text: str = "",
        candidate_quotes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Local preflight guardrails: verbatim grounding ratio and pattern-based PII check.

        Cloud watsonx.governance monitoring (drift/bias dashboards) is not
        implemented and is reported as such.
        """
        quotes = candidate_quotes or []
        grounded_count = sum(1 for quote in quotes if quote and document_text and quote in document_text)
        unverified_count = len(quotes) - grounded_count
        return {
            "local_guardrails_status": "ACTIVE_DETERMINISTIC",
            "cloud_watsonx_governance_status": "ENTERPRISE_ROADMAP",  # not implemented in this build
            "model_monitored": self.default_model_id,
            "hallucination_guard": "LEXICAL_EXACT_SUBSTRING_ENFORCED",
            "grounding_check": {
                "quotes_evaluated": len(quotes),
                "verbatim_grounded": grounded_count,
                "unverified_or_rejected": unverified_count,
                "grounding_ratio": round(grounded_count / len(quotes), 4) if quotes else 1.0,
            },
            "pii_scrubbing": {
                "method": "deterministic_pattern_based",
                "unmasked_pii_detected": contains_unmasked_pii(document_text),
                "sanitized_before_remote_inference": True,
            },
        }


__all__ = ["DEFAULT_GRANITE_MODEL", "WatsonxService"]
