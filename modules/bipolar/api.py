"""HTTP interface for the experimental bipolar screening prototype."""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from modules.bipolar.classifier import (
    BipolarModelUnavailableError,
    InvalidBipolarAnswersError,
    LIMITATIONS,
    get_classifier,
    validate_answers,
)


router = APIRouter(prefix="/api/bipolar")


class BipolarAnalysisRequest(BaseModel):
    """Strict request schema preserving the model's original feature names."""

    model_config = ConfigDict(extra="forbid", strict=True)

    sadness: StrictStr = Field(alias="Sadness")
    euphoric: StrictStr = Field(alias="Euphoric")
    exhausted: StrictStr = Field(alias="Exhausted")
    sleep_dissorder: StrictStr = Field(alias="Sleep dissorder")
    mood_swing: StrictStr = Field(alias="Mood Swing")
    aggressive_response: StrictStr = Field(alias="Aggressive Response")
    admit_mistakes: StrictStr = Field(alias="Admit Mistakes")
    overthinking: StrictStr = Field(alias="Overthinking")
    concentration: StrictInt = Field(alias="Concentration")
    optimisim: StrictInt = Field(alias="Optimisim")

    def feature_answers(self):
        return self.model_dump(by_alias=True)


class BipolarAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["Bipolar Type 1", "Bipolar Type 2", "No Bipolar Indication"]
    message: str
    limitations: list[str]


def classifier_dependency():
    try:
        return get_classifier()
    except BipolarModelUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="Bipolar screening is temporarily unavailable.",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Bipolar screening is temporarily unavailable.",
        ) from None


@router.post("/analyze", response_model=BipolarAnalysisResponse)
def analyze_bipolar(payload: BipolarAnalysisRequest):
    """Validate and classify a single in-memory set of model inputs."""
    try:
        answers = validate_answers(payload.feature_answers())
    except InvalidBipolarAnswersError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None

    classifier = classifier_dependency()
    try:
        result = classifier.analyze(answers)
        category = result["category"]
        if category == "No Bipolar Indication":
            message = (
                "The experimental model returned No Bipolar Indication for these inputs. "
                "This result cannot rule out bipolar disorder."
            )
        else:
            message = (
                f"The experimental model returned the {category} category for these inputs. "
                "This is not a diagnosis."
            )
        return BipolarAnalysisResponse(
            category=category,
            message=message,
            limitations=list(LIMITATIONS),
        )
    except InvalidBipolarAnswersError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The assessment could not be analyzed. Please try again.",
        ) from None
