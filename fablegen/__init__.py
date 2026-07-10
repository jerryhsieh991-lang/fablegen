"""fablegen — a multi-model master-prompt generator.

Generates lean prompts carrying a discovery gate (interview-first), a goal
block, an operating-loop protocol, auto-matched skill hooks, and a final check —
tuned per model via profiles. Public API below.
"""
__version__ = "0.4.0"

from .generator import build_prompt  # noqa: E402,F401
from .refine import refine, score_prompt  # noqa: E402,F401
from .profiles import list_profiles, load_profile  # noqa: E402,F401
from .models import resolve_profile, detect_model, model_to_profile  # noqa: E402,F401

__all__ = [
    "build_prompt", "refine", "score_prompt",
    "list_profiles", "load_profile",
    "resolve_profile", "detect_model", "model_to_profile",
    "__version__",
]
