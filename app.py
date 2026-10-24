"""Local Streamlit demo for a mental health screening assessment."""

import streamlit as st

from modules.assessment_result import (
    CONTEXT_OPTIONS,
    build_unified_assessment_result,
    validate_unified_assessment_submission,
)


st.set_page_config(page_title="Mental Health Assessment", page_icon="📝")
st.title("Mental Health Assessment")
st.info(
    "This questionnaire is a screening tool, not a diagnosis. It cannot replace "
    "a conversation with a qualified health professional."
)

phq9_questions = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading the newspaper or watching television",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
    "Thoughts that you would be better off dead, or of hurting yourself in some way",
]

gad7_questions = [
    "Feeling nervous, anxious or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it is hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid as if something awful might happen",
]

response_choices = {
    "Not at all": 0,
    "Several days": 1,
    "More than half the days": 2,
    "Nearly every day": 3,
}

context_questions = [
    ("age_group", "What is your age group?"),
    ("current_status", "What is your current status?"),
    ("sleep_duration", "On average, how many hours do you sleep per night?"),
    ("sleep_quality", "How would you describe your sleep quality?"),
    ("stress_level", "How would you rate your current stress level?"),
    ("physical_activity", "How often do you engage in physical activity for at least 30 minutes?"),
    ("tobacco_use", "Do you currently use tobacco or nicotine products?"),
    ("alcohol_frequency", "How often do you consume alcohol?"),
    ("emotional_support", "How often do you feel you have someone you can turn to for emotional support?"),
]

phq9_responses = []
gad7_responses = []
context_answers = {}
question_number = 0

for question in phq9_questions:
    question_number += 1
    selected = st.radio(
        f"{question_number}. {question}",
        options=list(response_choices),
        index=None,
        key=f"assessment_response_{question_number}",
    )
    phq9_responses.append(None if selected is None else response_choices[selected])

for question in gad7_questions:
    question_number += 1
    selected = st.radio(
        f"{question_number}. {question}",
        options=list(response_choices),
        index=None,
        key=f"assessment_response_{question_number}",
    )
    gad7_responses.append(None if selected is None else response_choices[selected])

for key, question in context_questions:
    question_number += 1
    context_answers[key] = st.selectbox(
        f"{question_number}. {question}",
        options=CONTEXT_OPTIONS[key],
        index=None,
        placeholder="Select an answer",
        key=f"assessment_context_{key}",
    )

all_questionnaire_answers_selected = all(
    answer is not None for answer in phq9_responses + gad7_responses
)
all_context_answers_selected = all(
    context_answers.get(key) in choices for key, choices in CONTEXT_OPTIONS.items()
)
submitted = st.button(
    "Submit assessment",
    disabled=not (all_questionnaire_answers_selected and all_context_answers_selected),
)

if submitted:
    try:
        validate_unified_assessment_submission(
            phq9_responses, gad7_responses, context_answers
        )
    except ValueError as error:
        st.error(str(error))
    else:
        assessment = build_unified_assessment_result(
            phq9_responses, gad7_responses, context_answers
        )
        results = assessment["questionnaire_results"]
        st.subheader("Screening results")

        for result_number, (questionnaire_id, denominator) in enumerate(
            (("PHQ-9", 27), ("GAD-7", 21)), start=1
        ):
            result = results[questionnaire_id]
            st.write(f"**Result {result_number}**")
            st.metric("Total score", f"{result['total_score']} / {denominator}")
            st.write(f"Interpretation: **{result['severity']}**")

        if assessment["safety_flags"]["PHQ-9"]["question_9"] is True:
            st.warning(
                "Your answer to question 9 indicates that you have had thoughts "
                "of being better off dead or of hurting yourself. Please reach "
                "out to a trusted person and seek support from a qualified "
                "mental health professional or local crisis service. If you may "
                "be in immediate danger, contact your local emergency service now."
            )

        with st.expander("Structured assessment data (JSON)"):
            st.json(assessment)

st.caption(
    "PHQ-9 © Pfizer Inc. All rights reserved. Use is subject to the PHQ Screeners "
    "terms of use. This local academic demo is not for distribution directly to "
    "patients or consumers outside the permitted contexts."
)
st.caption(
    "GAD-7 developed by Drs. Robert L. Spitzer, Janet B.W. Williams, Kurt Kroenke "
    "and colleagues, with an educational grant from Pfizer Inc. No permission "
    "is required to reproduce, translate, display, or distribute the GAD-7."
)
