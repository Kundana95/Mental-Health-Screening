"""Schizophrenia API validation, error isolation, and privacy behavior."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api import MAX_REQUEST_BODY_BYTES, app
from modules.schizophrenia.classifier import (
    CATEGORIES, LIMITATIONS, MODEL_ID, InvalidTextError, ModelsUnavailableError,
)


class TestSchizophreniaApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        self.loader = patch("modules.schizophrenia.api.get_classifier")
        self.get_classifier = self.loader.start()
        self.addCleanup(self.loader.stop)
        self.classifier = Mock()
        self.get_classifier.return_value = self.classifier
        self.classifier.analyze.return_value = {
            "category": "general_community", "model_id": MODEL_ID,
            "limitations": list(LIMITATIONS),
        }

    def test_each_category_returns_only_documented_fields(self):
        for category in CATEGORIES.values():
            self.classifier.analyze.return_value["category"] = category
            response = self.client.post("/api/schizophrenia/analyze", json={"text": "private-sentinel"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), self.classifier.analyze.return_value)
            self.assertNotIn("private-sentinel", response.text)

    def test_invalid_bodies_rejected_without_loading_models_or_echoing_text(self):
        bodies = [{}, None, [], "private-sentinel", {"text": None}, {"text": 1},
                  {"text": True}, {"text": []}, {"text": ""}, {"text": " \n\t"},
                  {"text": "a" * 4001}, {"text": "private-sentinel", "extra": True}]
        for body in bodies:
            with self.subTest(body_type=type(body).__name__):
                response = self.client.post("/api/schizophrenia/analyze", json=body)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("private-sentinel", response.text)
        self.get_classifier.assert_not_called()

    def test_character_limit_boundary(self):
        response = self.client.post("/api/schizophrenia/analyze", json={"text": "a" * 4000})
        self.assertEqual(response.status_code, 200)

    def test_malformed_json_is_sanitized(self):
        response = self.client.post("/api/schizophrenia/analyze", content='{"text":"private-sentinel',
                                    headers={"content-type": "application/json"})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("private-sentinel", response.text)

    def test_no_recognized_tokens_returns_422(self):
        self.classifier.analyze.side_effect = InvalidTextError("No recognized words were found. Please provide different text.")
        response = self.client.post("/api/schizophrenia/analyze", json={"text": "12345"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("No recognized words", response.json()["detail"])

    def test_unavailable_model_returns_503_without_internal_details(self):
        for error in (ModelsUnavailableError("private-sentinel"), ImportError("private-sentinel")):
            self.get_classifier.side_effect = error
            response = self.client.post("/api/schizophrenia/analyze", json={"text": "doctor"})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("private-sentinel", response.text)

    def test_processing_errors_and_malformed_results_are_sanitized_without_input_logging(self):
        for result in (RuntimeError("private-sentinel"), {"category": "private-sentinel"}):
            self.classifier.analyze.side_effect = result if isinstance(result, Exception) else None
            self.classifier.analyze.return_value = result
            with self.assertLogs(level="INFO") as logs:
                response = self.client.post("/api/schizophrenia/analyze", json={"text": "private-sentinel"})
            self.assertEqual(response.status_code, 500)
            self.assertNotIn("private-sentinel", response.text)
            self.assertNotIn("private-sentinel", "\n".join(logs.output))

    def test_global_request_limits_and_host_restrictions_apply(self):
        response = self.client.post("/api/schizophrenia/analyze", content=b"x" * (MAX_REQUEST_BODY_BYTES + 1))
        self.assertEqual(response.status_code, 413)
        response = self.client.post("/api/schizophrenia/analyze", json={"text": "doctor"},
                                    headers={"host": "untrusted.example"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
