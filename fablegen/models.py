"""Model detection + model->profile resolution.

This is the "auto-switch by model" layer: fablegen figures out which model you're
on (from a flag, an env var, an active-profile config, or ~/.claude/settings.json)
and picks the matching profile automatically.
"""
import json
import os
import re
from pathlib import Path

from .profiles import list_profiles, DEFAULT_PROFILE

# model id / alias  ->  profile id
MODEL_ALIASES = {
    # Anthropic — Claude
    "claude-fable-5": "fable-5", "fable-5": "fable-5", "fable": "fable-5",
    "claude-mythos-5": "fable-5", "mythos-5": "fable-5", "mythos": "fable-5",
    "claude-opus-4-8": "opus-4.8", "opus-4.8": "opus-4.8", "opus-4-8": "opus-4.8",
    "claude-opus-4.8": "opus-4.8", "opus": "opus-4.8", "claude": "opus-4.8",
    "claude-sonnet-5": "sonnet-5", "sonnet-5": "sonnet-5", "sonnet": "sonnet-5",
    "claude-design": "claude-design", "design": "claude-design",
    # OpenAI — ChatGPT (GPT-5.6 is current; 5.5 kept as legacy)
    "gpt-5.6": "gpt-5.6", "gpt5.6": "gpt-5.6", "gpt-5.6-sol": "gpt-5.6",
    "gpt-5.6-terra": "gpt-5.6", "gpt-5.6-luna": "gpt-5.6", "sol": "gpt-5.6",
    "gpt": "gpt-5.6", "gpt-5": "gpt-5.6", "chatgpt": "gpt-5.6", "openai": "gpt-5.6",
    "gpt-5.5-instant": "gpt-5.5-instant", "gpt-5.5": "gpt-5.5-instant", "gpt5.5": "gpt-5.5-instant",
    # OpenAI — Codex (coding agent)
    "codex": "codex", "gpt-5.6-codex": "codex", "codex-cli": "codex", "gpt-5-codex": "codex",
    # Google — Gemini
    "gemini-3": "gemini-3", "gemini": "gemini-3", "gemini-3-pro": "gemini-3",
    "gemini-2.5": "gemini-3", "gemini-2.5-pro": "gemini-3", "google": "gemini-3",
    # xAI — Grok
    "grok-4": "grok-4", "grok": "grok-4", "grok-4-heavy": "grok-4", "xai": "grok-4",
    # Open-weight / local (self-host)
    "local": "local", "open": "local", "deepseek": "local", "qwen": "local",
    "llama": "local", "ollama": "local", "mistral": "local",
}

_ENV_VARS = ("FABLEGEN_MODEL", "ANTHROPIC_MODEL", "CLAUDE_MODEL")
_SETTINGS = Path.home() / ".claude" / "settings.json"


def normalize_model(s):
    s = (s or "").strip().lower()
    s = re.sub(r"\[.*?\]", "", s)   # strip suffixes like [1m]
    return s.strip()


def model_to_profile(model):
    m = normalize_model(model)
    if not m:
        return None
    if m in MODEL_ALIASES:
        return MODEL_ALIASES[m]
    for key, prof in MODEL_ALIASES.items():   # loose containment fallback
        if key in m:
            return prof
    return None


def detect_model(env=None, settings_path=None):
    """Return (model_string, source) or (None, None)."""
    env = env if env is not None else os.environ
    for var in _ENV_VARS:
        if env.get(var):
            return env[var], "env:" + var
    sp = Path(settings_path) if settings_path else _SETTINGS
    try:
        data = json.loads(sp.read_text(encoding="utf-8"))
        if data.get("model"):
            return data["model"], "~/.claude/settings.json"
    except Exception:
        pass
    return None, None


def resolve_profile(explicit_profile=None, model=None, config=None,
                    env=None, settings_path=None):
    """Return (profile_id, reason). Precedence, highest first:

    --profile > --model (mapped, or 'auto' = detect) > env FABLEGEN_PROFILE >
    active config (fablegen use) > auto-detected model > default.
    """
    valid = set(list_profiles())

    if explicit_profile:
        if explicit_profile not in valid:
            raise ValueError("unknown profile '{}'. available: {}".format(
                explicit_profile, ", ".join(sorted(valid))))
        return explicit_profile, "explicit --profile"

    if model:
        if model == "auto":
            m, src = detect_model(env, settings_path)
            prof = model_to_profile(m) if m else None
            if prof:
                return prof, "auto-detected model '{}' via {}".format(m, src)
            return DEFAULT_PROFILE, "auto-detect found no known model - default"
        prof = model_to_profile(model)
        if prof:
            return prof, "model '{}'".format(model)
        raise ValueError("unknown model '{}'. known: {}".format(
            model, ", ".join(sorted(set(MODEL_ALIASES)))))

    e = env if env is not None else os.environ
    if e.get("FABLEGEN_PROFILE") in valid:
        return e["FABLEGEN_PROFILE"], "env FABLEGEN_PROFILE"

    if config is None:
        from .config import read_active
        config = read_active()
    if config.get("profile") in valid:
        return config["profile"], "active config (fablegen use)"

    m, src = detect_model(env, settings_path)
    prof = model_to_profile(m) if m else None
    if prof:
        return prof, "detected model '{}' via {}".format(m, src)

    return DEFAULT_PROFILE, "default"
