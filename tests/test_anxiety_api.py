"""HTTP tests for the anxiety screening endpoint."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from fastapi import HTTPException

from api import app
from modules.anxiety.classifier import LIMITATIONS


class TestAnxietyApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_valid_input_returns_supported_prediction_and_limitations(self):
        classifier = Mock()
        classifier.analyze.return_value = {
            "category": "Mild Anxiety",
            "limitations": list(LIMITATIONS),
        }
        with patch("modules.anxiety.api.classifier_dependency", return_value=classifier):
            response = self.client.post("/api/anxiety/analyze", json={"responses": [0, 1, 2, 3, 0, 1, 2]})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["category"], "Mild Anxiety")
        self.assertEqual(response.json()["limitations"], list(LIMITATIONS))
        classifier.analyze.assert_called_once_with([0, 1, 2, 3, 0, 1, 2])

    def test_real_model_handles_a_synthetic_http_submission(self):
        response = self.client.post(
            "/api/anxiety/analyze",
            json={"responses": [0, 1, 2, 3, 0, 1, 2]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            response.json()["category"],
            ("Minimal Anxiety", "Mild Anxiety", "Moderate Anxiety", "Severe Anxiety"),
        )
        self.assertIn("not a clinical diagnosis", response.json()["limitations"][0])

    def test_incomplete_and_invalid_values_are_rejected_clearly(self):
        incomplete = self.client.post("/api/anxiety/analyze", json={"responses": [0, 1, 2, 3, 0, 1]})
        invalid_value = self.client.post("/api/anxiety/analyze", json={"responses": [0, 1, 2, 3, 0, 1, 4]})
        boolean_value = self.client.post("/api/anxiety/analyze", json={"responses": [0, 1, 2, 3, 0, 1, True]})

        self.assertEqual(incomplete.status_code, 422)
        self.assertIn("exactly seven integer responses", incomplete.json()["detail"])
        self.assertEqual(invalid_value.status_code, 422)
        self.assertIn("integer from 0 to 3", invalid_value.json()["detail"])
        self.assertEqual(boolean_value.status_code, 422)
        self.assertIn("exactly seven integer responses", boolean_value.json()["detail"])

    def test_extra_fields_are_rejected_without_echoing_submitted_values(self):
        response = self.client.post(
            "/api/anxiety/analyze",
            json={"responses": [0] * 7, "private-sentinel": "private-sentinel"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("private-sentinel", response.text)

    def test_model_unavailable_and_inference_errors_are_sanitized(self):
        with patch(
            "modules.anxiety.api.classifier_dependency",
            side_effect=HTTPException(status_code=503, detail="Anxiety screening is temporarily unavailable."),
        ):
            unavailable = self.client.post("/api/anxiety/analyze", json={"responses": [0] * 7})
        classifier = Mock()
        classifier.analyze.side_effect = RuntimeError("private-sentinel")
        with patch("modules.anxiety.api.classifier_dependency", return_value=classifier):
            failed = self.client.post("/api/anxiety/analyze", json={"responses": [0] * 7})
        self.assertEqual(unavailable.status_code, 503)
        self.assertNotIn("local_models", unavailable.text)
        self.assertEqual(failed.status_code, 500)
        self.assertNotIn("private-sentinel", failed.text)
        self.assertNotIn("Traceback", failed.text)

    def test_anxiety_route_is_registered(self):
        self.assertIn("/api/anxiety/analyze", app.openapi()["paths"])


if __name__ == "__main__":
    unittest.main()
