# Decisions

Log of non-obvious choices. Format: Decision / Reason / Alternatives rejected.

### Generator, not an "OS" — 2026-07-10
Build a master-prompt *generator*, not a prompt "operating system."
**Reason:** the value is the generated prompt; a kernel/runtime/daemon adds scope and
zero user value. **Rejected:** a full OS with state, orchestration, and multi-model
routing — that is the product this repo *generates prompts for*, not the repo itself.

### Prompts are deliberately lean — 2026-07-10
Generated prompts stay minimal-with-strong-heuristics (a short role, a goal, a loop, a
few heuristics, skill hooks, guardrails).
**Reason:** frontier models like Fable 5 *degrade* on over-prescriptive mega-prompts.
A generator that emitted giant prompts would make the model worse. The offline linter
enforces a lean word budget for exactly this reason. **Rejected:** exhaustive rule lists.

### Standard library only — 2026-07-10
No third-party dependencies, including for the API call (`urllib` instead of the
`anthropic` SDK). **Reason:** clone-and-run, trivial install, no supply-chain surface,
easy to audit. **Rejected:** pulling in `anthropic`/`requests`/`click`.

### "Both" loops, split by responsibility — 2026-07-10
(1) The generated prompt carries a self-loop protocol the *consuming* model runs.
(2) `fablegen loop` re-runs to improve the *prompt itself*.
**Reason:** matches the user's "both" answer without a runtime — offline mode is a free
deterministic linter/trimmer; `--api` is a real Fable-5 rewrite. **Rejected:** a
scheduled daemon that executes prompts (heavier, needs a key to do anything).

### v0.3: auto model-detection, NOT a Sentinel rewrite — 2026-07-10
Added `--model auto`, a model->profile map, `fablegen use`/`detect`, and a persistent
active-profile config. fablegen now detects the current model (env, then
`~/.claude/settings.json`) and picks the profile itself.
**Reason:** the user asked to "auto-switch the generator when I switch models" and to
"plug it into Sentinel (the prompt OS)." The detection belongs in fablegen — a tool that
can actually read state at runtime. **Rejected (deliberately):** modifying Sentinel
itself. Sentinel is an output-style (text instruction layer), so it cannot intercept
`/model` switches; asking it to would turn a workflow into a runtime — the exact thing its
anti-expansion gate refuses. The wish has 0 cross-project evidence and Sentinel is in
feature freeze, so it was logged to the wishlist, not implemented. Integration is done at
the tool layer: a `/fable-gen --model auto` command + `SENTINEL.md`, no OS mutation.

### v0.2: multi-model profiles, discovery gate, final check — 2026-07-10
Added a per-model profile system (`fable-5`, `opus-4.8`, `sonnet-5`, `gpt-5.5-instant`,
`claude-design`), a discovery/interview gate, and a final-check block.
**Reason:** the user asked for per-model tuning + "ask the user until the goal is
understood, then loop, then final-check." Profiles were built from **deep research into
each model's own system prompt** (the four provided .md files) plus agent guides —
the elicitation stance is the key differentiator: `claude-design` is clarify-first
(~5–10 batched questions), Opus/Sonnet proceed on stated assumptions, `gpt-5.5-instant`
is context-first because its own prompt *penalizes* over-asking. **Rejected:** one
generic prompt for all models (would misfire on GPT and under-steer Sonnet); a separate
Markdown+JSON pair per model (kept one JSON per model — readable and loadable, stdlib-only).

### Discovery is a prompt block, not just a CLI feature — 2026-07-10
The "interview until understood" lives in TWO places: a Discovery block inside every
generated prompt (tuned by the profile's elicitation stance), and a `fablegen interview`
CLI that asks the user directly. **Reason:** the generated-prompt version works in any
harness with any model; the CLI version helps compose the prompt. **Rejected:** a runtime
that executes the interview itself (that's the OS-bloat direction we already refused).

### Lean budget raised 400 → 600 words — 2026-07-10
**Reason:** discovery + loop + final-check are all high-value; a full well-formed prompt
lands ~500–590 words. 600 still flags genuine bloat (over-long custom heuristics), so the
linter stays meaningful. **Rejected:** trimming the sourced discovery/loop content to hit
an arbitrary 400.

### CLI-first, Claude-Code-pluggable — 2026-07-10
Ship a standalone CLI plus a thin `/fable-gen` command file.
**Reason:** the user wants a GitHub repo usable anywhere *and* inside Claude Code.
**Rejected:** Claude-Code-only skill (not portable); web app (out of scope for v1).
