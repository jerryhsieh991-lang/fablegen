"""Interactive builder: ask the user about context until the goal is clear,
then generate a master prompt. This is the CLI-side elicitation loop; the
generated prompt also carries its own Discovery gate.
"""
import sys

from .generator import build_prompt
from .refine import score_prompt
from .profiles import list_profiles, DEFAULT_PROFILE

# (key, question, required)
_QUESTIONS = [
    ("task", "What do you want the model to do? (one line)", True),
    ("context", "Who/what is it for, and any hard constraints? (enter to skip)", False),
    ("success", "What does 'done' look like — a concrete, testable outcome?", False),
    ("profile", "Which model? [{}] (enter = {})".format(
        "/".join(list_profiles()), DEFAULT_PROFILE), False),
    ("skills", "Skills to force in? comma-separated (enter to auto-match)", False),
]

_MAX_REFINE_ROUNDS = 3


def run_interview(read=input, out=print, isatty=None):
    """Drive the Q&A and return the final prompt string, or None if aborted.

    `read`/`out` are injectable for testing. `isatty` overrides TTY detection.
    """
    if isatty is None:
        isatty = sys.stdin.isatty()
    if not isatty:
        out('interview needs an interactive terminal. '
            'Use: fablegen new "<task>" [--profile <id>]')
        return None

    answers = {}
    for key, question, required in _QUESTIONS:
        while True:
            val = (read("- " + question + "\n  > ") or "").strip()
            if val or not required:
                answers[key] = val
                break
            out("  (a task is required)")

    task = answers["task"]
    if answers.get("context"):
        task += "\n\nContext / constraints: " + answers["context"]

    profile = answers.get("profile") or DEFAULT_PROFILE
    success = answers.get("success") or None
    skills = [s for s in (answers.get("skills") or "").split(",") if s.strip()] or None

    prompt = build_prompt(task, profile=profile, success=success, skills=skills)

    # Keep asking for more context until the user accepts.
    for _ in range(_MAX_REFINE_ROUNDS):
        score, _, findings = score_prompt(prompt)
        out("\n--- generated · profile {} · lint {:.2f} ---\n".format(profile, score))
        out(prompt)
        more = (read("\nGood? [enter to accept] or add more context to refine: ") or "").strip()
        if not more:
            break
        task += "\n\nAlso: " + more
        prompt = build_prompt(task, profile=profile, success=success, skills=skills)

    return prompt
