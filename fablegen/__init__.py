"""fablegen — a master-prompt generator for Claude Fable 5.

Generates lean prompts carrying a goal block, an operating-loop protocol,
and auto-matched skill hooks. Public API: build_prompt, refine, score_prompt.
"""
__version__ = "0.1.0"

from .generator import build_prompt  # noqa: E402,F401
from .refine import refine, score_prompt  # noqa: E402,F401

__all__ = ["build_prompt", "refine", "score_prompt", "__version__"]
