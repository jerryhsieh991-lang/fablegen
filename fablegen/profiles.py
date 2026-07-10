"""Per-model prompting profiles — the data that tunes a prompt to a model."""
import json
from pathlib import Path

_DIR = Path(__file__).parent / "profiles"
DEFAULT_PROFILE = "fable-5"

_REQUIRED = ("id", "display", "tagline", "elicitation")


def list_profiles():
    return sorted(p.stem for p in _DIR.glob("*.json"))


def load_profile(profile_id=None):
    pid = (profile_id or DEFAULT_PROFILE).strip()
    path = _DIR / (pid + ".json")
    if not path.exists():
        raise ValueError("unknown profile '{}'. available: {}".format(
            pid, ", ".join(list_profiles())))
    prof = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in _REQUIRED if k not in prof]
    if missing:
        raise ValueError("profile '{}' missing fields: {}".format(pid, ", ".join(missing)))
    return prof
