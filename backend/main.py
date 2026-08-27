from fastapi import FastAPI, HTTPException, Header, Query, Depends, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
from typing import Optional, Dict, Any

from database import init_db, create_session, get_form_data, get_chat_history, update_form_data, get_session_by_api_key
from chatbot import process_chat_message, normalize_form_updates, get_next_question
from pdf_engine import generate_pdf

app = FastAPI(title="Chatbot to PDF Government Form Filler")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup DB initialization
@app.on_event("startup")
def startup_event():
    init_db()

# Custom API authentication dependency
def get_session_from_auth(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None)
):
    key = x_api_key
    
    # Try parsing Authorization header (Bearer token)
    if not key and authorization:
        if authorization.startswith("Bearer "):
            key = authorization[7:]
        else:
            key = authorization
            
    # Try query param (necessary for browser PDF preview iframes)
    if not key:
        key = api_key
        
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Provide it in X-API-KEY header, Authorization Bearer header, or api_key query parameter."
        )
        
    session = get_session_by_api_key(key)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API Key."
        )
        
    return session

# Pydantic models for client validation
class ChatRequest(BaseModel):
    message: str

# API Endpoints

# 1. Create session (Assigns a custom user API Key)
@app.post("/api/session")
def api_create_session():
    session_id = str(uuid.uuid4())
    # Generate user-facing API key
    user_api_key = f"sk_form_{uuid.uuid4().hex[:16]}"
    create_session(session_id, user_api_key)
    
    initial_form_data = get_form_data(session_id)
    return {
        "session_id": session_id,
        "user_api_key": user_api_key,
        "form_data": initial_form_data,
        "initial_question": get_next_question(initial_form_data),
        "chat_history": []
    }

# 2. Get active session state using API Key
@app.get("/api/session")
def api_get_session(session: dict = Depends(get_session_from_auth)):
    session_id = session["session_id"]
    current_form_data = get_form_data(session_id)
    return {
        "session_id": session_id,
        "user_api_key": session["user_api_key"],
        "form_data": current_form_data,
        "initial_question": get_next_question(current_form_data),
        "chat_history": get_chat_history(session_id)
    }

# 3. Post a message to chatbot using API Key
@app.post("/api/chat")
def api_chat(req: ChatRequest, session: dict = Depends(get_session_from_auth)):
    session_id = session["session_id"]
    reply = process_chat_message(session_id, req.message)
    
    return {
        "reply": reply,
        "form_data": get_form_data(session_id),
        "chat_history": get_chat_history(session_id)
    }

# 4. Update form fields directly (manual override) using API Key
@app.put("/api/form-data")
def api_update_form(data: Dict[str, Any], session: dict = Depends(get_session_from_auth)):
    session_id = session["session_id"]
    normalized_data = normalize_form_updates(data)
    update_form_data(session_id, normalized_data)
    
    return {
        "status": "success",
        "form_data": get_form_data(session_id)
    }

# 5. Live PDF preview using API Key (Query param api_key is used by iframe)
@app.get("/api/pdf/preview")
def api_pdf_preview(session: dict = Depends(get_session_from_auth)):
    session_id = session["session_id"]
    form_data = get_form_data(session_id)
    try:
        pdf_path = generate_pdf(session_id, form_data)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF generation failed")
        return FileResponse(pdf_path, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering PDF: {str(e)}")

# 6. PDF download using API Key
@app.get("/api/pdf/download")
def api_pdf_download(session: dict = Depends(get_session_from_auth)):
    session_id = session["session_id"]
    form_data = get_form_data(session_id)
    try:
        pdf_path = generate_pdf(session_id, form_data)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF generation failed")
        return FileResponse(
            pdf_path, 
            media_type="application/pdf", 
            filename=f"Parishisht_5_{session_id[:8]}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")

# Developer Integration APIs (v1)

# Fetch user's data programmatically using Custom Key
@app.get("/api/v1/form-data")
def api_v1_get_data(session: dict = Depends(get_session_from_auth)):
    session_id = session["session_id"]
    return {
        "user_api_key": session["user_api_key"],
        "form_data": get_form_data(session_id)
    }

# Submit / Update user's data programmatically using Custom Key
@app.post("/api/v1/form-data")
def api_v1_post_data(data: Dict[str, Any], session: dict = Depends(get_session_from_auth)):
    session_id = session["session_id"]
    normalized_data = normalize_form_updates(data)
    update_form_data(session_id, normalized_data)
    
    # Regenerate PDF automatically to ensure form is in sync
    generate_pdf(session_id, get_form_data(session_id))
    
    return {
        "status": "success",
        "user_api_key": session["user_api_key"],
        "form_data": get_form_data(session_id)
    }

# Mount static folder
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount templates folder (for developer calibration tools)
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
app.mount("/templates", StaticFiles(directory=templates_dir), name="templates")

# Frontend dist folder check
frontend_dist_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist"))
frontend_assets_dir = os.path.join(frontend_dist_dir, "assets")
if os.path.exists(frontend_assets_dir):
    app.mount("/assets", StaticFiles(directory=frontend_assets_dir), name="frontend_assets")

# Serve index.html on root
@app.get("/")
def serve_index():
    frontend_index = os.path.join(frontend_dist_dir, "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to Chatbot to PDF Backend! Client application is loading..."}
