"""Distress tripwire. Runs on the user's transcript in code, before the LLM sees the turn.

Same pattern as HeatDesk's emergency escalation: hard rules in code, the LLM is never
given the chance to stay in character past a distress signal.
"""
import re

# Exact-ish phrases. Word-boundary matched, case-insensitive.
DISTRESS_PATTERNS = [
    r"\bstop\b",
    r"\bplease stop\b",
    r"\bi can'?t do this\b",
    r"\bi cannot do this\b",
    r"\btoo much\b",
    r"\bthis is too much\b",
    r"\boverwhelm(ed|ing)?\b",
    r"\bi want to stop\b",
    r"\bi need a break\b",
    r"\bmake it stop\b",
    r"\bi'?m panicking\b",
    r"\bpanic attack\b",
    r"\bi feel sick\b",
    r"\bget me out\b",
    r"\bi hate this\b",
    r"\bleave me alone\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in DISTRESS_PATTERNS]

# Calm, out-of-character line spoken immediately when the tripwire fires.
DEESCALATION_LINE = (
    "Okay. We've stopped. There's no rush at all. "
    "You can take a breath, and when you're ready, you can end the session, "
    "or start again, or just sit for a moment. You're in control."
)

# Follow-up behaviour instructions once in safe mode.
SAFE_MODE_INSTRUCTIONS = (
    "You are no longer roleplaying. The practice scenario has ended because the user signalled distress. "
    "You are now a calm, quiet, supportive presence. Speak slowly, briefly and gently. "
    "Do not ask questions unless the user asks you something. Do not restart the scenario unless the user clearly asks to. "
    "Remind them, at most once, that the buttons to end or restart are on screen and everything here is their choice."
)


def check(text: str) -> bool:
    """Return True if the user's utterance matches any distress pattern."""
    if not text:
        return False
    return any(rx.search(text) for rx in _COMPILED)
