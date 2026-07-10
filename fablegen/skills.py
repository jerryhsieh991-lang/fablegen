"""Skill registry: match a task to the highest-signal skills to reach for."""
import json
from pathlib import Path

_REGISTRY_PATH = Path(__file__).parent / "templates" / "skills.json"


def load_registry(path=None):
    p = Path(path) if path else _REGISTRY_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def match_skills(task, forced=None, registry=None, limit=6):
    """Return the skill entries relevant to `task`.

    `forced` (list of names) are always included, even if not in the registry.
    """
    reg = registry if registry is not None else load_registry()
    by_name = {e["name"].lower(): e for e in reg}
    text = (task or "").lower()
    picked, seen = [], set()

    for name in forced or []:
        key = name.strip().lower()
        if not key or key in seen:
            continue
        picked.append(by_name.get(key, {"name": name.strip(),
                                         "triggers": [],
                                         "when": "(you specified this one)"}))
        seen.add(key)

    for entry in reg:
        key = entry["name"].lower()
        if key in seen:
            continue
        if any(trig.lower() in text for trig in entry.get("triggers", [])):
            picked.append(entry)
            seen.add(key)

    return picked[:limit]


def format_skills_block(matched):
    if not matched:
        return ("- No specialized skill matched — work directly; reach for a "
                "research or review pass only if the goal needs it.")
    return "\n".join("- **{name}** — {when}".format(**e) for e in matched)
