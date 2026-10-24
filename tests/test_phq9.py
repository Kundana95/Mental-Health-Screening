import unittest

from modules.depression.phq9 import calculate_phq9_score


class TestCalculatePhq9Score(unittest.TestCase):
    def test_calculates_total_and_minimal_severity(self):
        result = calculate_phq9_score([1, 1, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(result, {
            "total_score": 2,
            "severity": "Minimal",
            "safety_flag": False,
        })

    def test_severity_boundaries(self):
        cases = [
            (0, "Minimal"),
            (4, "Minimal"),
            (5, "Mild"),
            (9, "Mild"),
            (10, "Moderate"),
            (14, "Moderate"),
            (15, "Moderately severe"),
            (19, "Moderately severe"),
            (20, "Severe"),
            (27, "Severe"),
        ]
        for score, expected_severity in cases:
            with self.subTest(score=score):
                # Distribute the requested total across nine valid answers.
                remaining = score
                answers = []
                for _ in range(9):
                    answer = min(3, remaining)
                    answers.append(answer)
                    remaining -= answer
                result = calculate_phq9_score(answers)
                self.assertEqual(result["total_score"], score)
                self.assertEqual(result["severity"], expected_severity)

    def test_question_nine_sets_safety_flag_independent_of_total(self):
        result = calculate_phq9_score([0, 0, 0, 0, 0, 0, 0, 0, 1])
        self.assertEqual(result["total_score"], 1)
        self.assertEqual(result["severity"], "Minimal")
        self.assertTrue(result["safety_flag"])

    def test_zero_on_question_nine_does_not_set_safety_flag(self):
        result = calculate_phq9_score([3, 3, 3, 3, 3, 3, 3, 3, 0])
        self.assertFalse(result["safety_flag"])

    def test_missing_responses_are_rejected(self):
        for answers in ([0] * 8, [0, 1, None, 0, 0, 0, 0, 0, 0]):
            with self.subTest(answers=answers):
                with self.assertRaises(ValueError):
                    calculate_phq9_score(answers)

    def test_invalid_response_values_are_rejected(self):
        for invalid in (-1, 4, 1.5, "2", True):
            answers = [0] * 9
            answers[3] = invalid
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    calculate_phq9_score(answers)

    def test_non_sequence_and_too_many_responses_are_rejected(self):
        for answers in (None, "000000000", [0] * 10):
            with self.subTest(answers=answers):
                with self.assertRaises(ValueError):
                    calculate_phq9_score(answers)


if __name__ == "__main__":
    unittest.main()
