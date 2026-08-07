"""Rehearse voice agent worker.

Run:  python agent/agent.py download-files   (once, fetches VAD weights)
      python agent/agent.py dev              (local development)
      python agent/agent.py start            (production)

Design notes:
- Distress tripwire runs in code inside on_user_turn_completed, BEFORE the LLM
  is invoked. If it fires, the LLM never gets the turn: we speak the fixed
  de-escalation line and permanently switch the session into safe mode.
- Deepgram Flux (STTv2) handles end-of-turn detection, so turn_detection="stt".
- Ollama cloud is the primary LLM, Groq the fallback, wired through LiveKit's
  FallbackAdapter so mid-session failover is automatic.
- Frontend controls (pause / slower / restart / end) arrive as data messages
  on the "control" topic; the agent reports state on the "state" topic.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    StopResponse,
    WorkerOptions,
    cli,
    llm as lk_llm,
)
from livekit.plugins import deepgram, openai as openai_plugin, silero

from app import tripwire
from app.logger import log_event, TurnTimer
from app.scenarios import SCENARIOS, build_instructions, SLOW_MODE_NOTE

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
GROQ_BASE = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DEEPGRAM_STT_MODEL = os.getenv("DEEPGRAM_STT_MODEL", "flux-general-en")
DEEPGRAM_TTS_MODEL = os.getenv("DEEPGRAM_TTS_MODEL", "aura-2-thalia-en")


class RehearseAgent(Agent):
    def __init__(self, instructions: str, session_id: str, room: rtc.Room):
        super().__init__(instructions=instructions)
        self.session_id = session_id
        self.room = room
        self.safe_mode = False
        self.slow_mode = False
        self.turn_count = 0

    async def on_user_turn_completed(
        self, turn_ctx: lk_llm.ChatContext, new_message: lk_llm.ChatMessage
    ) -> None:
        self.turn_count += 1
        text = new_message.text_content or ""
        timer = TurnTimer(self.session_id, self.turn_count)
        timer.mark("user_turn_final")

        log_event("user_turn", session_id=self.session_id, turn=self.turn_count, text=text)

        # ---- TRIPWIRE: code decides before the model ever sees the turn ----
        if not self.safe_mode and tripwire.check(text):
            self.safe_mode = True
            log_event(
                "tripwire_fired",
                session_id=self.session_id,
                turn=self.turn_count,
                text=text,
            )
            await self.update_instructions(tripwire.SAFE_MODE_INSTRUCTIONS)
            self.session.say(tripwire.DEESCALATION_LINE)
            await self.publish_state({"type": "safe_mode", "active": True})
            timer.mark("deescalation_spoken")
            timer.close()
            raise StopResponse()

        if self.slow_mode and not self.safe_mode:
            turn_ctx.add_message(role="system", content=SLOW_MODE_NOTE)

        timer.mark("handed_to_llm")
        timer.close()

    async def publish_state(self, payload: dict) -> None:
        try:
            await self.room.local_participant.publish_data(
                json.dumps(payload).encode(), topic="state", reliable=True
            )
        except Exception as e:
            log_event("state_publish_failed", error=str(e)[:200])


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    # Wait for the human; scenario + mood ride in on their token attributes.
    participant = await ctx.wait_for_participant()
    attrs = participant.attributes or {}
    scenario_id = attrs.get("scenario_id", "restaurant")
    mood = attrs.get("mood", "friendly")
    session_id = ctx.room.name.removeprefix("rehearse-")

    if scenario_id not in SCENARIOS:
        scenario_id = "restaurant"

    instructions = build_instructions(scenario_id, mood)
    log_event("agent_joined", session_id=session_id, scenario=scenario_id, mood=mood)

    primary_llm = openai_plugin.LLM(
        model=OLLAMA_MODEL, base_url=OLLAMA_BASE, api_key=OLLAMA_KEY, temperature=0.6
    )
    fallback_llm = openai_plugin.LLM(
        model=GROQ_MODEL, base_url=GROQ_BASE, api_key=GROQ_KEY, temperature=0.6
    )

    agent = RehearseAgent(instructions=instructions, session_id=session_id, room=ctx.room)

    session = AgentSession(
        stt=deepgram.STTv2(model=DEEPGRAM_STT_MODEL),
        llm=lk_llm.FallbackAdapter([primary_llm, fallback_llm]),
        tts=deepgram.TTS(model=DEEPGRAM_TTS_MODEL),
        vad=silero.VAD.load(),
        turn_detection="stt",  # Flux provides end-of-turn events
    )

    def on_data(packet: rtc.DataPacket):
        if packet.topic != "control":
            return
        try:
            msg = json.loads(packet.data.decode())
        except Exception:
            return
        action = msg.get("action")
        log_event("control", session_id=session_id, action=action)

        if action == "pause":
            session.interrupt()
            session.input.set_audio_enabled(False)
        elif action == "resume":
            session.input.set_audio_enabled(True)
        elif action == "slower":
            agent.slow_mode = True
            session.say("Sure. I'll slow down.")
        elif action == "agent_start":
            session.say(SCENARIOS[scenario_id]["agent_opener"])
        elif action == "restart":
            agent.safe_mode = False
            agent.slow_mode = False
            session.interrupt()
            asyncio.create_task(agent.update_instructions(instructions))
            asyncio.create_task(agent.publish_state({"type": "safe_mode", "active": False}))
            session.say("Okay, starting fresh. Take your time.")

    ctx.room.on("data_received", on_data)

    await session.start(agent=agent, room=ctx.room)

    # The user speaks first by default; the agent stays silent until spoken to
    # or until the frontend sends the agent_start control.
    log_event("session_ready", session_id=session_id)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
