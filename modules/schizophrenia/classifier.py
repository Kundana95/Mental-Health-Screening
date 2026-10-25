"""Inference matching sctizo.ipynb, using only the owner's trusted local exports.

No training, request persistence, or clinical scoring occurs here. Dependencies
are imported lazily so missing ML dependencies do not disable depression routes.
"""

from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from threading import Lock


MODEL_DIRECTORY = Path(__file__).resolve().parents[2] / "local_models"
TRUSTED_ARTIFACTS = {
    "word2vec_zenodo.model": "4a0e70b94c81d0036c22ee432c050a917032a43a465a177a1859396b3c5b8350",
    "svm_word2vec_classifier.pkl": "f3c895f0006ef93da4797ca7c6a15b12f81575a38dfe89fe20ec456fda1716f0",
}
MODEL_ID = "reddit-word2vec-linearsvc-2026-10-24"
MAX_TEXT_LENGTH = 4000
CATEGORIES = {0: "general_community", 1: "schizophrenia_community"}
LIMITATIONS = (
    "Experimental Reddit community text classification; not a diagnosis or clinical screening result.",
    "Anxiety, addiction, and other mental-health text may be misclassified.",
    "Neither category establishes or rules out schizophrenia; no clinical risk or probability is estimated.",
)


class InvalidTextError(ValueError):
    """Input cannot be classified using the known vocabulary."""


class ModelsUnavailableError(RuntimeError):
    """Trusted compatible model artifacts are unavailable."""


def validate_text(text):
    if not isinstance(text, str) or not text.strip():
        raise InvalidTextError("Enter non-empty text to analyze.")
    if len(text) > MAX_TEXT_LENGTH:
        raise InvalidTextError(f"Text must contain at most {MAX_TEXT_LENGTH} characters.")


def preprocess_text(text):
    """Keep the notebook's exact Gensim defaults; do not strip or normalize."""
    from gensim.utils import simple_preprocess

    return simple_preprocess(str(text))


def document_vector(tokens, model):
    """Mean raw known-token vectors, counting repetitions as in the notebook.

    Unlike the notebook, reject zero-coverage text instead of classifying zeros.
    """
    import numpy as np

    vectors = [model.wv[word] for word in tokens if word in model.wv]
    if not vectors:
        raise InvalidTextError("No recognized words were found. Please provide different text.")
    return np.mean(vectors, axis=0)


class RedditTextClassifier:
    def __init__(self, word2vec, pipeline):
        self.word2vec = word2vec
        self.pipeline = pipeline

    def analyze(self, text):
        validate_text(text)
        vector = document_vector(preprocess_text(text), self.word2vec)
        # StandardScaler is already fitted and included in this pipeline.
        label = self.pipeline.predict(vector.reshape(1, -1))[0]
        if label not in CATEGORIES:
            raise RuntimeError("Unexpected model output.")
        return {
            "category": CATEGORIES[label],
            "model_id": MODEL_ID,
            "limitations": list(LIMITATIONS),
        }


def load_classifier(model_directory=MODEL_DIRECTORY):
    """Verify known owner-provided bytes before calling any pickle-based loader.

    No client-selected paths or model uploads are accepted. Replacement models
    require an explicit review and updated hashes; a hash is not a safety scanner.
    """
    try:
        paths = {}
        for name, expected in TRUSTED_ARTIFACTS.items():
            path = Path(model_directory) / name
            with path.open("rb") as artifact:
                if sha256(artifact.read()).hexdigest() != expected:
                    raise ModelsUnavailableError("Model artifact mismatch.")
            paths[name] = path

        if version("gensim") != "4.4.0" or version("scikit-learn") != "1.6.1":
            raise ModelsUnavailableError("Incompatible model dependencies.")

        import joblib
        import numpy as np
        from gensim.models import Word2Vec
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import LinearSVC

        word2vec = Word2Vec.load(str(paths["word2vec_zenodo.model"]))
        pipeline = joblib.load(paths["svm_word2vec_classifier.pkl"])
        if (
            word2vec.vector_size != 100
            or not isinstance(pipeline, Pipeline)
            or len(pipeline.steps) != 2
            or not isinstance(pipeline.steps[0][1], StandardScaler)
            or not isinstance(pipeline.steps[1][1], LinearSVC)
            or pipeline.n_features_in_ != 100
            or not np.array_equal(pipeline.classes_, [0, 1])
        ):
            raise ModelsUnavailableError("Unexpected model structure.")
        return RedditTextClassifier(word2vec, pipeline)
    except Exception:
        # Do not expose paths, serialization details, or exception contents.
        raise ModelsUnavailableError("Text classification is temporarily unavailable.") from None


_classifier = None
_classifier_lock = Lock()


def get_classifier():
    """Load once on first use per worker; failed loads may be retried."""
    global _classifier
    with _classifier_lock:
        if _classifier is None:
            _classifier = load_classifier()
        return _classifier
