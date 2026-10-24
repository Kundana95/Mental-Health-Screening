"""HTTP-level tests for the local assessment API."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import MAX_REQUEST_BODY_BYTES, app
from modules.assessment_result import (
    CONTEXT_OPTIONS,
    build_unified_assessment_result,
)


def completed_payload():
    """Create synthetic, complete answers without printing assessment data."""
    context_answers = {key: choices[0] for key, choices in CONTEXT_OPTIONS.items()}
    context_answers["age_group"] = "Prefer not to say"
    context_answers["tobacco_use"] = "Prefer not to say"
    context_answers["alcohol_frequency"] = "Prefer not to say"
    context_answers["emotional_support"] = "Prefer not to say"
    return {
        "phq9_responses": [0, 1, 2, 0, 1, 0, 2, 0, 1],
        "gad7_responses": [1, 0, 2, 1, 0, 1, 0],
        "context_answers": context_answers,
    }


class TestDepressionAssessmentApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_completed_submission_scores_and_preserves_context_and_safety(self):
        payload = completed_payload()

        with patch(
            "api.build_unified_assessment_result",
            wraps=build_unified_assessment_result,
        ) as builder:
            response = self.client.post("/api/depression/submit", json=payload)

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result, {
            "status": "received",
            "message": "Your responses were received.",
        })
        builder.assert_called_once_with(
            payload["phq9_responses"],
            payload["gad7_responses"],
            payload["context_answers"],
        )
        self.assertNotIn("responses", result)
        self.assertNotIn("total_score", result)
        self.assertNotIn("Prefer not to say", response.text)

    def test_incomplete_submission_is_rejected(self):
        payload = completed_payload()
        payload["gad7_responses"][3] = None

        response = self.client.post("/api/depression/submit", json=payload)

        self.assertEqual(response.status_code, 422)
        self.assertIn("Answer every questionnaire item", response.json()["detail"])

    def test_invalid_submission_is_rejected(self):
        payload = completed_payload()
        payload["phq9_responses"][0] = 4

        response = self.client.post("/api/depression/submit", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_boolean_response_is_rejected_as_not_an_integer_answer(self):
        payload = completed_payload()
        payload["gad7_responses"][0] = True

        response = self.client.post("/api/depression/submit", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_missing_fields_unexpected_fields_and_wrong_json_types_are_sanitized(self):
        payload = completed_payload()
        missing_field = dict(payload)
        del missing_field["context_answers"]
        extra_field = dict(payload, unexpected="sensitive-sentinel")
        wrong_type = dict(payload, phq9_responses="sensitive-sentinel")

        for invalid_payload in (missing_field, extra_field, wrong_type):
            with self.subTest(case="invalid request shape"):
                response = self.client.post("/api/depression/submit", json=invalid_payload)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("sensitive-sentinel", response.text)
                self.assertNotIn("input", response.text)

    def test_malformed_json_returns_a_sanitized_validation_error(self):
        response = self.client.post(
            "/api/depression/submit",
            content=b'{"phq9_responses":',
            headers={"content-type": "application/json"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["detail"],
            "Invalid assessment submission. Please review your answers.",
        )

    def test_invalid_context_choice_is_rejected_without_echoing_value(self):
        payload = completed_payload()
        payload["context_answers"]["sleep_quality"] = "private-answer-sentinel"

        response = self.client.post("/api/depression/submit", json=payload)

        self.assertEqual(response.status_code, 422)
        self.assertNotIn("private-answer-sentinel", response.text)

    def test_oversized_body_is_rejected(self):
        response = self.client.post(
            "/api/depression/submit",
            content=b"x" * (MAX_REQUEST_BODY_BYTES + 1),
            headers={"content-type": "application/json"},
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["detail"], "Request body is too large.")

    def test_unexpected_processing_error_returns_generic_message_without_logging_input(self):
        payload = completed_payload()
        client = TestClient(app, raise_server_exceptions=False)

        with self.assertLogs(level="INFO") as captured_logs:
            with patch(
                "api.build_unified_assessment_result",
                side_effect=RuntimeError("private-answer-sentinel"),
            ):
                response = client.post("/api/depression/submit", json=payload)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"],
            "The assessment could not be processed. Please try again.",
        )
        self.assertNotIn("private-answer-sentinel", response.text)
        self.assertNotIn("Traceback", response.text)
        self.assertNotIn("private-answer-sentinel", "\n".join(captured_logs.output))

    def test_unexpected_validation_error_is_sanitized(self):
        client = TestClient(app, raise_server_exceptions=False)

        with self.assertLogs(level="INFO") as captured_logs:
            with patch(
                "api.validate_unified_assessment_submission",
                side_effect=RuntimeError("private-answer-sentinel"),
            ):
                response = client.post(
                    "/api/depression/submit",
                    json=completed_payload(),
                )

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private-answer-sentinel", response.text)
        self.assertNotIn("private-answer-sentinel", "\n".join(captured_logs.output))

    def test_only_the_submission_route_is_exposed(self):
        paths = [route.path for route in app.routes]
        self.assertEqual(paths, ["/api/depression/submit"])

    def test_untrusted_host_is_rejected(self):
        response = self.client.get(
            "/api/depression/submit",
            headers={"host": "untrusted.example"},
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
