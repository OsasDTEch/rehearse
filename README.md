# Rehearse

A judgment free voice agent for practicing everyday conversations out loud, at your own pace. Built for the IncludAI Neurodiversity Hackathon, Track 2 (AI for Connection and Wellbeing).

**The promise:** you control the pace, always. Pause, slow down, restart, or stop at any moment. A safety layer written in code (not left to the LLM) drops the agent out of character the instant you signal distress.

## Architecture

```
Browser (React + Tailwind + LiveKit client)
   │  WebRTC audio + data messages (control / state topics)
   ▼
LiveKit Cloud room
   │
   ├── Agent worker (livekit-agents)
   │     Deepgram STT (Flux) → tripwire (code) → LLM → Deepgram TTS
   │     LLM = FallbackAdapter[ Ollama cloud gemma4:31b-cloud → Groq llama-3.3-70b ]
   │
   └── FastAPI backend
         /api/session   mints room token, scenario+mood ride in token attributes
         /api/scenarios serves scenario config (config as data)
         /api/feedback  post-session feedback, Ollama primary → Groq fallback
```

Key design decisions:
- **Tripwire before the LLM.** `on_user_turn_completed` checks the user's transcript against distress patterns in code and raises `StopResponse` so the model never gets the turn. The agent speaks a fixed de-escalation line and permanently enters safe mode.
- **Persona ceiling.** Every system prompt ends with hard rules: no mockery, no rushing, one question at a time, plain language.
- **User speaks first.** The agent never opens unless the user taps "Let them start". Predictability is an accessibility feature.
- **UTC-only timestamps, JSON-lines logging, per-turn latency spans** in `backend/app/logger.py`.

## Setup

Prereqs: Python 3.11+, Node 20+, accounts on LiveKit Cloud, Deepgram, Ollama cloud, Groq.

### Backend

```bash
cd backend
uv sync                    # creates .venv and installs all deps
cp .env.example .env       # fill in your keys (or use the root .env)
```

Download agent model files (VAD), then run the two processes:

```bash
uv run -m livekit.agents download-files
uv run uvicorn app.main:app --port 8000    # terminal 1: API
uv run python agent/agent.py dev           # terminal 2: agent worker
```

### Frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173, proxies /api to :8000
```

## Deploying

Same pattern as HeatDesk: backend + agent worker behind Nginx on the VPS, frontend built with `npm run build` and served statically. Set `CORS_ORIGINS` and `VITE_API_BASE` for the public domain.

## Testing the tripwire without a mic

Say or type nothing; instead run a session and say "stop" or "this is too much". The scenario halts immediately, the UI shifts to the calm lavender state, and the agent speaks the de-escalation line. This path never touches the LLM.

## Roadmap (post-hackathon)

- Impatient mood setting, gated on tester validation
- Custom scenario builder
- Saved progress, opt-in only
- More languages
