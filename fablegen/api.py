"""Minimal, dependency-free Anthropic client (stdlib urllib only).

Used by `fablegen loop --api` to have Fable 5 refine the prompt.
Model ids change over time — pass --model to override the default.
"""
import json
import os
import urllib.error
import urllib.request

ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

_SYSTEM = (
    "You are a prompt engineer tuning a master prompt for Claude Fable 5. "
    "Fable 5 performs best on lean, minimal-with-strong-heuristics prompts and "
    "degrades on bloat. Given the TASK and the DRAFT master prompt, return an "
    "improved, leaner, sharper version that keeps a clear goal, an explicit "
    "operating loop, skill hooks, and guardrails. "
    "Output ONLY the improved master prompt in Markdown — no preamble, no commentary."
)


def api_refine(prompt, task, model="claude-fable-5", api_key=None, max_tokens=2000):
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it, or drop --api to use the "
            "offline linter (no key required)."
        )

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": _SYSTEM,
        "messages": [{"role": "user",
                      "content": "TASK:\n{}\n\nDRAFT:\n{}".format(task, prompt)}],
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError("Anthropic API error {}: {}".format(e.code, detail))
    except urllib.error.URLError as e:
        raise RuntimeError("Network error reaching Anthropic API: {}".format(e.reason))

    parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    return "\n".join(parts).strip() or prompt
