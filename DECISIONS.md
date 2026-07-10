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

### CLI-first, Claude-Code-pluggable — 2026-07-10
Ship a standalone CLI plus a thin `/fable-gen` command file.
**Reason:** the user wants a GitHub repo usable anywhere *and* inside Claude Code.
**Rejected:** Claude-Code-only skill (not portable); web app (out of scope for v1).
