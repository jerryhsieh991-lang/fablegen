---
description: Generate a lean Fable-5 master prompt (goal + loop + skills) from a task
---

Run the `fablegen` CLI to produce a master prompt for the task described in `$ARGUMENTS`,
then show me the result and offer to save it.

```bash
fablegen new "$ARGUMENTS"
```

If `fablegen` is not found, tell me to install it with `pip install -e .` from the
fablegen repo (or run `python -m fablegen new "$ARGUMENTS"` from the repo root).
