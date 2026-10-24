"""Calculate a PHQ-9 screening score and its severity band."""


def calculate_phq9_score(responses):
    """Return the PHQ-9 total, severity band, and question 9 safety flag.

    This is a screening score calculation, not a diagnosis.
    ``responses`` must contain exactly nine integer answers from 0 to 3.
    """
    if not isinstance(responses, (list, tuple)):
        raise ValueError("responses must be a list or tuple of exactly 9 integers")

    if len(responses) != 9:
        raise ValueError("exactly 9 responses are required")

    for index, response in enumerate(responses, start=1):
        # bool is a subclass of int in Python, so exclude it explicitly.
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
    elif total_score <= 19:
        severity = "Moderately severe"
    else:
        severity = "Severe"

    return {
        "total_score": total_score,
        "severity": severity,
        "safety_flag": responses[8] > 0,
    }
