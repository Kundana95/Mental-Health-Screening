"""Build a common, JSON-serializable structure for screening results."""

import json

from modules.depression.gad7 import calculate_gad7_score
from modules.depression.phq9 import calculate_phq9_score


DEFAULT_LIMITATIONS = [
    "This is a screening result, not a diagnosis.",
    "Interpret results with a qualified health professional and other relevant information.",
]

CONTEXT_FIELDS = (
    "age_group",
    "current_status",
    "sleep_duration",
    "sleep_quality",
    "stress_level",
    "physical_activity",
    "tobacco_use",
    "alcohol_frequency",
    "emotional_support",
)

CONTEXT_OPTIONS = {
    "age_group": ("Under 18", "18–24", "25–34", "35–44", "45 and above", "Prefer not to say"),
    "current_status": ("Student", "Employed", "Self-employed", "Unemployed", "Other", "Prefer not to say"),
    "sleep_duration": ("Less than 5 hours", "5–6 hours", "7–8 hours", "More than 8 hours", "My sleep schedule varies considerably"),
    "sleep_quality": ("Very good", "Good", "Fair", "Poor", "Very poor"),
    "stress_level": ("Very low", "Low", "Moderate", "High", "Very high"),
    "physical_activity": ("Never", "1–2 days per week", "3–4 days per week", "5 or more days per week"),
    "tobacco_use": ("No", "Occasionally", "Daily", "Prefer not to say"),
    "alcohol_frequency": ("Never", "Less than once a month", "1–3 times a month", "1–2 times a week", "3 or more times a week", "Prefer not to say"),
    "emotional_support": ("Always", "Often", "Sometimes", "Rarely", "Never", "Prefer not to say"),
}


def validate_unified_assessment_submission(phq9_responses, gad7_responses, context_answers):
    """Reject a submission unless every questionnaire and context answer is valid."""
    phq9 = _validate_partial_responses(phq9_responses, 9, 3, "PHQ-9")
    gad7 = _validate_partial_responses(gad7_responses, 7, 3, "GAD-7")
    if any(answer is None for answer in phq9 + gad7):
        raise ValueError("Answer every questionnaire item before submitting")
    if not isinstance(context_answers, dict) or set(context_answers) != set(CONTEXT_FIELDS):
        raise ValueError("Answer every context question before submitting")
    for key, options in CONTEXT_OPTIONS.items():
        if context_answers[key] is None:
            raise ValueError("Answer every context question before submitting")
        if context_answers[key] not in options:
            raise ValueError(f"Select a valid answer for {key}")
    return True


def build_assessment_result(
    questionnaire_id,
    scoring_result,
    *,
    completion_status="complete",
    demographics=None,
    context=None,
    limitations=None,
):
    """Build a structured assessment payload from an existing score result.

    The returned dictionary contains no direct identifiers by default. Any
    optional demographic data is kept separate from questionnaire scores.
    """
    if not isinstance(questionnaire_id, str) or not questionnaire_id.strip():
        raise ValueError("questionnaire_id must be a non-empty string")
    if not isinstance(scoring_result, dict):
        raise ValueError("scoring_result must be a dictionary")
    if "total_score" not in scoring_result or "severity" not in scoring_result:
        raise ValueError("scoring_result must include total_score and severity")
    if isinstance(scoring_result["total_score"], bool) or not isinstance(
        scoring_result["total_score"], int
    ):
        raise ValueError("total_score must be an integer")
    if not isinstance(scoring_result["severity"], str):
        raise ValueError("severity must be a string")
    if completion_status not in ("complete", "incomplete"):
        raise ValueError("completion_status must be 'complete' or 'incomplete'")
    if demographics is not None and not isinstance(demographics, dict):
        raise ValueError("demographics must be a dictionary when provided")
    if context is not None and not isinstance(context, dict):
        raise ValueError("context must be a dictionary when provided")
    if limitations is not None and (
        not isinstance(limitations, (list, tuple))
        or any(not isinstance(item, str) for item in limitations)
    ):
        raise ValueError("limitations must be a list or tuple of strings")

    safety_flags = scoring_result.get("safety_flags", {})
    if not isinstance(safety_flags, dict) or any(
        not isinstance(name, str) or not isinstance(flag, bool)
        for name, flag in safety_flags.items()
    ):
        raise ValueError("safety_flags must be a dictionary of Boolean values")
    safety_flags = dict(safety_flags)
    if "safety_flag" in scoring_result:
        flag = scoring_result["safety_flag"]
        if not isinstance(flag, bool):
            raise ValueError("safety_flag must be a Boolean")
        # In PHQ-9, the only safety flag currently returned is for question 9.
        safety_flags["question_9"] = flag

    assessment = {
        "questionnaire_id": questionnaire_id,
        "total_score": scoring_result["total_score"],
        "severity": scoring_result["severity"],
        "safety_flags": safety_flags,
        "completion_status": completion_status,
        "demographics": {} if demographics is None else demographics,
        "context": {} if context is None else dict(context),
        "limitations": list(DEFAULT_LIMITATIONS if limitations is None else limitations),
    }

    try:
        json.dumps(assessment)
    except (TypeError, ValueError) as error:
        raise ValueError("assessment result must contain JSON-serializable data") from error

    return assessment


def _validate_partial_responses(responses, expected_count, maximum, questionnaire_id):
    """Validate fixed-length questionnaire answers while allowing unanswered items."""
    if not isinstance(responses, (list, tuple)):
        raise ValueError(f"{questionnaire_id} responses must be a list or tuple")
    if len(responses) != expected_count:
        raise ValueError(
            f"{questionnaire_id} requires exactly {expected_count} response slots"
        )

    validated = list(responses)
    for index, answer in enumerate(validated, start=1):
        if answer is None:
            continue
        if isinstance(answer, bool) or not isinstance(answer, int):
            raise ValueError(
                f"{questionnaire_id} response {index} must be an integer or None"
            )
        if answer < 0 or answer > maximum:
            raise ValueError(
                f"{questionnaire_id} response {index} must be from 0 to {maximum}"
            )
    return validated


def build_unified_assessment_result(phq9_responses, gad7_responses, context_answers=None):
    """Build a combined payload while scoring PHQ-9 and GAD-7 independently.

    An unanswered item is kept as ``None``. A questionnaire is scored only when
    all its items have valid answers. Context answers are never scored.
    """
    phq9_responses = _validate_partial_responses(phq9_responses, 9, 3, "PHQ-9")
    gad7_responses = _validate_partial_responses(gad7_responses, 7, 3, "GAD-7")

    if context_answers is None:
        context_answers = {}
    if not isinstance(context_answers, dict):
        raise ValueError("context_answers must be a dictionary")

    context = {field: None for field in CONTEXT_FIELDS}
    for key, answer in context_answers.items():
        if not isinstance(key, str):
            raise ValueError("context answer keys must be strings")
        if answer is not None and not isinstance(answer, str):
            raise ValueError("context answers must be strings or None")
        context[key] = answer

    phq9_complete = all(answer is not None for answer in phq9_responses)
    gad7_complete = all(answer is not None for answer in gad7_responses)
    phq9_score = calculate_phq9_score(phq9_responses) if phq9_complete else None
    gad7_score = calculate_gad7_score(gad7_responses) if gad7_complete else None

    question_nine = phq9_responses[8]
    safety_flag = None if question_nine is None else question_nine > 0

    assessment = {
        "assessment_id": "mental_health_screening_v1",
        "questionnaire_results": {
            "PHQ-9": {
                "responses": phq9_responses,
                "total_score": None if phq9_score is None else phq9_score["total_score"],
                "severity": None if phq9_score is None else phq9_score["severity"],
                "completion_status": "complete" if phq9_complete else "incomplete",
            },
            "GAD-7": {
                "responses": gad7_responses,
                "total_score": None if gad7_score is None else gad7_score["total_score"],
                "severity": None if gad7_score is None else gad7_score["severity"],
                "completion_status": "complete" if gad7_complete else "incomplete",
            },
        },
        "context": context,
        "completion_status": (
            "complete" if phq9_complete and gad7_complete else "incomplete"
        ),
        "context_completion_status": (
            "complete" if all(value is not None for value in context.values()) else "partial"
        ),
        "safety_flags": {"PHQ-9": {"question_9": safety_flag}},
        "limitations": list(DEFAULT_LIMITATIONS),
    }

    try:
        json.dumps(assessment)
    except (TypeError, ValueError) as error:
        raise ValueError("assessment result must contain JSON-serializable data") from error

    return assessment
