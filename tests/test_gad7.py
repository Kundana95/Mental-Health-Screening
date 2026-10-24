import unittest

from modules.depression.gad7 import calculate_gad7_score


class TestCalculateGad7Score(unittest.TestCase):
    def test_calculates_total_and_severity(self):
        result = calculate_gad7_score([1, 1, 0, 0, 0, 0, 0])
        self.assertEqual(result, {"total_score": 2, "severity": "Minimal"})

    def test_severity_boundaries(self):
        cases = [
            (0, "Minimal"),
            (4, "Minimal"),
            (5, "Mild"),
            (9, "Mild"),
            (10, "Moderate"),
            (14, "Moderate"),
            (15, "Severe"),
            (21, "Severe"),
        ]
        for score, expected_severity in cases:
            with self.subTest(score=score):
                remaining = score
                answers = []
                for _ in range(7):
                    answer = min(3, remaining)
                    answers.append(answer)
                    remaining -= answer

                result = calculate_gad7_score(answers)
                self.assertEqual(result["total_score"], score)
                self.assertEqual(result["severity"], expected_severity)

    def test_invalid_response_values_are_rejected(self):
        for invalid in (-1, 4, 1.5, "2", True):
            answers = [0] * 7
            answers[2] = invalid
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    calculate_gad7_score(answers)

    def test_missing_responses_are_rejected(self):
        invalid_answer_sets = (
            [0] * 6,
            [0, 1, None, 0, 0, 0, 0],
        )
        for answers in invalid_answer_sets:
            with self.subTest(answers=answers):
                with self.assertRaises(ValueError):
                    calculate_gad7_score(answers)

    def test_too_many_or_non_sequence_responses_are_rejected(self):
        for answers in ([0] * 8, None, "0000000"):
            with self.subTest(answers=answers):
                with self.assertRaises(ValueError):
                    calculate_gad7_score(answers)


if __name__ == "__main__":
    unittest.main()
