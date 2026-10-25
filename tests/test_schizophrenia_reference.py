"""Opt-in parity tests against the owner's local Colab exports, with no training.

Set RUN_LOCAL_MODEL_TESTS=1. Never execute notebook cells; historical inputs are
read as JSON text only and never printed or copied into tracked fixtures.
"""

import json
import os
import unittest
from pathlib import Path


@unittest.skipUnless(os.environ.get("RUN_LOCAL_MODEL_TESTS") == "1", "Requires trusted local exports; set RUN_LOCAL_MODEL_TESTS=1")
class TestColabReferenceParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np
        from gensim.utils import simple_preprocess
        from modules.schizophrenia.classifier import load_classifier

        cls.np = np
        cls.tokenize = staticmethod(simple_preprocess)
        cls.classifier = load_classifier()

    def notebook_vector(self, tokens):
        # Exact document_vector code from notebook cell 52 (zero-based index).
        model = self.classifier.word2vec
        vectors = [model.wv[word] for word in tokens if word in model.wv]
        if len(vectors) == 0:
            return self.np.zeros(model.vector_size)
        return self.np.mean(vectors, axis=0)

    def assert_parity(self, text):
        from modules.schizophrenia.classifier import CATEGORIES, document_vector, preprocess_text

        reference_tokens = self.tokenize(text)
        self.assertEqual(preprocess_text(text), reference_tokens)
        reference_vector = self.notebook_vector(reference_tokens)
        self.np.testing.assert_array_equal(
            document_vector(preprocess_text(text), self.classifier.word2vec), reference_vector
        )
        expected = self.classifier.pipeline.predict(reference_vector.reshape(1, -1))[0]
        self.assertEqual(self.classifier.analyze(text)["category"], CATEGORIES[expected])
        return int(expected)

    def test_synthetic_examples_match_notebook_path_and_http_response(self):
        from fastapi.testclient import TestClient
        from unittest.mock import patch
        from api import app
        from modules.schizophrenia.classifier import CATEGORIES

        examples = [
            "I am planning my monthly budget and saving money for rent.",
            "I talked with my psychiatrist about medication and hearing voices.",
            "I feel anxious and worried about exams and cannot sleep.",
            "I am trying to stop drinking alcohol and need support.",
            "Doctor doctor coffee! café 123 _hidden abcdefghijklmnop",
            "doctor",
        ]
        with patch("modules.schizophrenia.api.get_classifier", return_value=self.classifier):
            client = TestClient(app)
            for index, text in enumerate(examples):
                with self.subTest(reference=index):
                    expected = self.assert_parity(text)
                    response = client.post("/api/schizophrenia/analyze", json={"text": text})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["category"], CATEGORIES[expected])
            for text in ("12345 !!!", "qzxqzxqzx"):
                response = client.post("/api/schizophrenia/analyze", json={"text": text})
                self.assertEqual(response.status_code, 422)

    def test_original_saved_colab_example_matches_historical_prediction(self):
        notebook_path = Path(__file__).resolve().parents[1] / "modules" / "sctizo.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        output = "".join("".join(item.get("text", [])) for item in notebook["cells"][63].get("outputs", []))
        prefix = "Enter your paragraph: "
        suffix = "\nLanguage classified closer to schizophrenia-community posts"
        self.assertTrue(output.startswith(prefix))
        self.assertIn(suffix, output)
        text = output[len(prefix):output.index(suffix)]
        self.assertEqual(self.assert_parity(text), 1)


if __name__ == "__main__":
    unittest.main()
