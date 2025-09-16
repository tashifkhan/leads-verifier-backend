from __future__ import annotations

import io
from typing import List

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .models import (
    Lead,
    ProductOffer,
    ScoredLead,
    ScoringState,
    current_offer,
    scored_leads,
    uploaded_leads,
)
from .scoring_workflow import scoring_workflow


app = FastAPI(
    title="Lead Scoring Backend (LangChain + LangGraph)",
    description=(
        "Upload an offer and a CSV of leads, then score them using rules + AI."
    ),
    version="0.1.0",
)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Lead Scoring API. Visit /docs for OpenAPI UI."}


@app.post("/offer", summary="Upload Product/Offer details")
async def upload_offer(offer: ProductOffer):
    global current_offer
    current_offer = offer
    return {
        "message": "Product offer uploaded successfully",
        "offer": offer.model_dump(),
    }


@app.post("/leads/upload", summary="Upload Leads CSV file")
async def upload_leads(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):  # type: ignore
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    required_cols = ["name", "role", "company", "industry", "location", "linkedin_bio"]
    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing column in CSV: {col}")

    uploaded_leads.clear()
    for _, row in df.iterrows():
        lead = Lead(
            name=str(row.get("name", "")),
            role=str(row.get("role", "")),
            company=str(row.get("company", "")),
            industry=str(row.get("industry", "")),
            location=str(row.get("location", "")),
            linkedin_bio=str(row.get("linkedin_bio", "")),
        )
        uploaded_leads.append(lead)

    return {"message": f"Uploaded {len(uploaded_leads)} leads."}


@app.post("/score", summary="Run scoring on uploaded leads")
async def run_scoring():
    if current_offer is None:
        raise HTTPException(
            status_code=400, detail="No offer uploaded. POST /offer first."
        )
    if not uploaded_leads:
        raise HTTPException(
            status_code=400, detail="No leads uploaded. POST /leads/upload first."
        )

    scored_leads.clear()
    for lead in uploaded_leads:
        initial_state: ScoringState = {
            "lead": lead,
            "offer": current_offer,
        }
        result_state: ScoringState = await scoring_workflow.ainvoke(initial_state)  # type: ignore
        scored = ScoredLead(
            name=lead.name,
            role=lead.role,
            company=lead.company,
            industry=lead.industry,
            location=lead.location,
            linkedin_bio=lead.linkedin_bio,
            intent=result_state.get("ai_intent", "Low"),
            score=int(result_state.get("final_score", 0)),
            reasoning=result_state.get("ai_reasoning", ""),
        )
        scored_leads.append(scored)

    return {
        "message": f"Scoring complete for {len(scored_leads)} leads.",
        "total_scored": len(scored_leads),
    }


@app.get("/results", response_model=List[ScoredLead], summary="Get scored leads")
async def get_results():
    return scored_leads


@app.get("/results/csv", summary="Export scored leads as CSV")
async def export_results_csv():
    if not scored_leads:
        raise HTTPException(
            status_code=400,
            detail="No scored leads. POST /score first.",
        )
    # Build DataFrame
    df = pd.DataFrame([s.model_dump() for s in scored_leads])
    stream = io.StringIO()
    df.to_csv(
        stream,
        index=False,
    )
    stream.seek(0)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="scored_leads.csv"',
        },
    )
