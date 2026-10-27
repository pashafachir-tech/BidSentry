from __future__ import annotations

import json
import os
import unittest
from dataclasses import replace
from unittest.mock import Mock, patch

import composio_dispatcher
from bidsentry.config import Settings
from bidsentry.services.langflow_service import LangflowService


class FakeResponse:
    def __init__(self, body: dict):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit: int = -1) -> bytes:
        return self.body


class IntegrationAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings.from_environment()

    @patch("composio_dispatcher.urllib.request.urlopen")
    @patch.dict(os.environ, {"COMPOSIO_USER_ID": "bid-sentry-test-user", "COMPOSIO_API_KEY": "test-project-key"})
    def test_composio_executes_v31_tool_schema(self, urlopen: Mock) -> None:
        urlopen.return_value = FakeResponse({"successful": True, "data": {"documentId": "doc-1"}})
        result = composio_dispatcher._post_composio(
            "GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN",
            "test-project-key",
            {"title": "Audit", "markdown_text": "# Evidence"},
        )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://backend.composio.dev/api/v3.1/tools/execute/GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("X-api-key"), "test-project-key")
        self.assertEqual(payload["user_id"], "bid-sentry-test-user")
        self.assertEqual(payload["version"], "latest")
        self.assertEqual(payload["arguments"]["markdown_text"], "# Evidence")
        self.assertEqual(result["successful"], True)

    @patch("composio_dispatcher._post_composio")
    @patch.dict(os.environ, {"COMPOSIO_API_KEY": "test-project-key"})
    def test_action_builders_use_current_google_tool_parameters(self, post: Mock) -> None:
        post.side_effect = [
            {"successful": True, "data": {"documentId": "doc-1"}},
            {"successful": True, "data": {"htmlLink": "https://calendar.google.com/event/1"}},
        ]
        result = composio_dispatcher.dispatch_tender_workspace({
            "nama_paket": "Paket uji",
        })

        calls = post.call_args_list
        self.assertEqual(calls[0].args[0], "GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN")
        self.assertIn("markdown_text", calls[0].args[2])
        self.assertEqual(calls[1].args[0], "GOOGLECALENDAR_CREATE_EVENT")
        calendar_args = calls[1].args[2]
        self.assertIn("start_datetime", calendar_args)
        self.assertTrue(calendar_args["start_datetime"].endswith("Z"))
        self.assertEqual(calendar_args["event_duration_minutes"], 30)
        gmail_args = composio_dispatcher._build_gmail_params({"email_penerima": "reviewer@example.test"})
        self.assertEqual(gmail_args["recipient_email"], "reviewer@example.test")
        self.assertNotIn("to", gmail_args)
        self.assertEqual(result["status"], "success")

    @patch("composio_dispatcher.urllib.request.urlopen")
    def test_composio_connection_test_only_lists_account_metadata(self, urlopen: Mock) -> None:
        configured = replace(
            self.settings,
            composio_api_key="test-project-key",
            composio_user_id="bid-sentry-test-user",
            composio_base_url="https://backend.composio.dev/api/v3.1/tools/execute/{action}",
        )
        urlopen.return_value = FakeResponse({
            "items": [
                {"toolkit": {"slug": "googledocs"}, "status": "ACTIVE"},
                {"toolkit": {"slug": "gmail"}, "status": "INITIALIZING"},
            ],
            "next_cursor": None,
        })

        result = composio_dispatcher.test_composio_connection(configured)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIn("/api/v3.1/connected_accounts?", request.full_url)
        self.assertIn("user_ids=bid-sentry-test-user", request.full_url)
        self.assertEqual(result["status"], "connected")
        self.assertEqual(result["active_account_count"], 1)
        self.assertEqual(result["linked_toolkits"], ["GOOGLEDOCS"])

    @patch("composio_dispatcher.urllib.request.urlopen")
    def test_composio_test_skips_network_when_key_is_missing(self, urlopen: Mock) -> None:
        result = composio_dispatcher.test_composio_connection(replace(self.settings, composio_api_key=""))
        self.assertEqual(result["status"], "not_configured")
        urlopen.assert_not_called()

    @patch("bidsentry.services.langflow_service.urllib.request.urlopen")
    def test_langflow_connection_test_reads_flow_without_running_it(self, urlopen: Mock) -> None:
        configured = replace(
            self.settings,
            langflow_url="http://localhost:7860",
            langflow_flow_id="flow/for-test",
            langflow_api_key="langflow-test-key",
        )
        urlopen.return_value = FakeResponse({"id": "flow/for-test", "name": "Tender extraction"})

        result = LangflowService(configured).test_connection()

        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, "http://localhost:7860/api/v1/flows/flow%2Ffor-test")
        self.assertEqual(request.get_header("X-api-key"), "langflow-test-key")
        self.assertEqual(result["status"], "connected")
        self.assertEqual(result["flow_name"], "Tender extraction")


if __name__ == "__main__":
    unittest.main()
