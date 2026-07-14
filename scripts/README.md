# fablegen model-profile refresh

Keeps the per-model prompting profiles (`fablegen/profiles/*.json`) current with how each
frontier model actually wants to be prompted. Two layers:

| File | Role |
|------|------|
| `model-research.workflow.js` | Multi-agent research workflow: one web-researcher per model family → adversarial verify → synthesize a report + one profile per model. |
| `apply_profiles.py` | Turns the workflow output JSON into `docs/model-prompting-guide.md` + lean `profiles/*.json`. Enforces leanness (nulls role_hint, trims idioms/guardrails, folds loop notes). |
| `~/.claude/skills/refresh-model-profiles/SKILL.md` | The **agent procedure**: research → apply → `unittest` gate → commit+push **only if green**. |
| `weekly-refresh-reminder.sh` | Safe weekly **reminder** (macOS notification). No agent, no git. |
| `com.fablegen.weekly-refresh.plist` | launchd job that fires the reminder every Mon 09:07. |

A fully unattended runner is deliberately **not shipped** (it would need approvals-off — see the tradeoff below).

## Run it now (recommended — human in the loop)

```
cd ~/Projects/fablegen && claude
# then: "run the refresh-model-profiles skill"
```

You approve each web/git tool call; every refresh lands as one revertable commit.

## Schedule the safe weekly reminder

```
sed "s|__REPO__|$PWD|g" scripts/com.fablegen.weekly-refresh.plist > ~/Library/LaunchAgents/com.fablegen.weekly-refresh.plist
launchctl load ~/Library/LaunchAgents/com.fablegen.weekly-refresh.plist
```

Every Monday you get a notification; you run the skill when convenient. Unload with
`launchctl unload ~/Library/LaunchAgents/com.fablegen.weekly-refresh.plist`.

## Fully unattended (opt-in — read the tradeoff)

`weekly-refresh.sh` would run the skill with **no human gate**, which requires
`claude -p --dangerously-skip-permissions` — an agent that can web-research, run workflows,
and **push to this public repo** with approvals disabled. The test-gate + one-commit-per-run
design limits blast radius, but a compromised or hallucinated step runs unchecked. That is a
deliberate security tradeoff, so **this repo does not ship or enable that runner** — if you
want it, you write and schedule it yourself. The safe reminder above is the default on purpose.

> Note on cadence: prompting best-practices move slowly. **Monthly** is plenty and cheaper
> than weekly deep research — change the plist's `Weekday`/`Day` if you agree.
