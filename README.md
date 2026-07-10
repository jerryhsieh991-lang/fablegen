# fablegen

A master-prompt generator for **Claude Fable 5**. You describe a task; it hands back a
**lean** prompt that already carries a goal block, an operating-loop protocol, and
auto-matched skill hooks — the scaffolding you'd otherwise write by hand every time.

It is deliberately *not* a "prompt OS." Frontier models like Fable 5 perform best on
minimal-with-strong-heuristics prompts and get **worse** when you bury them in rules, so
fablegen optimizes for lean output and even lints prompts that run long.

- Zero dependencies — standard library only. Clone and run.
- Works as a standalone CLI **and** plugs into Claude Code as `/fable-gen`.
- "Both" loops: every generated prompt self-loops toward its goal, and `fablegen loop`
  refines the prompt itself (free offline linter, or a real Fable-5 rewrite with `--api`).

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
fablegen new "Build a Rust CLI that watches a folder and syncs changes to S3" \
  --success "syncs a 1k-file tree in <2s and survives network drops"
```

Prints a ready-to-paste master prompt. A short lint score goes to stderr, so you can pipe
just the prompt:

```bash
fablegen new "..." > prompt.md          # clean prompt in the file
fablegen new "..." --save prompt.md     # same, and still printed
```

Then switch to Fable 5 (`/model claude-fable-5`) and paste it as your first message —
at high/xhigh effort for hard tasks.

## What a generated prompt looks like

Every prompt has the same lean skeleton: a role line, a **Goal** with a testable
**Done when**, an **Operating loop**, a few strong heuristics, the **skills to reach
for**, guardrails, and an output contract. See [`examples/`](examples/) for full outputs.

## Commands

| Command | What it does |
| --- | --- |
| `fablegen new "<task>"` | Generate one master prompt. |
| `fablegen loop "<task>"` | Generate, then refine over N iterations (`--iterations`, `--api`). |
| `fablegen skills` | List the built-in skill hooks and their triggers. |

Useful flags on `new`/`loop`: `--success` (testable criteria — always worth setting),
`--role`, `--skills a,b,c` (force specific skills), `--no-loop`, `--save PATH`.

## The two loops

1. **In the prompt.** The generated prompt tells the model to run
   *orient → plan → act → check → decide*, repeating until the success criteria are met,
   with explicit stop conditions. Use `--no-loop` for one-shot prompts.

2. **On the prompt.** `fablegen loop` improves the prompt itself:
   - **offline (default):** a deterministic linter that scores against a Fable-5 rubric
     (clear goal, measurable success, loop present, lean length, …) and trims toward
     lean. No API key needed.
   - **`--api`:** sends the draft to Fable 5 and asks for a leaner, sharper rewrite.
     Needs `ANTHROPIC_API_KEY`. Override the model with `--model` (ids change over time).

## Extend the skills

Skill hooks live in [`fablegen/templates/skills.json`](fablegen/templates/skills.json) —
`name`, `triggers` (substrings matched against the task), and `when`. Add your own
entries, or force any skill by name with `--skills my-skill`.

## Use it inside Claude Code

See [`claude_code/INSTALL.md`](claude_code/INSTALL.md). Short version: `pip install -e .`,
copy `claude_code/commands/fable-gen.md` into `~/.claude/commands/`, then
`/fable-gen <your task>`.

## Development

```bash
python -m unittest discover -s tests
```

## License

MIT — see [LICENSE](LICENSE). Set your name in `LICENSE` and `pyproject.toml` before
publishing.
