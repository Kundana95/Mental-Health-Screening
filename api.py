"""Local API adapter for the existing Mindful assessment scoring logic."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr
from starlette.middleware.trustedhost import TrustedHostMiddleware

from modules.assessment_result import (
    build_unified_assessment_result,
    validate_unified_assessment_submission,
)
from modules.schizophrenia.api import router as schizophrenia_router


class DepressionAssessmentRequest(BaseModel):
    """Answers accepted by the unified depression assessment endpoint."""

    model_config = ConfigDict(extra="forbid")

    phq9_responses: list[StrictInt | None]
    gad7_responses: list[StrictInt | None]
    context_answers: dict[StrictStr, StrictStr | None]


MAX_REQUEST_BODY_BYTES = 16 * 1024

app = FastAPI(
    title="Mindful Assessment API",
    version="1.0.0",
    debug=False,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "testserver"],
)


@app.middleware("http")
async def limit_request_body(request: Request, call_next):
    """Keep the local assessment endpoint's JSON request body small."""
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request."},
            )
        if declared_size < 0 or declared_size > MAX_REQUEST_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body is too large."},
            )

    body = await request.body()
    if len(body) > MAX_REQUEST_BODY_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body is too large."},
        )
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request: Request, error: RequestValidationError):
    """Avoid echoing submitted values from framework validation errors."""
    if request.url.path == "/api/schizophrenia/analyze":
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid text submission. Provide non-empty text of at most 4000 characters."},
        )
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid assessment submission. Please review your answers."},
    )


@app.post("/api/depression/submit")
def submit_depression_assessment(payload: DepressionAssessmentRequest):
    """Validate and process the assessment, returning only a neutral receipt."""
    try:
        validate_unified_assessment_submission(
            payload.phq9_responses,
            payload.gad7_responses,
            payload.context_answers,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The assessment could not be processed. Please try again.",
        ) from None

    try:
        # Keep the complete structured result available inside the server while
        # returning only what the current React UI needs.
        assessment_result = build_unified_assessment_result(
            payload.phq9_responses,
            payload.gad7_responses,
            payload.context_answers,
        )
    except Exception:
        # Do not let an unexpected exception include request data in the HTTP
        # response or escape to default traceback logging.
        raise HTTPException(
            status_code=500,
            detail="The assessment could not be processed. Please try again.",
        ) from None

    return {"status": "received", "message": "Your responses were received."}


app.include_router(schizophrenia_router)
