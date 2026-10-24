"""Calculate a GAD-7 screening score and severity band."""


def calculate_gad7_score(responses):
    """Return the GAD-7 total and severity band for seven answers.

    This calculates a screening score, not a diagnosis. Each answer must be
    an integer from 0 to 3, and exactly seven answers are required.
    """
    if not isinstance(responses, (list, tuple)):
        raise ValueError("responses must be a list or tuple of exactly 7 integers")

    if len(responses) != 7:
        raise ValueError("exactly 7 responses are required")

    for index, response in enumerate(responses, start=1):
        # In Python, bool is a subclass of int, so reject it explicitly.
        if isinstance(response, bool) or not isinstance(response, int):
            raise ValueError(f"response {index} must be an integer from 0 to 3")
        if response < 0 or response > 3:
            raise ValueError(f"response {index} must be an integer from 0 to 3")

    total_score = sum(responses)

    if total_score <= 4:
        severity = "Minimal"
    elif total_score <= 9:
        severity = "Mild"
    elif total_score <= 14:
        severity = "Moderate"
    else:
        severity = "Severe"

    return {"total_score": total_score, "severity": severity}
