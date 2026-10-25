"""Validated inference for the project's experimental bipolar model.

This prototype returns a screening category, not a clinical diagnosis.
"""

from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
import sys
from threading import Lock


MODEL_PATH = Path(__file__).resolve().parents[2] / "local_models" / "bipolar_random_forest_model.joblib"
TRUSTED_MODEL_SHA256 = "f1de57e73db6feb6ba1950254d87bfa9b3796e0159f9a70ab2580016044348fc"

FEATURES = (
    "Sadness",
    "Euphoric",
    "Exhausted",
    "Sleep dissorder",
    "Mood Swing",
    "Aggressive Response",
    "Admit Mistakes",
    "Overthinking",
    "Concentration",
    "Optimisim",
)

CATEGORICAL_CHOICES = {
    "Sadness": ("Seldom", "Sometimes", "Usually", "Most-Often"),
    "Euphoric": ("Seldom", "Sometimes", "Usually", "Most-Often"),
    "Exhausted": ("Seldom", "Sometimes", "Usually", "Most-Often"),
    "Sleep dissorder": ("Seldom", "Sometimes", "Usually", "Most-Often"),
    "Mood Swing": ("YES", "NO"),
    "Aggressive Response": ("YES", "NO"),
    "Admit Mistakes": ("YES", "NO"),
    "Overthinking": ("YES", "NO"),
}
NUMERIC_RANGES = {"Concentration": (1, 8), "Optimisim": (1, 9)}
SUPPORTED_CATEGORIES = (
    "Bipolar Type 1",
    "Bipolar Type 2",
    "No Bipolar Indication",
)

LIMITATIONS = (
    "This is an experimental screening prototype based on a small dataset, not a diagnosis.",
    "A model result cannot confirm or rule out bipolar disorder.",
    "If you have concerns, seek an assessment from a qualified mental-health professional.",
)


class InvalidBipolarAnswersError(ValueError):
    """Submitted inputs do not match the model's documented feature schema."""


class BipolarModelUnavailableError(RuntimeError):
    """The trusted model or its compatible dependencies are unavailable."""


def validate_answers(answers):
    """Validate all categorical and numeric model inputs without coercion."""
    if not isinstance(answers, dict):
        raise InvalidBipolarAnswersError("Answers must be an object.")

    received = set(answers)
    expected = set(FEATURES)
    if received != expected:
        if expected - received:
            raise InvalidBipolarAnswersError("All ten answers are required.")
        raise InvalidBipolarAnswersError("Unexpected answers were supplied.")

    cleaned = {}
    for feature, choices in CATEGORICAL_CHOICES.items():
        value = answers[feature]
        if type(value) is not str or value not in choices:
            raise InvalidBipolarAnswersError(f"{feature} has an invalid choice.")
        cleaned[feature] = value

    for feature, (minimum, maximum) in NUMERIC_RANGES.items():
        value = answers[feature]
        if type(value) is not int or not minimum <= value <= maximum:
            raise InvalidBipolarAnswersError(
                f"{feature} must be an integer from {minimum} to {maximum}."
            )
        cleaned[feature] = value

    return {feature: cleaned[feature] for feature in FEATURES}


class BipolarClassifier:
    """Run the existing fitted pipeline without changing its preprocessing."""

    def __init__(self, model):
        self.model = model

    def analyze(self, answers):
        validated = validate_answers(answers)
        import pandas as pd

        frame = pd.DataFrame(
            [[validated[feature] for feature in FEATURES]], columns=FEATURES
        )
        predictions = self.model.predict(frame)
        if len(predictions) != 1:
            raise RuntimeError("Unexpected model output.")

        category = str(predictions[0])
        if category not in SUPPORTED_CATEGORIES:
            raise RuntimeError("Unexpected model output.")

        return {
            "category": category,
            "limitations": list(LIMITATIONS),
        }


def _validate_bundle(bundle):
    """Check the saved bundle's schema and fitted pipeline before use."""
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder

    if not isinstance(bundle, dict) or set(bundle) != {"model", "features", "classes"}:
        raise BipolarModelUnavailableError("Unexpected model bundle.")
    if not isinstance(bundle["features"], (list, tuple)) or tuple(bundle["features"]) != FEATURES:
        raise BipolarModelUnavailableError("Unexpected model features.")
    if set(bundle["classes"]) != set(SUPPORTED_CATEGORIES):
        raise BipolarModelUnavailableError("Unexpected model classes.")

    model = bundle["model"]
    if not isinstance(model, Pipeline) or [name for name, _ in model.steps] != [
        "preprocessor", "classifier"
    ]:
        raise BipolarModelUnavailableError("Unexpected model pipeline.")

    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]
    if not isinstance(preprocessor, ColumnTransformer) or not isinstance(
        classifier, RandomForestClassifier
    ):
        raise BipolarModelUnavailableError("Unexpected model components.")
    if not hasattr(classifier, "estimators_") or not classifier.estimators_:
        raise BipolarModelUnavailableError("The model is not fitted.")
    if set(classifier.classes_) != set(SUPPORTED_CATEGORIES):
        raise BipolarModelUnavailableError("Unexpected classifier classes.")
    if tuple(getattr(model, "feature_names_in_", ())) != FEATURES:
        raise BipolarModelUnavailableError("Unexpected model feature order.")

    transformers = {
        name: (columns, transformer)
        for name, transformer, columns in preprocessor.transformers_
        if name != "remainder"
    }
    if set(transformers) != {"categorical", "numeric"}:
        raise BipolarModelUnavailableError("Unexpected model preprocessing.")

    categorical_columns, categorical_pipeline = transformers["categorical"]
    numeric_columns, numeric_pipeline = transformers["numeric"]
    if tuple(categorical_columns) != FEATURES[:8] or tuple(numeric_columns) != FEATURES[8:]:
        raise BipolarModelUnavailableError("Unexpected model feature order.")
    if not isinstance(categorical_pipeline, Pipeline) or not isinstance(
        numeric_pipeline, Pipeline
    ):
        raise BipolarModelUnavailableError("Unexpected model preprocessing.")
    categorical_imputer = categorical_pipeline.named_steps.get("imputer")
    encoder = categorical_pipeline.named_steps.get("encoder")
    numeric_imputer = numeric_pipeline.named_steps.get("imputer")
    if (
        not isinstance(categorical_imputer, SimpleImputer)
        or categorical_imputer.strategy != "most_frequent"
        or not isinstance(encoder, OneHotEncoder)
        or encoder.handle_unknown != "ignore"
        or not isinstance(numeric_imputer, SimpleImputer)
        or numeric_imputer.strategy != "median"
    ):
        raise BipolarModelUnavailableError("Unexpected model preprocessing.")

    observed_categories = {
        feature: set(values)
        for feature, values in zip(FEATURES[:8], encoder.categories_)
    }
    if any(
        observed_categories[feature] != set(choices)
        for feature, choices in CATEGORICAL_CHOICES.items()
    ):
        raise BipolarModelUnavailableError("Unexpected model categories.")

    return model


def load_classifier(model_path=MODEL_PATH):
    """Verify the trusted artifact and environment before deserializing it."""
    try:
        artifact = Path(model_path)
        digest = sha256(artifact.read_bytes()).hexdigest()
        if digest != TRUSTED_MODEL_SHA256:
            raise BipolarModelUnavailableError("Model artifact mismatch.")

        if sys.version_info[:2] != (3, 13):
            raise BipolarModelUnavailableError("Incompatible Python version.")
        expected_versions = {
            "scikit-learn": "1.6.1",
            "joblib": "1.5.3",
            "numpy": "2.2.6",
            "pandas": "2.2.3",
        }
        if any(version(package) != expected for package, expected in expected_versions.items()):
            raise BipolarModelUnavailableError("Incompatible model dependencies.")

        import joblib

        bundle = joblib.load(artifact)
        return BipolarClassifier(_validate_bundle(bundle))
    except Exception:
        raise BipolarModelUnavailableError(
            "Bipolar screening is temporarily unavailable."
        ) from None


_classifier = None
_classifier_lock = Lock()


def get_classifier():
    """Load once on the first valid request; allow retries after a failure."""
    global _classifier
    with _classifier_lock:
        if _classifier is None:
            _classifier = load_classifier()
        return _classifier
