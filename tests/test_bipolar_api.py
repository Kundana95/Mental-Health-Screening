"""API tests use only synthetic inputs and mocked model inference."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api import app
from modules.bipolar.classifier import (
    LIMITATIONS,
    SUPPORTED_CATEGORIES,
    BipolarModelUnavailableError,
)


def valid_payload():
    return {
        "Sadness": "Seldom",
        "Euphoric": "Sometimes",
        "Exhausted": "Usually",
        "Sleep dissorder": "Most-Often",
        "Mood Swing": "YES",
        "Aggressive Response": "NO",
        "Admit Mistakes": "YES",
        "Overthinking": "NO",
        "Concentration": 4,
        "Optimisim": 5,
    }


class TestBipolarApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        self.loader = patch("modules.bipolar.api.get_classifier")
        self.get_classifier = self.loader.start()
        self.addCleanup(self.loader.stop)
        self.classifier = Mock()
        self.get_classifier.return_value = self.classifier
        self.classifier.analyze.return_value = {
            "category": "Bipolar Type 1",
            "limitations": list(LIMITATIONS),
        }

    def test_each_supported_category_returns_safe_documented_fields(self):
        for category in SUPPORTED_CATEGORIES:
            with self.subTest(category=category):
                self.classifier.analyze.return_value = {
                    "category": category,
                    "limitations": list(LIMITATIONS),
                }
                self.classifier.analyze.side_effect = None
                response = self.client.post("/api/bipolar/analyze", json=valid_payload())
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body["category"], category)
                self.assertEqual(set(body), {"category", "message", "limitations"})
                self.assertNotIn("Bipolar disorder is absent", body["message"])
                self.assertNotIn("Sadness", response.text)
                self.assertNotIn("Concentration", response.text)
                self.assertTrue(any("small dataset" in item for item in body["limitations"]))

    def test_valid_input_passes_ordered_answers_to_existing_classifier(self):
        self.client.post("/api/bipolar/analyze", json=valid_payload())
        answers = self.classifier.analyze.call_args.args[0]
        self.assertEqual(list(answers), [
            "Sadness", "Euphoric", "Exhausted", "Sleep dissorder", "Mood Swing",
            "Aggressive Response", "Admit Mistakes", "Overthinking", "Concentration", "Optimisim",
        ])

    def test_missing_unexpected_and_wrongly_typed_fields_are_rejected_safely(self):
        payloads = []
        missing = valid_payload()
        missing.pop("Sadness")
        payloads.append(missing)
        unexpected = valid_payload()
        unexpected["extra"] = "private-sentinel"
        payloads.append(unexpected)
        for feature, value in (("Mood Swing", "sometimes"), ("Concentration", True),
                               ("Concentration", 4.0), ("Optimisim", "5")):
            invalid = valid_payload()
            invalid[feature] = value
            payloads.append(invalid)

        for payload in payloads:
            response = self.client.post("/api/bipolar/analyze", json=payload)
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("private-sentinel", response.text)

    def test_numeric_bounds_and_invalid_choices_are_rejected_before_model_load(self):
        for feature, value in (("Concentration", 0), ("Concentration", 9),
                               ("Optimisim", 0), ("Optimisim", 10),
                               ("Sadness", "Rarely")):
            with self.subTest(feature=feature, value=value):
                payload = valid_payload()
                payload[feature] = value
                response = self.client.post("/api/bipolar/analyze", json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn(str(value), response.text)
        self.get_classifier.assert_not_called()

    def test_malformed_json_is_sanitized(self):
        response = self.client.post(
            "/api/bipolar/analyze",
            content='{"Sadness":"private-sentinel',
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("private-sentinel", response.text)
        self.get_classifier.assert_not_called()

    def test_unavailable_model_and_inference_errors_are_sanitized(self):
        self.get_classifier.side_effect = BipolarModelUnavailableError("C:/private/model path")
        response = self.client.post("/api/bipolar/analyze", json=valid_payload())
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", response.text)

        self.get_classifier.side_effect = None
        self.get_classifier.return_value = self.classifier
        self.classifier.analyze.side_effect = RuntimeError("private-sentinel")
        with self.assertLogs(level="INFO") as logs:
            response = self.client.post("/api/bipolar/analyze", json=valid_payload())
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private-sentinel", response.text)
        self.assertNotIn("private-sentinel", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
