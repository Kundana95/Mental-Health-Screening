"""Unit tests for bipolar input validation and the model adapter."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from modules.bipolar import classifier as module


def valid_answers():
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


class TestBipolarInputs(unittest.TestCase):
    def test_valid_answers_are_returned_in_model_feature_order(self):
        answers = module.validate_answers(valid_answers())
        self.assertEqual(tuple(answers), module.FEATURES)
        self.assertEqual(answers["Concentration"], 4)
        self.assertEqual(answers["Optimisim"], 5)

    def test_missing_and_unexpected_fields_are_rejected(self):
        answers = valid_answers()
        answers.pop("Sadness")
        with self.assertRaisesRegex(ValueError, "All ten"):
            module.validate_answers(answers)

        answers = valid_answers()
        answers["unexpected"] = "value"
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            module.validate_answers(answers)

    def test_invalid_categorical_values_and_types_are_rejected(self):
        for value in ("sometimes", "Rarely", 1, None, True):
            with self.subTest(value_type=type(value).__name__):
                answers = valid_answers()
                answers["Sadness"] = value
                with self.assertRaises(ValueError):
                    module.validate_answers(answers)

    def test_numeric_inputs_require_integer_values_within_observed_ranges(self):
        for feature, invalid_values in (
            ("Concentration", (0, 9, 4.0, "4", True, None)),
            ("Optimisim", (0, 10, 5.0, "5", False, None)),
        ):
            for value in invalid_values:
                with self.subTest(feature=feature, value_type=type(value).__name__):
                    answers = valid_answers()
                    answers[feature] = value
                    with self.assertRaises(ValueError):
                        module.validate_answers(answers)

    def test_model_receives_ordered_dataframe_and_supported_labels_are_kept(self):
        for category in module.SUPPORTED_CATEGORIES:
            with self.subTest(category=category):
                model = Mock()
                model.predict.return_value = [category]
                result = module.BipolarClassifier(model).analyze(valid_answers())
                frame = model.predict.call_args.args[0]
                self.assertEqual(list(frame.columns), list(module.FEATURES))
                self.assertEqual(result["category"], category)
                self.assertEqual(set(result), {"category", "limitations"})
                self.assertTrue(any("not a diagnosis" in text for text in result["limitations"]))

    def test_unsupported_model_output_is_rejected(self):
        model = Mock()
        model.predict.return_value = ["unexpected"]
        with self.assertRaisesRegex(RuntimeError, "Unexpected model output"):
            module.BipolarClassifier(model).analyze(valid_answers())

    def test_missing_or_modified_artifact_is_rejected_before_deserialization(self):
        with tempfile.TemporaryDirectory() as directory:
            missing_path = Path(directory) / "missing.joblib"
            with patch("joblib.load") as loader:
                with self.assertRaises(module.BipolarModelUnavailableError):
                    module.load_classifier(missing_path)
                loader.assert_not_called()

            altered_path = Path(directory) / "bipolar.joblib"
            altered_path.write_bytes(b"untrusted artifact bytes")
            with patch("joblib.load") as loader:
                with self.assertRaises(module.BipolarModelUnavailableError):
                    module.load_classifier(altered_path)
                loader.assert_not_called()

    def test_incompatible_dependency_is_rejected_before_deserialization(self):
        with patch("modules.bipolar.classifier.version", return_value="wrong"):
            with patch("joblib.load") as loader:
                with self.assertRaises(module.BipolarModelUnavailableError):
                    module.load_classifier()
                loader.assert_not_called()

    def test_model_is_loaded_once_and_failed_load_can_retry(self):
        instance = object()
        with patch.object(module, "_classifier", None), patch.object(
            module, "load_classifier", side_effect=[module.BipolarModelUnavailableError(), instance]
        ) as loader:
            with self.assertRaises(module.BipolarModelUnavailableError):
                module.get_classifier()
            self.assertIs(module.get_classifier(), instance)
            self.assertIs(module.get_classifier(), instance)
            self.assertEqual(loader.call_count, 2)


if __name__ == "__main__":
    unittest.main()
