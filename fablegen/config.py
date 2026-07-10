"""Persistent active-profile config (~/.fablegen.json).

`fablegen use <model-or-profile>` writes it so later `new`/`loop` calls follow
the model you switched to without re-passing flags.
"""
import json
from pathlib import Path

_PATH = Path.home() / ".fablegen.json"


def _path(path=None):
    return Path(path) if path else _PATH


def read_active(path=None):
    try:
        return json.loads(_path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def set_active(profile, path=None):
    _path(path).write_text(json.dumps({"profile": profile}), encoding="utf-8")
    return profile


def clear_active(path=None):
    p = _path(path)
    if p.exists():
        p.unlink()
