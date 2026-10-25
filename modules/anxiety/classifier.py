"""Validated inference for the project's experimental anxiety model."""

from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
import pickle
import sys
from threading import Lock


MODEL_DIRECTORY = Path(__file__).resolve().parents[2] / "local_models"
TRUSTED_ARTIFACTS = {
    "best_anxiety_model.joblib": "1eac08c3e4a7d90f38e6ed26c949215f167bcdcfcc286ceb83990a1c6cf1797a",
    "anxiety_features.pkl": "b5022e7b7e678d7c2c00e5ef459f73ca3df1ca4852cbf45f495fef8c580519d1",
}
SUPPORTED_CATEGORIES = (
    "Minimal Anxiety",
    "Mild Anxiety",
    "Moderate Anxiety",
    "Severe Anxiety",
)
LIMITATIONS = (
    "This is an experimental screening estimate, not a clinical diagnosis.",
    "The model's output does not establish or rule out an anxiety disorder.",
    "Seek assessment from a qualified mental-health professional for concerns.",
)


class InvalidAnxietyResponsesError(ValueError):
    """The submitted answers do not match the model input requirements."""


class AnxietyModelUnavailableError(RuntimeError):
    """The verified anxiety model or compatible dependencies are unavailable."""


def validate_responses(responses):
    """Require seven integer frequency responses encoded from zero to three."""
    if not isinstance(responses, (list, tuple)) or len(responses) != 7:
        raise InvalidAnxietyResponsesError("Provide exactly seven responses.")
    if any(type(answer) is not int or not 0 <= answer <= 3 for answer in responses):
        raise InvalidAnxietyResponsesError(
            "Each response must be an integer from 0 to 3."
        )
    return list(responses)


class AnxietyClassifier:
    """Apply the existing fitted pipeline to responses in feature-file order."""

    def __init__(self, model, features):
        self.model = model
        self.features = tuple(features)

    def analyze(self, responses):
        validated = validate_responses(responses)
        import pandas as pd

        frame = pd.DataFrame([validated], columns=self.features)
        predictions = self.model.predict(frame)
        if len(predictions) != 1:
            raise RuntimeError("Unexpected model output.")
        category = str(predictions[0])
        if category not in SUPPORTED_CATEGORIES:
            raise RuntimeError("Unexpected model output.")
        return {"category": category, "limitations": list(LIMITATIONS)}


def _verified_artifacts(model_directory):
    paths = {}
    for name, expected_digest in TRUSTED_ARTIFACTS.items():
        path = Path(model_directory) / name
        if sha256(path.read_bytes()).hexdigest() != expected_digest:
            raise AnxietyModelUnavailableError("Anxiety model artifact mismatch.")
        paths[name] = path
    return paths


def load_classifier(model_directory=MODEL_DIRECTORY):
    """Verify known artifact bytes and runtime before pickle-based loading."""
    try:
        paths = _verified_artifacts(model_directory)
        if sys.version_info[:2] != (3, 13):
            raise AnxietyModelUnavailableError("Incompatible Python version.")
        expected_versions = {
            "scikit-learn": "1.6.1",
            "joblib": "1.5.3",
            "numpy": "2.2.6",
            "pandas": "2.2.3",
        }
        if any(
            version(package) != expected
            for package, expected in expected_versions.items()
        ):
            raise AnxietyModelUnavailableError("Incompatible model dependencies.")

        import joblib
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        # The feature artifact is hash-checked above and contains only the
        # ordered list of question strings used as the model's input columns.
        with paths["anxiety_features.pkl"].open("rb") as feature_file:
            features = pickle.load(feature_file)
        model = joblib.load(paths["best_anxiety_model.joblib"])
        if (
            not isinstance(features, list)
            or len(features) != 7
            or any(not isinstance(feature, str) for feature in features)
            or not isinstance(model, Pipeline)
            or [name for name, _ in model.steps]
            != ["standardscaler", "logisticregression"]
            or not isinstance(model.named_steps["standardscaler"], StandardScaler)
            or not isinstance(model.named_steps["logisticregression"], LogisticRegression)
            or not hasattr(model.named_steps["logisticregression"], "classes_")
            or set(model.classes_) != set(SUPPORTED_CATEGORIES)
            or tuple(model.feature_names_in_) != tuple(features)
        ):
            raise AnxietyModelUnavailableError("Unexpected anxiety model structure.")
        return AnxietyClassifier(model, features)
    except Exception:
        raise AnxietyModelUnavailableError(
            "Anxiety screening is temporarily unavailable."
        ) from None


_classifier = None
_classifier_lock = Lock()


def get_classifier():
    """Load once on first valid request; failed loads can be retried."""
    global _classifier
    with _classifier_lock:
        if _classifier is None:
            _classifier = load_classifier()
        return _classifier
