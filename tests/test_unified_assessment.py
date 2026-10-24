import json
import unittest

from modules.assessment_result import (
    CONTEXT_OPTIONS,
    build_unified_assessment_result,
    validate_unified_assessment_submission,
)
from modules.depression.gad7 import calculate_gad7_score
from modules.depression.phq9 import calculate_phq9_score


class TestBuildUnifiedAssessmentResult(unittest.TestCase):
    def test_submission_validation_rejects_incomplete_answers(self):
        complete_context = {key: choices[0] for key, choices in CONTEXT_OPTIONS.items()}
        with self.assertRaisesRegex(ValueError, "every questionnaire item"):
            validate_unified_assessment_submission(
                [0] * 8 + [None], [0] * 7, complete_context
            )
        with self.assertRaisesRegex(ValueError, "every context question"):
            validate_unified_assessment_submission([0] * 9, [0] * 7, {})
        incomplete_context = dict(complete_context)
        incomplete_context["sleep_quality"] = None
        with self.assertRaisesRegex(ValueError, "every context question"):
            validate_unified_assessment_submission(
                [0] * 9, [0] * 7, incomplete_context
            )
        extra_context = dict(complete_context, unexpected="value")
        with self.assertRaisesRegex(ValueError, "every context question"):
            validate_unified_assessment_submission(
                [0] * 9, [0] * 7, extra_context
            )

    def test_submission_validation_accepts_complete_answers(self):
        complete_context = {key: choices[0] for key, choices in CONTEXT_OPTIONS.items()}
        self.assertTrue(
            validate_unified_assessment_submission(
                [0] * 9, [0] * 7, complete_context
            )
        )

    def test_prefer_not_to_say_is_a_valid_complete_answer(self):
        complete_context = {key: choices[0] for key, choices in CONTEXT_OPTIONS.items()}
        complete_context["age_group"] = "Prefer not to say"
        complete_context["tobacco_use"] = "Prefer not to say"
        complete_context["alcohol_frequency"] = "Prefer not to say"
        complete_context["emotional_support"] = "Prefer not to say"
        self.assertTrue(
            validate_unified_assessment_submission(
                [0] * 9, [0] * 7, complete_context
            )
        )

    def test_scores_questionnaires_separately_and_serializes(self):
        phq9_responses = [1] * 9
        gad7_responses = [1] * 7
        result = build_unified_assessment_result(
            phq9_responses,
            gad7_responses,
            {"age_group": "18–24", "tobacco_use": "Prefer not to say"},
        )

        self.assertEqual(result["completion_status"], "complete")
        self.assertEqual(result["questionnaire_results"]["PHQ-9"]["total_score"], 9)
        self.assertEqual(result["questionnaire_results"]["PHQ-9"]["severity"], "Mild")
        self.assertEqual(result["questionnaire_results"]["GAD-7"]["total_score"], 7)
        self.assertEqual(result["questionnaire_results"]["GAD-7"]["severity"], "Mild")
        self.assertNotIn("total_score", result)
        self.assertEqual(result["context"]["tobacco_use"], "Prefer not to say")
        self.assertEqual(result["safety_flags"]["PHQ-9"]["question_9"], True)
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_unified_scores_match_individual_scoring_functions(self):
        phq9_responses = [0, 1, 2, 1, 0, 2, 1, 0, 1]
        gad7_responses = [2, 1, 0, 2, 1, 0, 1]
        result = build_unified_assessment_result(
            phq9_responses,
            gad7_responses,
        )

        phq9_result = result["questionnaire_results"]["PHQ-9"]
        gad7_result = result["questionnaire_results"]["GAD-7"]
        expected_phq9 = calculate_phq9_score(phq9_responses)
        expected_gad7 = calculate_gad7_score(gad7_responses)
        self.assertEqual(phq9_result["total_score"], expected_phq9["total_score"])
        self.assertEqual(phq9_result["severity"], expected_phq9["severity"])
        self.assertEqual(gad7_result["total_score"], expected_gad7["total_score"])
        self.assertEqual(gad7_result["severity"], expected_gad7["severity"])
        self.assertEqual(result["safety_flags"]["PHQ-9"]["question_9"], expected_phq9["safety_flag"])

    def test_unanswered_items_remain_null_and_prevent_scoring(self):
        phq9_responses = [0] * 8 + [None]
        gad7_responses = [None, 0, 0, 0, 0, 0, 0]
        result = build_unified_assessment_result(phq9_responses, gad7_responses)

        phq9 = result["questionnaire_results"]["PHQ-9"]
        gad7 = result["questionnaire_results"]["GAD-7"]
        self.assertIsNone(phq9["responses"][8])
        self.assertIsNone(phq9["total_score"])
        self.assertIsNone(phq9["severity"])
        self.assertEqual(phq9["completion_status"], "incomplete")
        self.assertIsNone(gad7["total_score"])
        self.assertEqual(gad7["completion_status"], "incomplete")
        self.assertEqual(result["completion_status"], "incomplete")
        self.assertIsNone(result["safety_flags"]["PHQ-9"]["question_9"])
        self.assertTrue(all(value is None for value in result["context"].values()))

    def test_complete_questionnaire_scores_when_the_other_is_incomplete(self):
        result = build_unified_assessment_result([2] * 9, [0] * 6 + [None])

        phq9 = result["questionnaire_results"]["PHQ-9"]
        gad7 = result["questionnaire_results"]["GAD-7"]
        self.assertEqual(phq9["total_score"], 18)
        self.assertEqual(phq9["severity"], "Moderately severe")
        self.assertIsNone(gad7["total_score"])
        self.assertEqual(gad7["completion_status"], "incomplete")

    def test_positive_question_nine_sets_safety_flag_even_if_score_is_incomplete(self):
        phq9_responses = [None] * 8 + [1]
        result = build_unified_assessment_result(phq9_responses, [None] * 7)

        self.assertIsNone(result["questionnaire_results"]["PHQ-9"]["total_score"])
        self.assertTrue(result["safety_flags"]["PHQ-9"]["question_9"])

    def test_invalid_partial_answers_are_rejected(self):
        invalid_answers = [0] * 8 + [1.5]
        with self.assertRaisesRegex(ValueError, "PHQ-9 response 9"):
            build_unified_assessment_result(invalid_answers, [None] * 7)

    def test_prefer_not_to_say_is_not_null_or_no(self):
        result = build_unified_assessment_result(
            [0] * 9,
            [0] * 7,
            {
                "age_group": "Prefer not to say",
                "tobacco_use": "No",
                "alcohol_frequency": None,
            },
        )

        context = result["context"]
        self.assertEqual(context["age_group"], "Prefer not to say")
        self.assertEqual(context["tobacco_use"], "No")
        self.assertIsNone(context["alcohol_frequency"])


if __name__ == "__main__":
    unittest.main()
