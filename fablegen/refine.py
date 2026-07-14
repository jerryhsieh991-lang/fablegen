"""Refine a generated prompt over N iterations.

- offline (default): a deterministic linter that scores the prompt against a
  Fable-5-style rubric and trims it toward "lean" when it runs long. No API key.
- api: sends the prompt to the target model and asks for a leaner, sharper rewrite.
"""
import re

from .generator import build_prompt, DEFAULT_HEURISTICS, DEFAULT_GUARDRAILS

# The generated prompt carries a discovery gate, a final-check block, and per-model
# profile idioms/guardrails, so the "lean" ceiling sits a bit above a bare goal+loop
# prompt. A full, well-formed prompt lands ~530-620 words; above this something got heavy.
LEAN_WORD_BUDGET = 630


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
        "has_discovery": "## Discovery" in text,
        "has_loop": ("Operating loop" in text) if loop_expected else True,
        "has_skills": "Skills & tools" in text,
        "has_guardrails": "## Guardrails" in text,
        "has_final_check": "## Final check" in text,
        "lean": _words(text) <= LEAN_WORD_BUDGET,
    }
    passed = sum(1 for v in checks.values() if v)
    score = passed / len(checks)
    findings = [k for k, v in checks.items() if not v]
    return score, checks, findings


def refine(task, build_kwargs, iterations=3, api=False,
           model=None, api_key=None):
    """Return (final_prompt, trail) where trail is a list of per-iteration dicts."""
    kwargs = dict(build_kwargs)
    prompt = build_prompt(task, **kwargs)
    loop_expected = kwargs.get("loop", True)
    resolved_model = model or _model_for_profile(kwargs.get("profile"))
    trail = []

    for i in range(1, max(1, iterations) + 1):
        action = "none"

        if api:
            from .api import api_refine
            prompt = api_refine(prompt, task, model=resolved_model, api_key=api_key)
            action = "api rewrite ({})".format(resolved_model)
        else:
            _, checks, _ = score_prompt(prompt, loop_expected)
            if not checks["lean"] and kwargs.get("heuristics") is None:
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


def _model_for_profile(profile):
    """Map a profile id to an API model string for --api rewrites."""
    ids = {
        "fable-5": "claude-fable-5",
        "opus-4.8": "claude-opus-4-8",
        "sonnet-5": "claude-sonnet-5",
        "claude-design": "claude-opus-4-8",
        "gpt-5.5-instant": "claude-opus-4-8",  # refiner is a Claude; GPT api not wired
    }
    return ids.get(profile or "fable-5", "claude-opus-4-8")
