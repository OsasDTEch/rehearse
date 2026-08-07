"""Structured JSON-lines logger with per-turn latency instrumentation.

Every event is one JSON object per line in logs/rehearse.jsonl, plus a readable
console line. Timestamps are UTC only.
"""
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "rehearse.jsonl"

_console = logging.getLogger("rehearse")
if not _console.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
    _console.addHandler(h)
    _console.setLevel(logging.INFO)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event: str, **fields):
    record = {"ts": _utc_now(), "event": event, **fields}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    _console.info("%s %s", event, {k: v for k, v in fields.items() if k != "text"})


class TurnTimer:
    """Measures the spans of one conversational turn.

    Usage:
        t = TurnTimer(session_id)
        t.mark("user_speech_end")
        t.mark("llm_first_token")
        t.mark("tts_first_byte")
        t.close()
    """

    def __init__(self, session_id: str, turn: int):
        self.session_id = session_id
        self.turn = turn
        self.t0 = time.monotonic()
        self.marks: dict[str, float] = {}

    def mark(self, name: str):
        self.marks[name] = round((time.monotonic() - self.t0) * 1000, 1)

    def close(self):
        log_event(
            "turn_latency",
            session_id=self.session_id,
            turn=self.turn,
            spans_ms=self.marks,
        )
