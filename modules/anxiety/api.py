"""HTTP interface for the experimental anxiety screening model."""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from modules.anxiety.classifier import (
    AnxietyModelUnavailableError,
    InvalidAnxietyResponsesError,
    LIMITATIONS,
    get_classifier,
    validate_responses,
)


router = APIRouter(prefix="/api/anxiety")


class AnxietyAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    responses: list[StrictInt] = Field(min_length=7, max_length=7)


class AnxietyAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal[
        "Minimal Anxiety",
        "Mild Anxiety",
        "Moderate Anxiety",
        "Severe Anxiety",
    ]
    limitations: list[str]


def classifier_dependency():
    try:
        return get_classifier()
    except AnxietyModelUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="Anxiety screening is temporarily unavailable.",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Anxiety screening is temporarily unavailable.",
        ) from None


@router.post("/analyze", response_model=AnxietyAnalysisResponse)
def analyze_anxiety(payload: AnxietyAnalysisRequest):
    """Validate and classify seven responses in memory."""
    try:
        responses = validate_responses(payload.responses)
    except InvalidAnxietyResponsesError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None

    classifier = classifier_dependency()
    try:
        return AnxietyAnalysisResponse(**classifier.analyze(responses))
    except InvalidAnxietyResponsesError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The anxiety screening could not be analyzed. Please try again.",
        ) from None
