"""Unit tests with synthetic vectors, independent of private artifacts."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from modules.schizophrenia import classifier as module


class TestTextClassifier(unittest.TestCase):
    def setUp(self):
        self.word2vec = SimpleNamespace(
            wv={"doctor": np.array([2., 4.]), "coffee": np.array([8., 10.])}
        )

    def test_exact_preprocessing_defaults(self):
        self.assertEqual(
            module.preprocess_text("THE café, doctor123 hello_world _hidden a ab abcdefghijklmnop!"),
            ["the", "café", "doctor", "hello_world", "ab"],
        )

    def test_mean_counts_repetitions_and_skips_unknown_words(self):
        result = module.document_vector(
            ["doctor", "unknown", "coffee", "doctor"], self.word2vec
        )
        np.testing.assert_array_equal(result, [4., 6.])

    def test_no_known_words_or_no_tokens_are_rejected(self):
        for tokens in ([], ["unknown"]):
            with self.subTest(tokens=tokens), self.assertRaises(module.InvalidTextError):
                module.document_vector(tokens, self.word2vec)

    def test_invalid_text_is_rejected(self):
        for text in (None, 1, True, [], "", " \n\t", "a" * 4001):
            with self.subTest(text_type=type(text).__name__), self.assertRaises(module.InvalidTextError):
                module.validate_text(text)
        module.validate_text("a" * 4000)

    def test_pipeline_receives_raw_mean_once_and_category_mapping_is_nonclinical(self):
        for label, category in module.CATEGORIES.items():
            pipeline = Mock()
            pipeline.predict.return_value = np.array([label])
            classifier = module.RedditTextClassifier(self.word2vec, pipeline)
            result = classifier.analyze("doctor coffee")
            pipeline.predict.assert_called_once()
            np.testing.assert_array_equal(pipeline.predict.call_args.args[0], [[5., 7.]])
            self.assertEqual(result["category"], category)
            self.assertEqual(set(result), {"category", "model_id", "limitations"})

    def test_unrecognized_text_never_reaches_pipeline(self):
        pipeline = Mock()
        classifier = module.RedditTextClassifier(self.word2vec, pipeline)
        with self.assertRaises(module.InvalidTextError):
            classifier.analyze("unknown")
        pipeline.predict.assert_not_called()

    def test_unexpected_class_is_not_mapped_to_general(self):
        pipeline = Mock()
        pipeline.predict.return_value = [2]
        with self.assertRaises(RuntimeError):
            module.RedditTextClassifier(self.word2vec, pipeline).analyze("doctor")

    def test_missing_or_modified_artifacts_rejected_before_dependency_import(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(module, "version") as dependency_version:
                with self.assertRaises(module.ModelsUnavailableError):
                    module.load_classifier(directory)
                for name in module.TRUSTED_ARTIFACTS:
                    (Path(directory) / name).write_bytes(b"untrusted bytes")
                with self.assertRaises(module.ModelsUnavailableError):
                    module.load_classifier(directory)
                dependency_version.assert_not_called()

    def test_successful_load_is_cached_and_failed_load_can_retry(self):
        with patch.object(module, "_classifier", None), patch.object(module, "load_classifier") as loader:
            loader.side_effect = [module.ModelsUnavailableError(), Mock()]
            with self.assertRaises(module.ModelsUnavailableError):
                module.get_classifier()
            loaded = module.get_classifier()
            self.assertIs(loaded, module.get_classifier())
            self.assertEqual(loader.call_count, 2)


if __name__ == "__main__":
    unittest.main()
