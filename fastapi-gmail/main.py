
import os
import pickle
import pathlib

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow

app = FastAPI()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

BASE_DIR = pathlib.Path(__file__).resolve().parent
GOOGLE_CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

BASE_DIR = pathlib.Path(__file__).resolve().parent
GOOGLE_CLIENT_ID = BASE_DIR / "client_secret.json"

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<a href='/authorize'>Authorize with Google</a>"
            
@app.get("/authorize")
async def authorize():
    flow = Flow.from_client_secrets_file(
        str(GOOGLE_CLIENT_SECRET_FILE),
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/oauth2callback"
    )
    
    authorization_url, _ = flow.authorization_url(prompt='consent')
    
    return RedirectResponse(url=authorization_url)
            
@app.get("/oauth2callback")
async def oauth2callback(request: Request):
    flow = Flow.from_client_secrets_file(
        str(GOOGLE_CLIENT_ID),
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        redirect_uri="http://localhost:8000/oauth2callback"
    )
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    access_token = credentials.token
    
    return HTMLResponse(f"<h3>Access Token:</h3><pre>{access_token}</pre>")