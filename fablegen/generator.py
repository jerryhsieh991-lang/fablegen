"""Build a lean, model-tuned master prompt from a task description + a profile."""
import re
from pathlib import Path

from .skills import match_skills, format_skills_block
from .profiles import load_profile

_TEMPLATE = (Path(__file__).parent / "templates" / "master.md").read_text(encoding="utf-8")

# The operating-loop the *consuming* model runs (unless --no-loop or a profile
# overrides it). Step 2 explicitly ties planning to the matched skills.
LOOP_BLOCK = """
## Operating loop
Repeat until *Done when* is satisfied:
1. **Orient** — restate the goal; note what is done and what is left.
2. **Plan** — pick the single next step that most advances the goal, and the skill from *Skills & tools* that best fits it.
3. **Act** — do it.
4. **Check** — test the result against the success criteria; if it fails, diagnose before retrying.
5. **Decide** — loop, or stop.

Stop when: the success criteria are met · the same step fails 3× · an action is irreversible or costly (surface it and wait) · the goal is ambiguous (ask one sharp question).
"""

# Discovery gate, tuned by the profile's elicitation stance. This is the
# "interview the user until the goal is understood, THEN loop" behavior.
DISCOVERY_BLOCKS = {
    "balanced": """
## Discovery — understand before you act
First restate the goal in one sentence and state the assumptions you are making. Then test every unknown with one question: *would a different answer change the plan?* Batch the ones that pass into a single short round (aim for 3-5, asked together — not one at a time); for the rest, state your assumption inline and proceed. Front-load this — do not discover ambiguity mid-execution. If an answer stays vague, reframe it (outcome / trade-off / failure-framing) instead of repeating. When the blocking unknowns are resolved, enter the loop.
""",
    "clarify-first": """
## Discovery — interview first, build nothing yet
Do not start the work until you understand it. In one batched round, ask about: the exact deliverable and format, the fidelity and scope, how many options/variations and along what axis (UX / visuals / copy / flow), whether they want something novel or safe and on-brand, and any source material to ground in (design system, brand, existing code). Aim for the ~5-10 questions that would actually change what you build, and offer escape hatches ("a few options", "you decide", "other"). If an answer is vague, reframe with a concrete example or a forced choice — don't repeat it. Only once the deliverable is unambiguous — and after reading any provided resources — proceed.
""",
    "context-first": """
## Discovery — mine context, then ask only what's missing
Restate the goal in one sentence. First use everything already provided — context, memory, prior turns, files — and do NOT ask for anything it already answers. Ask a clarifying question ONLY when it is genuinely blocking, no provided context resolves it, and a different answer would change the plan; otherwise state the assumption in one line and proceed. Never pause to confirm a context-supported detail. Keep any questions to a single batched round.
""",
}

FINAL_CHECK_BLOCK = """
## Final check — before you call it done
1. Re-read the Goal and *Done when*; confirm each criterion is actually met.
2. Verify with evidence — run it, test it, or re-read it. Do not claim done from inference.
3. Name what you did NOT do and any risk that remains.
4. State the single most valuable next step.
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


def build_prompt(task, *, profile="fable-5", role=None, success=None, skills=None,
                 loop=True, heuristics=None, guardrails=None, output=None, registry=None):
    """Return a finished, model-tuned master prompt as a Markdown string."""
    prof = profile if isinstance(profile, dict) else load_profile(profile)
    task = (task or "").strip()
    if not task:
        raise ValueError("task is empty — describe what you want the model to do.")

    matched = match_skills(task, forced=skills, registry=registry)

    heur = list(heuristics or DEFAULT_HEURISTICS)
    if heuristics is None:
        heur += list(prof.get("idioms") or [])[:2]
    guards = list(guardrails or DEFAULT_GUARDRAILS)
    if guardrails is None:
        guards += list(prof.get("guardrail_extra") or [])

    discovery = DISCOVERY_BLOCKS.get(prof.get("elicitation", "balanced"),
                                     DISCOVERY_BLOCKS["balanced"])
    loop_block = (prof.get("loop_override") or LOOP_BLOCK) if loop else ""

    final_check = FINAL_CHECK_BLOCK
    if prof.get("verify_note"):
        final_check = final_check.rstrip() + "\n5. " + prof["verify_note"] + "\n"

    effort = prof.get("effort_line") or ""
    mapping = {
        "PROFILE_DISPLAY": prof.get("display", "Claude Fable 5"),
        "PROFILE_TAGLINE": prof.get("tagline", ""),
        "EFFORT_LINE": ("> " + effort) if effort else "",
        "ROLE": role or prof.get("role_hint") or infer_role(task),
        "GOAL": task,
        "SUCCESS": success or DEFAULT_SUCCESS,
        "DISCOVERY_BLOCK": discovery,
        "LOOP_BLOCK": loop_block,
        "HEURISTICS": _bullets(heur),
        "SKILLS": format_skills_block(matched),
        "GUARDRAILS": _bullets(guards),
        "FINAL_CHECK_BLOCK": final_check,
        "OUTPUT": output or DEFAULT_OUTPUT,
    }
    text = _fill(_TEMPLATE, mapping)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text
