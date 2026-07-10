---
description: Generate a master prompt tuned to the CURRENT model (auto-detected)
---

Run the `fablegen` CLI to produce a master prompt for the task in `$ARGUMENTS`,
auto-tuned to whichever model is currently active, then show me the result and offer
to save it.

```bash
fablegen new "$ARGUMENTS" --model auto
```

`--model auto` detects the current model (from env or `~/.claude/settings.json`) and picks
the matching profile. To force one instead: `fablegen new "..." --profile opus-4.8`.

If `fablegen` is not found, tell me to install it with `pip install -e .` from the fablegen
repo (or run `python -m fablegen new "$ARGUMENTS" --model auto` from the repo root).
