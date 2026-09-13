"""
FastAPI application for Intelligent Email Security Detection.
"""
import os

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from src.predict import EmailSecurityPredictor
from src.scanner import EmailScanner
from src.preprocessing import validate_email_content
from src.connectors.gmail import ( create_gmail_flow, get_gmail_credentials, list_gmail_messages, get_gmail_message_raw,  scan_gmail_messages , get_gmail_account_email,)
from src.config import (
    FRONTEND_URL,
    SESSION_SECRET_KEY,
)
from src.oauth_storage import (
    save_oauth_account,
    get_oauth_account,
    get_refresh_token,
    delete_oauth_account,
)
from src.session import generate_session_id



os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

app = FastAPI(
    title="Intelligent Email Security Detection API",
    description="API for Spam and Phishing Email Risk Analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    https_only=False,
    same_site="lax"
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

class ScanResultResponse(BaseModel):
    message_id: str
    thread_id: str | None = None
    subject: str = ""
    sender: str = ""
    date: str = ""
    status: str
    category: str | None = None
    spam_score: float | None = None
    spam_decision: str | None = None
    phishing_score: float | None = None
    phishing_decision: str | None = None
    risk_level: str | None = None
    reasons: list[str] = []
    error: str | None = None


class ScanSummaryResponse(BaseModel):
    total: int
    successful: int
    errors: int
    spam: int
    maybe_spam: int
    phishing: int
    both: int
    none: int


class GmailScanResponse(BaseModel):
    summary: ScanSummaryResponse
    results: list[ScanResultResponse]
    next_page_token: str | None = None


predictor = EmailSecurityPredictor()


scanner = EmailScanner(
    predictor=predictor
)



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


@app.get("/auth/gmail")
def gmail_login(request : Request):
    flow = create_gmail_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    request.session["oauth_state"] = state

    return RedirectResponse(
        url=authorization_url
    )


@app.get("/auth/gmail/callback")
def gmail_callback(request: Request):
    state = request.session.get("oauth_state")

    if not state:
        raise HTTPException(
            status_code=400,
            detail="OAuth session state is missing."
        )

    flow = create_gmail_flow()
    flow.state = state

    try:
        flow.fetch_token(
            authorization_response=str(request.url)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Gmail OAuth failed: {exc}"
        )

    credentials = flow.credentials

    if not credentials.refresh_token:
        raise HTTPException(
            status_code=400,
            detail=(
                "Gmail authorization did not provide a refresh token. "
                "Please authorize Gmail again."
            )
        )

    try:
        email_address = get_gmail_account_email(
            credentials
        )

        session_id = generate_session_id()

        save_oauth_account(
            session_id=session_id,
            email_address=email_address,
            refresh_token=credentials.refresh_token
        )

    except Exception:
        import traceback
        traceback.print_exc()
        raise
    request.session.clear()

    request.session["session_id"] = session_id

    return RedirectResponse(
        url=FRONTEND_URL
    )

@app.get("/gmail/messages")
def gmail_messages(request: Request, limit: int = 5):
    session_id = request.session.get("session_id")

    if not session_id:
        raise HTTPException(
          status_code=401,
          detail="Gmail account is not connected."
        )

    refresh_token = get_refresh_token(session_id)

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Gmail account is not connected."
        )

    try:
        credentials = get_gmail_credentials(refresh_token)

        page = list_gmail_messages(
            credentials=credentials,
            limit=limit
        )

        return {
            "count": len(page["messages"]),
            "messages": page["messages"],
            "next_page_token": page["next_page_token"]
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.get("/gmail/messages/{message_id}/raw")
def gmail_message_raw(
    request: Request,
    message_id: str
):
    session_id = request.session.get("session_id")

    if not session_id:
        raise HTTPException(
          status_code=401,
          detail="Gmail account is not connected."
        )

    refresh_token = get_refresh_token(session_id)

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Gmail account is not connected."
        )

    try:
        credentials = get_gmail_credentials(refresh_token)

        raw_bytes = get_gmail_message_raw(
            credentials=credentials,
            message_id=message_id
        )

        return {
            "message_id": message_id,
            "size_bytes": len(raw_bytes),
            "message_preview": raw_bytes[:200].decode(
                "utf-8",
                errors="replace"
            )
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.get("/gmail/messages/{message_id}/predict")
def predict_gmail_message(
    request: Request,
    message_id: str
):
    session_id = request.session.get("session_id")

    if not session_id:
        raise HTTPException(
          status_code=401,
          detail="Gmail account is not connected."
        )

    refresh_token = get_refresh_token(session_id)

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Gmail account is not connected."
        )

    try:
        credentials = get_gmail_credentials(refresh_token)

        raw_bytes = get_gmail_message_raw(
            credentials=credentials,
            message_id=message_id
        )

        result = predictor.predict_raw_email(raw_bytes)

        return {
            "message_id": message_id,
            "result": result
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )




@app.get(
    "/gmail/scan",
    response_model=GmailScanResponse
)
def scan_gmail(
    request: Request,
    limit: int = 20,
    page_token: str | None = None
):

    session_id = request.session.get("session_id")

    if not session_id:
        raise HTTPException(
          status_code=401,
          detail="Gmail account is not connected."
        )

    refresh_token = get_refresh_token(session_id)

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Gmail account is not connected."
        )


        

    if limit <= 0:
        raise HTTPException(
            status_code=400,
            detail="limit must be greater than zero."
        )

    if limit > 20:
        raise HTTPException(
            status_code=400,
            detail="For now, limit cannot exceed 20."
        )

    try:
        credentials = get_gmail_credentials(refresh_token)
        

        scan_result = scan_gmail_messages(
            credentials=credentials,
            limit=limit,
            page_token=page_token
        )

        results = scanner.scan_messages(
            scan_result["results"]
        )


        summary = scanner.summarize_results(
            results
        )

        return {
            "summary": summary,
            "results": results,
            "next_page_token": scan_result["next_page_token"]
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.get("/auth/gmail/status")
def gmail_status(request: Request):
    session_id = request.session.get("session_id")

    if not session_id:
        raise HTTPException(
          status_code=401,
          detail="Gmail account is not connected."
        )

    refresh_token = get_refresh_token(session_id)

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Gmail account is not connected."
        )

    
        


    return {
        "connected": True
    }