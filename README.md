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

Prereqs:

- Python 3.12+
- uv tool (for local dev) or Docker (for containerized run)

1. Create a `.env` in repo root with your Gemini API key:

```
GEMINI_API_KEY=your_key_here
```

2. Install dependencies for local dev (using uv):

```bash
uv pip install -e .
```

## Run

Launch the API server (hot reload):

```bash
uv run app.main:app --reload --port 8000
```

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

## API usage examples (cURL)

Assumes server running at http://localhost:8000

1. Upload Offer

```bash
curl -X POST http://localhost:8000/offer \
    -H 'Content-Type: application/json' \
    -d '{
                "name": "Acme Analytics",
                "value_props": ["Faster dashboards", "Cost-effective"],
                "ideal_use_cases": ["SaaS analytics", "data-driven marketing teams"]
            }'
```

2. Upload Leads (CSV)

CSV must have columns: name, role, company, industry, location, linkedin_bio.

```bash
curl -X POST http://localhost:8000/leads/upload \
    -H 'Content-Type: multipart/form-data' \
    -F 'file=@/path/to/leads.csv'
```

3. Run Scoring

```bash
curl -X POST http://localhost:8000/score
```

4. Get Results (JSON)

```bash
curl http://localhost:8000/results
```

5. Download Results (CSV)

```bash
curl -L -o scored_leads.csv http://localhost:8000/results/csv
```

## Rule logic explained

The deterministic rule score (0–50), implemented in `app/scoring_logic.py`, comprises:

- Role relevance (0–20):
  - Title contains decision-maker keywords (e.g., head, director, vp, cxo, ceo, cto, cmo, founder, owner, lead): +20
  - Title contains influencer keywords (e.g., manager, specialist, analyst, coordinator, associate): +10
  - Otherwise: +0
- ICP/industry match (0–20):
  - Token overlap between `offer.ideal_use_cases` and the lead's `industry` string.
  - 2+ overlapping tokens: +20; exactly 1 token: +10; else: +0
- Data completeness (0–10):
  - All of name, role, company, industry, location, linkedin_bio are non-empty.

The final rule score is bounded to 0..50.

## Prompt and AI mapping

The LLM prompt (see `app/llm_chain.py`) requests a fixed two-line response:

```
Intent: <High|Medium|Low>
Reasoning: <one or two concise sentences>
```

We parse the intent via regex and map it to points:

- High → 50 points
- Medium → 30 points
- Low → 10 points

These AI points combine with the rule score to produce the `final_score`.

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
