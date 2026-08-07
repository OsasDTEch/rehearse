"""Rehearse API. Mints LiveKit room tokens, serves scenario config, generates feedback."""
import os
import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from pydantic import BaseModel, Field

from .llm_router import generate_feedback
from .logger import log_event
from .scenarios import SCENARIOS, MOODS

app = FastAPI(title="Rehearse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")


class StartSessionRequest(BaseModel):
    scenario_id: str
    mood: str = "friendly"


class TranscriptTurn(BaseModel):
    speaker: str
    text: str


class FeedbackRequest(BaseModel):
    scenario_id: str
    transcript: list[TranscriptTurn] = Field(default_factory=list)


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/scenarios")
async def list_scenarios():
    return {
        "scenarios": [
            {k: s[k] for k in ("id", "title", "blurb", "opening_hint")}
            for s in SCENARIOS.values()
        ],
        "moods": list(MOODS.keys()),
    }


@app.post("/api/session")
async def start_session(req: StartSessionRequest):
    if req.scenario_id not in SCENARIOS:
        raise HTTPException(404, "Unknown scenario")
    if req.mood not in MOODS:
        raise HTTPException(400, "Unknown mood")

    session_id = uuid.uuid4().hex[:12]
    room_name = f"rehearse-{session_id}"

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(f"user-{session_id}")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        # Scenario + mood travel to the agent via room metadata-free path:
        # the agent reads them from participant attributes set here.
        .with_attributes({"scenario_id": req.scenario_id, "mood": req.mood})
        .to_jwt()
    )

    log_event("session_started", session_id=session_id, scenario=req.scenario_id, mood=req.mood)
    return {
        "session_id": session_id,
        "room": room_name,
        "token": token,
        "livekit_url": LIVEKIT_URL,
        "scenario": {
            k: SCENARIOS[req.scenario_id][k]
            for k in ("id", "title", "opening_hint")
        },
    }


@app.post("/api/feedback")
async def feedback(req: FeedbackRequest):
    if req.scenario_id not in SCENARIOS:
        raise HTTPException(404, "Unknown scenario")
    result = await generate_feedback(
        [t.model_dump() for t in req.transcript],
        SCENARIOS[req.scenario_id]["title"],
    )
    log_event("feedback_served", scenario=req.scenario_id, turns=len(req.transcript))
    return result
