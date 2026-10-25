"""Unit tests for the experimental anxiety classifier."""

import unittest
from unittest.mock import Mock

from modules.anxiety.classifier import (
    AnxietyClassifier,
    AnxietyModelUnavailableError,
    SUPPORTED_CATEGORIES,
    load_classifier,
    validate_responses,
)


class TestAnxietyClassifier(unittest.TestCase):
    def test_requires_seven_integer_responses_from_zero_to_three(self):
        self.assertEqual(validate_responses([0, 1, 2, 3, 0, 1, 2]), [0, 1, 2, 3, 0, 1, 2])
        for invalid in (
            None,
            [0] * 6,
            [0] * 8,
            [0, 1, 2, 3, 0, 1, True],
            [0, 1, 2, 3, 0, 1, 2.0],
            [0, 1, 2, 3, 0, 1, "2"],
            [0, 1, 2, 3, 0, 1, -1],
            [0, 1, 2, 3, 0, 1, 4],
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_responses(invalid)

    def test_model_receives_values_in_feature_file_order(self):
        model = Mock()
        model.predict.return_value = ["Moderate Anxiety"]
        classifier = AnxietyClassifier(model, [f"question-{index}" for index in range(7)])

        result = classifier.analyze([3, 2, 1, 0, 3, 2, 1])

        frame = model.predict.call_args.args[0]
        self.assertEqual(list(frame.columns), [f"question-{index}" for index in range(7)])
        self.assertEqual(frame.iloc[0].tolist(), [3, 2, 1, 0, 3, 2, 1])
        self.assertEqual(result["category"], "Moderate Anxiety")
        self.assertIn("not a clinical diagnosis", result["limitations"][0])

    def test_unsupported_prediction_is_rejected(self):
        model = Mock()
        model.predict.return_value = ["unexpected label"]
        classifier = AnxietyClassifier(model, [f"question-{index}" for index in range(7)])
        with self.assertRaises(RuntimeError):
            classifier.analyze([0] * 7)

    def test_trained_model_loads_and_predicts_a_synthetic_valid_response(self):
        classifier = load_classifier()
        self.assertEqual(len(classifier.features), 7)
        result = classifier.analyze([0, 1, 2, 3, 0, 1, 2])
        self.assertIn(result["category"], SUPPORTED_CATEGORIES)

    def test_missing_model_artifacts_fail_without_exposing_paths(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AnxietyModelUnavailableError) as error:
                load_classifier(directory)
        self.assertEqual(
            str(error.exception),
            "Anxiety screening is temporarily unavailable.",
        )
        self.assertNotIn(directory, str(error.exception))


if __name__ == "__main__":
    unittest.main()
