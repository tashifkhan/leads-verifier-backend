# Vercel Python serverless entrypoint for FastAPI app
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.main import app as fastapi_app

# Optionally wrap/extend if needed
app: FastAPI = fastapi_app

# Enable CORS for local dev and Vercel previews if desired
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
