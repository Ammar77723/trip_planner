"""
Main application entry point for the Airspace Copilot system.
Provides API endpoints for the frontend.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from agents.crew import AirspaceCopilotCrew
import uvicorn

app = FastAPI(title="Airspace Copilot API", version="1.0.0")

# Initialize the crew
crew = AirspaceCopilotCrew()


class RegionAnalysisRequest(BaseModel):
    region: str = "data"


class TravelerQuestionRequest(BaseModel):
    question: str
    callsign: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Airspace Copilot API",
        "version": "1.0.0",
        "endpoints": {
            "analyze_region": "/api/analyze-region",
            "answer_question": "/api/answer-question",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}


@app.post("/api/analyze-region")
async def analyze_region(request: RegionAnalysisRequest):
    """
    Analyze a region and get operational summary.
    
    This uses the Ops Analyst Agent.
    """
    try:
        summary = crew.analyze_region(request.region)
        return {
            "success": True,
            "region": request.region,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/answer-question")
async def answer_question(request: TravelerQuestionRequest):
    """
    Answer a traveler's question about their flight.
    
    This uses the Traveler Support Agent (with A2A communication if needed).
    """
    try:
        answer = crew.answer_traveler_question(
            question=request.question,
            callsign=request.callsign
        )
        return {
            "success": True,
            "question": request.question,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("=" * 50)
    print("Airspace Copilot API Server")
    print("=" * 50)
    print("API URL: http://localhost:8001")
    print("API Docs: http://localhost:8001/docs")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)

