# Model profile changelog

One line per refresh of `fablegen/profiles/*.json`. Newest first.

## 2026-07-12 — full re-research + auto-switch by model
- Added profiles: `gpt-5.6`, `codex`, `gemini-3`, `grok-4`, `local`, `opus-4.8`, `sonnet-5`,
  `fable-5`, `claude-design`; kept `gpt-5.5-instant` as legacy.
- Detection: expanded `MODEL_ALIASES` (chatgpt→gpt-5.6, deepseek/qwen/llama→local, …) so a
  prompt auto-picks its profile from the active model.
- Discovery stances now include **assume-and-proceed** (GPT/Codex bias-to-action) alongside
  clarify-first / context-first / interview-first.
- Leanness pass: role is task-inferred (role_hint nulled), idioms→2, one guardrail, loop
  guidance folded into notes. Word budget 630.
- Reference: regenerated `docs/model-prompting-guide.md`.
- Automation: added `refresh-model-profiles` skill + `scripts/` (research→apply→test→commit).
