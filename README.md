# fablegen

A **multi-model master-prompt generator**. You describe a task; it hands back a
**lean** prompt tuned to a specific model, carrying five things you'd otherwise write
by hand every time:

1. a **discovery gate** — the model interviews you until the goal is actually understood,
2. a **goal** with a testable *Done when*,
3. an **operating loop** (orient → plan → act → check → decide),
4. auto-matched **skill hooks**, and
5. a **final check** before it calls the work done.

It is deliberately *not* a "prompt OS." Frontier models perform best on
minimal-with-strong-heuristics prompts and get **worse** when buried in rules, so
fablegen optimizes for lean output and lints prompts that run long.

- **Per-model profiles.** Each model is prompted differently — `fablegen profiles`.
- **Zero dependencies.** Standard library only (even the API call uses `urllib`). Clone and run.
- Works as a standalone CLI **and** plugs into Claude Code as `/fable-gen`.
- **Both loops:** every generated prompt self-loops toward its goal, and `fablegen loop`
  refines the prompt itself (free offline linter, or a live model rewrite with `--api`).

## Why per-model profiles

The models genuinely want different prompts — this is researched from each model's own
behavior, not guessed:

| Profile | Elicitation stance | Style |
| --- | --- | --- |
| `fable-5` | balanced | lean; bloat degrades it; xhigh effort |
| `opus-4.8` | balanced (proceed on stated assumptions) | XML-structured, context-before-task, numeric effort budget |
| `sonnet-5` | balanced (needs explicit steering) | itemized steps + a concrete stop condition |
| `gpt-5.5-instant` | **context-first** (penalizes over-asking) | flat Markdown + numbered priorities; no Claude-isms |
| `claude-design` | **clarify-first** (interview ~5–10 questions) | understand → explore → todo → build → verify |

See [`examples/`](examples/) for a full generated prompt per model.

## Install

```bash
git clone https://github.com/your-username/fablegen
cd fablegen
pip install -e .        # gives you the `fablegen` command
# or skip install entirely:
python -m fablegen new "..."
```

Requires Python 3.9+.

## Quickstart

```bash
fablegen new "Build a Rust CLI that watches a folder and syncs to S3" \
  --profile opus-4.8 \
  --success "syncs a 1k-file tree in <2s and survives network drops"
```

Prints a ready-to-paste master prompt; a lint score goes to stderr, so you can pipe just
the prompt:

```bash
fablegen new "..." --profile sonnet-5 > prompt.md
```

Prefer to be interviewed instead of composing flags? Let fablegen ask you:

```bash
fablegen interview
```

It asks what you're building, who it's for, what "done" means, which model, and which
skills — then generates, and keeps refining while you add context.

## Auto-switch by model

fablegen can detect the model you're on and pick the matching profile itself — no flag:

```bash
fablegen detect
# detected model: claude-fable-5[1m] (via ~/.claude/settings.json)
# resolves to profile: fable-5 — detected model 'claude-fable-5[1m]' ...

fablegen new "build a rate limiter" --model auto   # tuned to the current model
```

Detection order (highest first): `--profile` → `--model <id>|auto` → `FABLEGEN_PROFILE`
env → `fablegen use` active config → detected model (env, then `~/.claude/settings.json`)
→ `fable-5`. Pin one across sessions with `fablegen use opus-4.8` (or a model id like
`fablegen use claude-opus-4-8`); undo with `fablegen use --clear`.

Using this inside a Sentinel-style workflow? See [SENTINEL.md](SENTINEL.md).

## Commands

| Command | What it does |
| --- | --- |
| `fablegen new "<task>" [--model auto\|ID] [--profile ID]` | Generate one master prompt. |
| `fablegen loop "<task>"` | Generate, then refine over N iterations (`--iterations`, `--api`). |
| `fablegen interview` | Interactive builder — answer questions, get a prompt. |
| `fablegen detect` | Show the detected model and which profile it resolves to. |
| `fablegen use <profile\|model>` | Pin an active profile across sessions (`--clear` to undo). |
| `fablegen profiles` | List the model profiles and their taglines. |
| `fablegen skills` | List the built-in skill hooks and triggers. |

Flags on `new`/`loop`: `--profile`, `--success` (testable criteria — always worth
setting), `--role`, `--skills a,b,c`, `--no-loop`, `--save PATH`.

## The two loops

1. **In the prompt.** The generated prompt runs *orient → plan → act → check → decide*
   until the success criteria are met, with explicit stop conditions. `claude-design`
   uses its own *understand → explore → todo → build → verify* loop. `--no-loop` omits it.

2. **On the prompt.** `fablegen loop` improves the prompt itself:
   - **offline (default):** a deterministic linter scoring against a rubric (clear goal,
     measurable success, discovery + loop + final-check present, lean length) and trimming
     toward lean. No API key.
   - **`--api`:** sends the draft to the profile's model for a leaner rewrite. Needs
     `ANTHROPIC_API_KEY`; override the model with `--model` (ids change over time).

## Extend it

- **Skills** live in [`fablegen/templates/skills.json`](fablegen/templates/skills.json)
  (`name`, `triggers`, `when`). Add your own, or force any with `--skills my-skill`.
- **Profiles** live in [`fablegen/profiles/`](fablegen/profiles/) — one JSON per model
  (elicitation stance, effort line, idioms, guardrails, optional loop override). Copy one
  to add a new model.

## Use it inside Claude Code

See [`claude_code/INSTALL.md`](claude_code/INSTALL.md): `pip install -e .`, copy
`claude_code/commands/fable-gen.md` into `~/.claude/commands/`, then `/fable-gen <task>`.

## Development

```bash
python -m unittest discover -s tests
```

## License

MIT — see [LICENSE](LICENSE). Set your name in `LICENSE` and `pyproject.toml` before
publishing.
