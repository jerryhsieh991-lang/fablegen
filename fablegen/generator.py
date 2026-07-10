"""Build a lean, Fable-5-tuned master prompt from a task description."""
import re
from pathlib import Path

from .skills import match_skills, format_skills_block

_TEMPLATE = (Path(__file__).parent / "templates" / "master.md").read_text(encoding="utf-8")

# The operating-loop block embedded in every generated prompt (unless --no-loop).
# This is the self-loop the *consuming* model runs.
LOOP_BLOCK = """
## Operating loop
Repeat until *Done when* is satisfied:
1. **Orient** — restate the goal; note what is done and what is left.
2. **Plan** — pick the single next step that most advances the goal.
3. **Act** — do it.
4. **Check** — test the result against the success criteria; if it fails, diagnose before retrying.
5. **Decide** — loop, or stop.

Stop when: the success criteria are met · the same step fails 3× · an action is irreversible or costly (surface it and wait for a go-ahead) · the goal is ambiguous (ask one sharp question).
"""

DEFAULT_HEURISTICS = [
    "Think first, briefly: state the plan in one or two lines, then act.",
    "Take the simplest path that satisfies the goal; cut whatever does not serve it.",
    "When something is unknown but knowable, verify it — do not guess.",
    "Every step must move the goal forward; bias to finishing over exploring.",
]

DEFAULT_GUARDRAILS = [
    "Stay inside the goal — no unrequested features or scope.",
    "Before anything irreversible or costly, stop and confirm.",
    "If one step fails three times, halt and report instead of retrying blindly.",
]

DEFAULT_OUTPUT = (
    "End by stating: what you did, what you verified it against, "
    "and the single most valuable next step."
)

DEFAULT_SUCCESS = (
    "the goal above is fully met and checked against its own stated outcome, "
    "with no scope creep (replace this with concrete, testable criteria)."
)

# Small keyword → role map. Falls back to a neutral executor role.
_ROLE_HINTS = [
    (("code", "bug", "api", "backend", "refactor", "implement", "function"),
     "You are a senior software engineer."),
    (("ui", "ux", "frontend", "react", "website", "landing", "design"),
     "You are a senior product designer and front-end engineer."),
    (("research", "compare", "investigate", "sources", "market", "analysis"),
     "You are a rigorous research analyst."),
    (("copy", "headline", "blog", "essay", "story", "content", "messaging"),
     "You are a sharp writer."),
    (("prompt", "agent", "system prompt", "llm"),
     "You are an expert prompt engineer."),
    (("plan", "roadmap", "strategy", "prioritize", "spec"),
     "You are a decisive product lead."),
]


def infer_role(task):
    t = task.lower()
    for keys, role in _ROLE_HINTS:
        if any(k in t for k in keys):
            return role
    return "You are a focused expert executor who finishes what the goal requires and nothing more."


def _bullets(items):
    return "\n".join("- " + str(x).strip() for x in items)


def _fill(template, mapping):
    def repl(m):
        key = m.group(1).strip()
        return str(mapping.get(key, m.group(0)))
    return re.sub(r"{{\s*(\w+)\s*}}", repl, template)


def build_prompt(task, *, role=None, success=None, skills=None, loop=True,
                 heuristics=None, guardrails=None, output=None, registry=None):
    """Return a finished master prompt as a Markdown string."""
    task = (task or "").strip()
    if not task:
        raise ValueError("task is empty — describe what you want the model to do.")

    matched = match_skills(task, forced=skills, registry=registry)
    mapping = {
        "ROLE": role or infer_role(task),
        "GOAL": task,
        "SUCCESS": success or DEFAULT_SUCCESS,
        "LOOP_BLOCK": LOOP_BLOCK if loop else "",
        "HEURISTICS": _bullets(heuristics or DEFAULT_HEURISTICS),
        "SKILLS": format_skills_block(matched),
        "GUARDRAILS": _bullets(guardrails or DEFAULT_GUARDRAILS),
        "OUTPUT": output or DEFAULT_OUTPUT,
    }
    text = _fill(_TEMPLATE, mapping)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text
