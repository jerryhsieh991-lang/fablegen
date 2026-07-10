# Plugging fablegen into a Sentinel-style workflow

fablegen is the *prompt-generation arm*. Sentinel (an output-style / instruction
layer at `~/.claude/output-styles/promptos.md`) is the *controller*. They connect at
the **tool layer** — you install fablegen as a command Sentinel can call. You do **not**
edit Sentinel's core instructions to do this, and nothing here turns Sentinel into a
runtime. A text instruction layer can't intercept `/model` switches; fablegen does the
detecting instead.

## The one thing that makes it feel automatic

fablegen reads the model you're on and picks the matching profile itself:

```bash
fablegen detect
# detected model: claude-fable-5[1m] (via ~/.claude/settings.json)
# resolves to profile: fable-5  — detected model 'claude-fable-5[1m]' via ~/.claude/settings.json
```

So `fablegen new "<task>"` with **no flags** already tracks your current model. When you
`/model` switch in Claude Code (which rewrites `settings.json`), the next `fablegen` call
follows. That is the "auto-switch when I switch models" you wanted — living in the tool,
where it can actually work.

Resolution order (highest first): `--profile` → `--model <id>|auto` →
`FABLEGEN_PROFILE` env → `fablegen use` active config → detected model → `fable-5`.

## Install the command (one time)

```bash
cd fablegen && pip install -e .
cp claude_code/commands/fable-gen.md ~/.claude/commands/fable-gen.md
```

Now `/fable-gen build a rate limiter` runs `fablegen new "..." --model auto` and hands
back a master prompt tuned to whatever model you're currently on.

## Where it fits in the loop

Sentinel already routes by model and task (see its CLAUDE.md model-routing section).
fablegen slots in at the "draft the brief / master prompt" step:

1. Sentinel scopes the task and picks the model.
2. `fablegen new --model auto "<task>" --success "<criteria>"` produces the master prompt
   (discovery gate → goal → loop → skills → final check), already tuned to that model.
3. Sentinel hands that prompt to the executor (or you paste it into the target model).

No Sentinel edit is required for any of this. If you later want Sentinel's routing doc to
*mention* fablegen, that's a one-line pointer you add deliberately — not a subsystem baked
into the OS.

## Why it's not baked into Sentinel itself

Sentinel v1 is in feature freeze: a capability is earned only when the same friction shows
up across 2–3 different real projects, or to fix a verified bug. "Auto-switch generators
inside the OS" has one project behind it and no recorded friction, and it's the
workflow→runtime direction the anti-expansion gate exists to refuse. Keeping the mechanism
in fablegen (a tool you version, test, and publish) is the honest, reversible home for it.
