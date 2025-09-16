"""Dev helper entrypoint.

This project exposes a FastAPI app at app.main:app.
Run the server with:

    uv run app.main:app --reload --port 8000

"""

from app.main import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        port=8000,
    )
