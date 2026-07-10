"""Refine a generated prompt over N iterations.

Two modes:
- offline (default): a deterministic linter that scores the prompt against a
  Fable-5 rubric and trims it toward "lean" when it runs long. No API key.
- api: sends the prompt to Fable 5 and asks for a leaner, sharper rewrite.
"""
import re

from .generator import build_prompt, DEFAULT_HEURISTICS, DEFAULT_GUARDRAILS

LEAN_WORD_BUDGET = 400


def _words(text):
    return len(text.split())


def score_prompt(text, loop_expected=True):
    """Return (score in [0,1], checks dict, list of failing check names)."""
    checks = {
        "has_role": bool(re.search(r"you are ", text, re.I)),
        "has_goal": "## Goal" in text,
        "has_done_when": "Done when" in text,
        "success_measurable": bool(re.search(
            r"Done when:.*?(\d|when |able to|pass|<|>|%|verif|criteria)",
            text, re.I | re.S)),
        "has_loop": ("Operating loop" in text) if loop_expected else True,
        "has_skills": "Skills & tools" in text,
        "has_guardrails": "## Guardrails" in text,
        "lean": _words(text) <= LEAN_WORD_BUDGET,
    }
    passed = sum(1 for v in checks.values() if v)
    score = passed / len(checks)
    findings = [k for k, v in checks.items() if not v]
    return score, checks, findings


def refine(task, build_kwargs, iterations=3, api=False,
           model="claude-fable-5", api_key=None):
    """Return (final_prompt, trail) where trail is a list of per-iteration dicts."""
    kwargs = dict(build_kwargs)
    prompt = build_prompt(task, **kwargs)
    loop_expected = kwargs.get("loop", True)
    trail = []

    for i in range(1, max(1, iterations) + 1):
        action = "none"

        if api:
            from .api import api_refine
            prompt = api_refine(prompt, task, model=model, api_key=api_key)
            action = "api rewrite"
        else:
            _, checks, _ = score_prompt(prompt, loop_expected)
            if not checks["lean"] and kwargs.get("heuristics") is None:
                # Deterministic improvement: trim to the strongest few bullets.
                kwargs["heuristics"] = DEFAULT_HEURISTICS[:3]
                kwargs["guardrails"] = DEFAULT_GUARDRAILS[:3]
                prompt = build_prompt(task, **kwargs)
                action = "trimmed toward lean"

        score, _, findings = score_prompt(prompt, loop_expected)
        trail.append({"iter": i, "mode": "api" if api else "offline",
                      "score": score, "action": action, "findings": findings})

        if not api and score == 1.0:
            break

    return prompt, trail
