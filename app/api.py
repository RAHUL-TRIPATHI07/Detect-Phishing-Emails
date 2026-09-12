"""
FastAPI application for Intelligent Email Security Detection.
"""

from fastapi import FastAPI, UploadFile, File , HTTPException
from pydantic import BaseModel

from src.predict import EmailSecurityPredictor
from src.preprocessing import validate_email_content


app = FastAPI(
    title="Intelligent Email Security Detection API",
    description="API for Spam and Phishing Email Risk Analysis",
    version="1.0.0"
)


class EmailRequest(BaseModel):
    subject: str
    body: str


class EmailPredictionResponse(BaseModel):
    spam_score: float
    spam_decision: str
    phishing_score: float
    phishing_decision: str
    risk_level: str
    reasons: list[str]


predictor = EmailSecurityPredictor()


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post(
    "/predict",
    response_model=EmailPredictionResponse
)
def predict_email(request: EmailRequest):

    try:
        return predictor.predict_email(
            subject=request.subject,
            body=request.body
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post(
    "/predict/raw",
    response_model=EmailPredictionResponse
)
async def predict_raw_email(file: UploadFile = File(...)):

    raw_bytes = await file.read()

    if not raw_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if not validate_email_content(raw_bytes):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file does not contain a valid email message."
        )

    try:
        return predictor.predict_raw_email(raw_bytes)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )