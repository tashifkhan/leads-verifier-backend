# Lead Scoring Backend (FastAPI + LangChain + LangGraph + uv)

Implements a backend service to score leads' buying intent (High / Medium / Low) using a combination of rule-based logic and AI reasoning, orchestrated with LangChain and LangGraph, and served with the high-performance `uv` ASGI server.

## Features

- Upload a Product/Offer JSON
- Upload Leads via CSV
- Score using a rule layer (0–50) + AI layer (0–50)
- Retrieve results (JSON) or export CSV
- Interactive API docs at /docs

## Project Structure

- app/models.py: Pydantic models, in-memory storage
- app/scoring_logic.py: Deterministic rule-based scoring
- app/llm_chain.py: LangChain prompt + Gemini model + response parsing
- app/scoring_workflow.py: LangGraph workflow orchestrating steps
- app/main.py: FastAPI app and endpoints

## Setup

1. Python 3.12+ and uv tool available
2. Set the Gemini API key:

Create a `.env` file in repo root:

    GEMINI_API_KEY=your_key_here

3. Install dependencies (managed by pyproject.toml):

   uv pip install -e .

## Run

Launch the API server (hot reload):

    uv run app.main:app --reload --port 8000

Then open http://localhost:8000/docs

## Endpoints (Quick Reference)

- POST /offer: Upload product/offer JSON
- POST /leads/upload: Upload leads CSV (columns: name, role, company, industry, location, linkedin_bio)
- POST /score: Execute scoring workflow for uploaded leads
- GET /results: Get scored leads as JSON
- GET /results/csv: Download scored leads as CSV

## Notes

- For assignment scope, data is stored in-memory and resets when the server restarts.
- Rule layer: role relevance, ICP overlap, completeness (max 50).
- AI layer: Gemini classifies intent + reasoning; intent mapped to points (High=50, Medium=30, Low=10).

## Docker

Build the image:

```bash
docker build -t assignment-backend:latest .
```

Run the container (requires `GEMINI_API_KEY`):

```bash
docker run --rm -p 8000:8000 \
    -e GEMINI_API_KEY=your_key_here \
    assignment-backend:latest
```

Now open http://localhost:8000/docs
