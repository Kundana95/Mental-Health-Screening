import json
import unittest

from modules.assessment_result import build_assessment_result


class TestBuildAssessmentResult(unittest.TestCase):
    def test_builds_phq9_result_with_safety_flag(self):
        result = build_assessment_result(
            "PHQ-9",
            {"total_score": 1, "severity": "Minimal", "safety_flag": True},
        )

        self.assertEqual(result["questionnaire_id"], "PHQ-9")
        self.assertEqual(result["total_score"], 1)
        self.assertEqual(result["severity"], "Minimal")
        self.assertEqual(result["safety_flags"], {"question_9": True})
        self.assertEqual(result["completion_status"], "complete")
        self.assertEqual(result["demographics"], {})
        self.assertIn("not a diagnosis", result["limitations"][0].lower())

    def test_builds_result_for_questionnaire_without_safety_flag(self):
        result = build_assessment_result(
            "GAD-7", {"total_score": 7, "severity": "Mild"}
        )
        self.assertEqual(result["questionnaire_id"], "GAD-7")
        self.assertEqual(result["total_score"], 7)
        self.assertEqual(result["severity"], "Mild")
        self.assertEqual(result["safety_flags"], {})
        self.assertEqual(result["completion_status"], "complete")

    def test_preserves_named_safety_flags_for_future_questionnaires(self):
        result = build_assessment_result(
            "FUTURE-TOOL",
            {
                "total_score": 3,
                "severity": "Low",
                "safety_flags": {"follow_up_needed": True},
            },
        )
        self.assertEqual(result["safety_flags"], {"follow_up_needed": True})

    def test_keeps_optional_demographics_separate(self):
        result = build_assessment_result(
            "GENERIC",
            {"total_score": 8, "severity": "Subthreshold insomnia"},
            demographics={"age_group": "18-24", "gender": "not specified"},
        )
        self.assertEqual(result["demographics"]["age_group"], "18-24")
        self.assertNotIn("age_group", result)
        self.assertNotIn("name", result)
        self.assertNotIn("email", result)

    def test_result_serializes_to_json(self):
        result = build_assessment_result(
            "PHQ-9", {"total_score": 0, "severity": "Minimal", "safety_flag": False}
        )
        serialized = json.dumps(result)
        decoded = json.loads(serialized)
        self.assertEqual(decoded, result)

    def test_includes_optional_context_and_preserves_skips(self):
        context = {
            "age_group": None,
            "current_status": "Prefer not to say",
            "sleep_duration": "7–8 hours",
            "sleep_quality": None,
            "stress_level": "Moderate",
            "physical_activity": None,
            "tobacco_use": "No",
            "alcohol_frequency": "Prefer not to say",
            "emotional_support": "Often",
        }
        result = build_assessment_result(
            "PHQ-9",
            {"total_score": 6, "severity": "Mild", "safety_flag": False},
            context=context,
        )

        decoded = json.loads(json.dumps(result))
        self.assertEqual(decoded["context"], context)
        self.assertIsNone(decoded["context"]["age_group"])
        self.assertEqual(decoded["context"]["current_status"], "Prefer not to say")
        self.assertEqual(decoded["total_score"], 6)
        self.assertNotIn("context_score", decoded)

    def test_context_defaults_to_empty_object(self):
        result = build_assessment_result(
            "GAD-7", {"total_score": 2, "severity": "Minimal"}
        )
        self.assertEqual(result["context"], {})

    def test_rejects_non_json_serializable_data(self):
        with self.assertRaisesRegex(ValueError, "JSON-serializable"):
            build_assessment_result(
                "PHQ-9",
                {"total_score": 0, "severity": "Minimal"},
                demographics={"extra": object()},
            )

    def test_rejects_incomplete_score_result(self):
        with self.assertRaisesRegex(ValueError, "total_score and severity"):
            build_assessment_result("PHQ-9", {"total_score": 0})


if __name__ == "__main__":
    unittest.main()
