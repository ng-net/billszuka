"""Thin Kimi K3 client — stdlib only, OpenAI-compatible endpoint."""
import json
import urllib.request
from tools.config import KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL, KIMI_MAX_TOKENS


def ask(prompt: str, system: str = "", model: str = KIMI_MODEL,
        max_tokens: int = KIMI_MAX_TOKENS, reasoning: bool = True) -> str:
    """Send a single prompt to Kimi K3, return text response."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if reasoning:
        payload["reasoning_effort"] = "max"

    req = urllib.request.Request(
        url=f"{KIMI_BASE_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {KIMI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def ask_json(prompt: str, system: str = "") -> dict | list:
    """Ask K3 and parse response as JSON."""
    system_json = (system + "\nRespond ONLY with valid JSON, no markdown.").strip()
    raw = ask(prompt, system=system_json, reasoning=False)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)