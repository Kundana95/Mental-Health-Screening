"""Separate HTTP contract for experimental Reddit text classification."""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from modules.schizophrenia.classifier import (
    MAX_TEXT_LENGTH,
    InvalidTextError,
    ModelsUnavailableError,
    get_classifier,
    validate_text,
)

router = APIRouter(prefix="/api/schizophrenia")


class TextAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: StrictStr = Field(min_length=1, max_length=MAX_TEXT_LENGTH)

    @field_validator("text")
    @classmethod
    def nonblank_text(cls, text):
        validate_text(text)
        return text


class TextAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal["general_community", "schizophrenia_community"]
    model_id: str
    limitations: list[str]


def classifier_dependency():
    try:
        return get_classifier()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Text classification is temporarily unavailable.",
        ) from None


@router.post("/analyze", response_model=TextAnalysisResult)
def analyze_text(payload: TextAnalysisRequest):
    # Resolve models after body validation so malformed requests always get 422.
    classifier = classifier_dependency()
    try:
        # Construct inside the error boundary, keeping malformed model output private.
        return TextAnalysisResult(**classifier.analyze(payload.text))
    except InvalidTextError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except ModelsUnavailableError:
        raise HTTPException(
            status_code=503, detail="Text classification is temporarily unavailable."
        ) from None
    except Exception:
        raise HTTPException(
            status_code=500, detail="The text could not be analyzed. Please try again."
        ) from None
