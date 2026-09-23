"""FloodCast AI assistant: natural-language Q&A over the live flood situation.

Two modes:
  * "claude"  - Claude (via the Anthropic SDK) answers using read-only situation tools.
                Enabled when Anthropic credentials are present (ANTHROPIC_API_KEY, etc.).
  * "offline" - built-in keyword/fuzzy-match NLP engine (app.assistant.nlp). Always available.

Set ASSISTANT_MODE=offline to force the offline engine, or ASSISTANT_MODE=claude to use
Claude with credentials from an `ant auth login` profile.
"""
import json
import logging
import os
from typing import Any, Dict, List

from app.assistant import nlp, tools

log = logging.getLogger("floodcast.assistant")

MODEL = os.getenv("ASSISTANT_MODEL", "claude-opus-5")
EFFORT = os.getenv("ASSISTANT_EFFORT", "medium")
MAX_TOOL_ROUNDS = 6
MAX_HISTORY_TURNS = 20

SYSTEM_PROMPT = """You are the FloodCast AI assistant in the Assam State Disaster Management Authority (ASDMA) flood control room. Operators, district officers and SDRF teams ask you about the live flood situation computed by FloodCast AI: hill rainfall triggers, river gauge levels and forecasts, red/yellow/green hazard zones, village risk, rescue boat and relief allocation, and the delivery of resident SMS and AI voice-call alerts.

How to answer:
- Get every number, name and status from the tools. Never estimate or invent figures; if a tool doesn't have something, say so.
- Lead with what matters most for saving lives (red zones, extreme-risk villages, shortfalls, failed alerts), then details.
- Be brief and scannable: a one-line headline, then short "- " bullets. Use **bold** for key numbers. No tables, no headings.
- When it helps, end with one to three concrete next steps (get_recommended_actions has suggestions).
- Reply in the language the user writes in (English, Hindi or Assamese). Keep village and place names as they are.
- The data is a simulation of a 72-hour flood event; "hour" is the simulation hour currently shown on the dashboard.
- You can only read data. To send alerts, change send rates or run the simulation, point the user to the Alerts, Settings pages or the Play button.
- For resident safety questions, give standard flood-safety guidance and the helplines (1079 State EOC, 112 national emergency)."""


def claude_available() -> bool:
    mode = os.getenv("ASSISTANT_MODE", "").lower()
    if mode == "offline":
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    if mode == "claude":  # e.g. credentials from an `ant auth login` profile
        return True
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_PROFILE"))


def status() -> Dict[str, Any]:
    mode = "claude" if claude_available() else "offline"
    return {"mode": mode, "model": MODEL if mode == "claude" else "built-in NLP", "suggestions": nlp.SUGGESTIONS}


def _clean_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Keep plain user/assistant text turns, alternating, starting with a user turn."""
    out: List[Dict[str, str]] = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        role, content = turn.get("role"), (turn.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        if not out and role != "user":
            continue
        if out and out[-1]["role"] == role:
            out[-1]["content"] += "\n\n" + content
        else:
            out.append({"role": role, "content": content})
    if out and out[-1]["role"] == "user":
        out.pop()  # the new question is appended by the caller
    return out


def _ask_claude(message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    import anthropic

    client = anthropic.Anthropic()
    messages: List[Dict[str, Any]] = _clean_history(history) + [{"role": "user", "content": message}]
    tools_used: List[str] = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=tools.TOOL_SCHEMAS,
            thinking={"type": "adaptive"},
            output_config={"effort": EFFORT},
            # Server-side refusal fallback: a declined request is re-run on Anthropic's recommended model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=messages,
        )

        if response.stop_reason == "refusal":
            return {"reply": "I can't help with that request. Ask me about the flood situation, zones, villages, rivers, relief or alerts.",
                    "tools_used": tools_used}

        if response.stop_reason != "tool_use":
            text = "\n".join(b.text for b in response.content if b.type == "text").strip()
            if response.stop_reason == "max_tokens":
                text += "\n\n(Answer cut short.)"
            return {"reply": text or "I don't have an answer for that.", "tools_used": tools_used}

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tools_used.append(block.name)
            try:
                payload = tools.run_tool(block.name, block.input if isinstance(block.input, dict) else {})
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(payload, default=str)})
            except Exception as exc:  # noqa: BLE001 - surface tool errors to the model
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": f"Error: {exc}", "is_error": True})
        messages.append({"role": "user", "content": results})

    return {"reply": "That needed too many lookups. Please ask a narrower question.", "tools_used": tools_used}


def chat(message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """Answer one user message. Falls back to the offline engine if Claude is unavailable or fails."""
    message = (message or "").strip()[:2000]
    if not message:
        return {"reply": "Ask me about the flood situation.", "mode": "offline", "tools_used": []}

    if claude_available():
        import anthropic
        try:
            result = _ask_claude(message, history or [])
            return {**result, "mode": "claude", "model": MODEL}
        except anthropic.AuthenticationError:
            note = "Claude credentials were rejected"
        except anthropic.RateLimitError:
            note = "Claude is rate-limited right now"
        except anthropic.APIStatusError as exc:
            note = f"Claude returned an error ({exc.status_code})"
        except anthropic.APIConnectionError:
            note = "Claude could not be reached"
        log.warning("Assistant falling back to offline engine: %s", note)
        offline = nlp.answer(message)
        return {"reply": offline["reply"], "mode": "offline", "notice": f"{note}; answered with the built-in engine.",
                "intent": offline["intent"], "tools_used": []}

    offline = nlp.answer(message)
    return {"reply": offline["reply"], "mode": "offline", "intent": offline["intent"], "tools_used": []}
