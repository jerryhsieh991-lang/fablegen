# Model Prompting Guide

> Auto-researched reference (2026). Feeds fablegen's per-model profiles.

# Per-Model Prompting Guide (2026-07-13)

A working reference for tuning a **master prompt per model**. Every section folds in the verified findings *and* the corrections, and drops the myths that didn't survive checking. The throughline: the 2026 frontier models converge on a few durable primitives (an explicit effort dial, native reasoning, schema-enforced output, lean prompts) but **diverge sharply** on defaults, locked sampling params, tool-loop invariants, and where "context" and "memory" belong. A prompt that is optimal for one is often actively wrong for another.

---

## 1. OpenAI GPT-5.6 "Sol" (`openai-gpt`)

**One-liner:** A contract-following, prompt-sensitive reasoner where *less instruction beats more* — state outcomes and boundaries once, cleanly, and let it choose the path. Contradictions and redundancy actively hurt it.

**System-prompt style.** Put task instructions in the `developer` message (higher priority than `user`); reserve `system` for platform rules. Structure with the GPT-5.6 skeleton in order — Role, Personality, Goal, Success criteria, Constraints, Tools, Output format, Stop rules — and fence discrete blocks in **XML-style tags** (`<constraints>`, `<tool_usage_rules>`, `<output_spec>`) with **Markdown prose/bullets inside** the tags. The answer to "Markdown or XML" is *both*: XML to fence instruction blocks, Markdown for readable content. This is literally how OpenAI's own GPT-5 guides are written, and it out-steers walls of Markdown headers. Be outcome-focused (goal, constraints, required evidence, success criteria, output format), not a step-by-step script. State each policy exactly once, in one place.

**Reasoning & verbosity.** Set `reasoning_effort` explicitly: `none | low | medium | high | xhigh | max`. On GPT-5.6 the default is **medium** (confirmed in the model-specific guidance — "when omitted, GPT-5.6 defaults to medium in both standard and pro modes"). `none` forces zero reasoning tokens (the true non-reasoning path; it *replaced* GPT-5's `minimal` and now works with hosted web/file search); reserve `max` for the hardest quality-first work. Migration heuristic straight from OpenAI: keep current effort as baseline, then **A/B one level lower** — newer versions are calibrated to match quality at lower cost. Verbosity has two independent knobs: the API param `text.verbosity` (`low|medium|high`) sets a global default; concrete in-prompt length constraints ("≤2 sentences", "≤5 bullets") override it locally. 5.6 is already terse by default, so specify exact *shape* instead of vague "be concise".

**Tools & context.** Prefer the Responses API. Expose only task-relevant tools, describe each in 1–2 sentences, set `strict:true` on function definitions (constrained decoding). Encourage parallel independent reads; use **Programmatic Tool Calling** for deterministic bulk work (filter/join/sort/dedupe/aggregate) but *not* for semantic judgment, approvals, or citation-dependent answers. Context is large (1M on 5.4+) but the operative risk is **consistency, not length** — the model follows prompt contracts closely, so scattered conflicting rules destabilize it more than missing detail. Front-load Role/Goal/Constraints; put stable content first for prompt caching; scope or clear stale persisted reasoning (`previous_response_id`) between distinct tasks.

**Corrections folded in.** The famous leaner-prompt numbers (**~10–15% eval gain, −41–66% tokens, −33–67% cost**) are real and verbatim in OpenAI's 5.6 guidance — but they are **directional estimates from a sample of internal coding-agent eval runs**, not a universal law. Validate on your own representative tasks. The XML tags (`<solution_persistence>` etc.) are from the **5.2 guide**; the "conflicting rules cause more instability than missing detail" warning is from the separate **5.6 prompt-guidance page**. The ChatGPT Instant-vs-Thinking adaptive routing is documented in the **GPT-5.1 product announcement**, not the developer prompting guide. The generic family reasoning guide lists a different set (`none|minimal|low|medium|high|xhigh`) — cite the **model-specific** page, whose set is `none|low|medium|high|xhigh|max`.

---

## 2. OpenAI Codex — current default GPT-5.6 (`openai-codex`)

**One-liner:** A persistence-biased autonomous coding agent that ships with its *own* tuned harness/system prompt. Your leverage is scoping the task and encoding durable rules in AGENTS.md — not coaxing effort or autonomy out of prose.

**System-prompt style.** Do **not** hand-author a monolithic system prompt; the Codex CLI injects its own tuned harness prompt (autonomy, persistence, tool contract). Your two surfaces are (1) **AGENTS.md** for durable, repo-scoped rules and (2) a compact per-task prompt. Write both in **flat Markdown with short `##` headings** — not XML tags, not Anthropic-style role tags. Frame the task prompt as **Goal / Context / Constraints / Done-when**: name the exact files, folders, docs, and the literal failing test or stack trace near the top; state a verifiable end state ("tests pass", "bug no longer repros", "touch only X"). Keep conventions, build/test commands, and style rules *out* of the task prompt and *in* AGENTS.md.

**Reasoning.** Effort is a config/CLI dial (`minimal | low | medium | high | xhigh` via `model_reasoning_effort`, `/model`, `--config`) — never coaxed with "think harder". **medium** is the interactive default; low for quick scoped edits; high/xhigh for hard long-horizon debugging. It allocates reasoning dynamically per step, so raising the tier on easy work just adds latency and worsens over-editing. It is concise by default and mirrors the user's tone; suppress its short collaborative progress preambles with an explicit "no status updates, only a final summary."

**Tools & sandbox.** Trained on OpenAI's exact `apply_patch` diff format — use it verbatim in custom harnesses. Prefers `read_file`/`list_dir` over shell, `rg` over grep, batches independent reads. The default sandbox is **workspace-write ("Auto")**, which **blocks network access** — prompts relying on dep installs or URL fetches silently fail unless `network_access` is enabled. Bias-to-action is built in: "default to implementing with reasonable assumptions; do not end your turn with clarifications unless truly blocked" (verbatim). Govern this with scope constraints + a tight sandbox, not autonomy prompts.

**Corrections folded in — two significant ones.**
- **Model:** GPT-5.3-Codex is **deprecated**, not current. The current Codex default is **GPT-5.6** (Terra = balanced default, Sol = flagship for hard work, Luna = fast), GA July 9 2026. Tune to that.
- **AGENTS.md is NOT "re-read every turn" and does NOT "survive compaction."** That was mis-attributed from Claude Code's CLAUDE.md. Codex builds the instruction chain **once per session (per launched TUI run)**; there is an open feature request (#8547) asking it to re-read mid-session and a bug (#5772) that it does *not* re-read after auto `/compact`. Practical consequence: keep AGENTS.md lean *and* re-state anything critical after a compaction. Precedence is correct: global `~/.codex/AGENTS.md` (with `AGENTS.override.md`) → git root → walk down to cwd, closer files overriding, ~32 KiB cap (`project_doc_max_bytes`).

---

## 3. Google Gemini 3.x (`google-gemini`)

**One-liner:** Rewards terse, direct, context-first prompts at the default temperature of 1.0; leans on native "thinking" instead of hand-written CoT; and actively punishes habits imported from GPT/Claude (lowering temperature, CoT scaffolding, dropping tool-loop signatures).

**System-prompt style.** Use the dedicated top-level `system_instruction` field, separate from `contents`. Google's recommended order: (1) role identity, (2) environmental context, (3) behavioral rules, (4) exact output format. XML-style tags OR Markdown headings both work — there is **no strong XML affinity** like Claude — but pick ONE and stay consistent; mixing hurts. Keep it short; 300+ line instruction blocks stop being verifiable. Add an explicit current-date clause for time-sensitive tasks and a grounding clause to cut hallucination. Gemini leans on **few-shot examples and response prefixes** more than GPT/Claude.

**Reasoning.** Gemini 3 uses categorical `thinking_level` (`minimal|low|medium|high`) — **not** hand-written "think step by step." Drop to low/minimal for simple instruction-following or high-throughput work. Thought summaries are opt-in (`includeThoughts:true`); you're billed for thinking tokens.

**Corrections folded in.** Two factual fixes to the reasoning claim:
- **Defaults:** high is the default only on **Gemini 3 Pro (3.1 Pro)**. The current **Gemini 3.5 Flash defaults to *medium*, not high** (only the older `gemini-3-flash-preview` defaulted to high).
- **`thinking_budget` on Gemini 3:** the absolute "cannot be used on 3" is false. `thinking_budget` **is accepted on Gemini 3 for backward compatibility** (though discouraged — on 3 Pro it may degrade performance). The real hard constraint is that you **cannot send both `thinking_level` and `thinking_budget`** in one request (400). Gemini 2.5 still uses numeric `thinking_budget` (-1 dynamic, 0 off on Flash/Flash-Lite; 2.5 Pro can't fully disable), and `thinking_level` is not supported on 2.5.

**Context & tools.** 1M input window, 64k output. **Context-first is doctrine:** supply all data/context FIRST, put the specific instruction/question at the very END, and bridge explicitly ("Based on the document above, …") — verified in Google's own prompting-strategies page. The big Gemini-3 gotcha: function-call responses carry an encrypted **`thought_signature`**. In stateless/manual-history mode you MUST append the entire returned `Content` object (signatures intact) — omitting it on the first `functionCall` part of a step returns a 400. Gemini 3 enforces this far more strictly than 2.5 (it has broken tool loops in ADK, goose, LibreChat). Prefer the Python SDK's automatic/stateful function calling, which round-trips signatures for you. Native structured output (`response_schema` + `response_mime_type='application/json'`) now has near-full JSON Schema support and works out-of-the-box with Pydantic/Zod; order schema keys so rationale fields precede the final answer.

---

## 4. Anthropic Claude Opus 4.8 (`anthropic-claude`)

**One-liner:** A literal, lean-prompt frontier family where you set an effort dial and trust the model's own reasoning — aggressive "CRITICAL/you MUST" scaffolding and hand-written step plans now backfire, causing overtriggering and overthinking.

**System-prompt style.** Lean Markdown headings plus XML tags for content separation — *not* maximalist. A one-sentence role is enough. Place long/reference data at the **TOP** and put the query/instructions/examples at the **END** (up to ~30% quality gain on complex multi-doc inputs, verified). Because current models follow instructions **literally and won't generalize** an instruction across items, state scope explicitly ("apply this to every section, not just the first"). Provide the reason behind a rule ("do X because Y") — the model generalizes from the explanation. Wrap docs in `<document>`/`<document_content>`/`<source>`.

**Reasoning.** `output_config.effort` (`low|medium|high|xhigh|max`) is the **primary** control, paired with adaptive thinking. On Opus 4.8/4.7, adaptive is the only *thinking-on* mode and thinking is **OFF unless you set `thinking:{type:'adaptive'}`**; manual `budget_tokens` returns a 400. (Correction/precision: `thinking:{type:'disabled'}` is *also* still accepted and is behaviorally equivalent to omitting — "adaptive is the only mode that turns thinking on".) API default = high (identical to omitting). Start **xhigh for coding/agentic, high minimum** for intelligence-sensitive work; if reasoning is shallow, **raise effort** rather than prompting around it. Reserve `max` for frontier problems (can overthink). Effort governs *all* tokens including tool calls; at xhigh/max set large `max_tokens` (~64k) since thinking counts toward it. Scope note: the "start at xhigh" advice is Opus-4.7/4.8-specific — Sonnet 5 defaults to high, Fable 5 starts at high.

**The key 2026 shift (verified verbatim).** Dial back aggressive tool-forcing language. "CRITICAL: You MUST use this tool" and "If in doubt, use [tool]" now cause **overtriggering** on 4.5/4.6+ (and the even-more-literal 4.7/4.8). The fix: plain "Use this tool when it would help." Prefer general guidance — "think thoroughly", "self-verify before finishing" — over hand-written step plans; "Claude's reasoning frequently exceeds what a human would prescribe."

**Model-specifics.** Opus 4.8 favors reasoning over tool calls and spawns fewer subagents by default — raise effort or give explicit criteria to increase both. The Opus line lacks the context-awareness self-tracking that Sonnet 5/4.6/Haiku 4.5 have, so tell it about your harness's compaction or it may wrap up early. Non-default temperature/top_p/top_k return a 400 on Opus 4.7+. Prefilled assistant turns are removed on 4.6+ (400) — use Structured Outputs or a "respond directly without preamble" instruction. When thinking is off, Opus is unusually sensitive to the word "think" — use "consider/evaluate/reason through." **Code-review harness gotcha:** 4.8 obeys "only high-severity / be conservative" so faithfully that recall regressed — instead instruct "report every finding with confidence + severity; filter downstream."

---

## 5. Anthropic Claude Fable 5 (`anthropic-fable`)

**One-liner:** A frontier long-horizon agent that rewards terse, high-level specs plus explicit intent and boundaries — and actively punishes the over-prescriptive, enumerate-every-rule, show-your-work prompting that worked on Opus. (No corrections needed — all five claims verified.)

**System-prompt style.** Same Claude conventions, but the load-bearing shift is **less prescription, not more.** Front-load the goal, the intent/"why + who it's for", the constraints, and the pause/autonomy boundaries — then stop. Do NOT enumerate step-by-step procedures; Anthropic states prior-model skills are "often too prescriptive for Claude Fable 5 and can degrade output quality," and one brief instruction now steers a behavior as well as a long enumerated list did on Opus. Give it the hardest, fully-specified version of the problem and let it scope, ask, and execute ("start at the top of your difficulty range"). State boundaries it otherwise over-reaches on ("the deliverable is your assessment — report findings and stop; don't apply a fix until asked") plus a checkpoint rule ("pause only for destructive/irreversible actions, real scope changes, or input only the user can provide; otherwise keep going").

**Reasoning.** Controlled entirely through `effort` (`low|medium|high|xhigh|max`). **Adaptive thinking is ALWAYS ON and cannot be disabled** (`type:'disabled'` rejected, no `budget_tokens`) — unlike Sonnet 5 (can disable) and Opus 4.8 (must opt in). The recommended default and starting point is **`high`, not xhigh**; lower-effort Fable "often exceeds xhigh performance on prior models," so defaulting everything to xhigh/max wastes cost and causes unrequested refactoring, option-surveying, and scope creep. Raw chain-of-thought is **never** returned — set `thinking.display:'summarized'` to read a summary. `max_tokens` is a **hard cap over thinking + text combined**; set it generously.

**Guardrail — the sharp one.** **Never** instruct it to echo, transcribe, reflect on, or "show your thinking" — this trips the `reasoning_extraction` safety classifier, returns `stop_reason:'refusal'`, and forces elevated fallback to Opus 4.8. Read summarized thinking blocks or use a `send_to_user` tool instead. Also expect refusals in offensive-cyber and bio/life-sciences (even some benign ones) — wire an Opus 4.8 fallback rather than treating a refusal as an error.

**Long-horizon behavior.** Two Fable-specific failure modes: (a) it may end a very long session with "I'll now run X" without the tool call, or ask permission it doesn't need — an autonomous-mode reminder ("continue / do it end to end") fixes it; (b) surfacing a remaining-token countdown triggers premature "let's start a new session"/self-trimming — avoid showing budget counts, or add "You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits." It dispatches parallel/long-lived subagents more readily than Opus (orchestrate asynchronously), and fresh-context verifier subagents beat self-critique. Provide a markdown memory/notes file (one lesson per file) — a distinctive Fable strength. Single requests run many minutes and autonomous runs run hours, so check runs asynchronously and never set tight timeouts or small `max_tokens`.

---

## 6. xAI Grok 4.5 (`xai-grok`)

**One-liner:** A reasoning-first, natively-agentic model with unique real-time X/web search — prompt it flat and direct, tune `reasoning_effort` instead of adding CoT, and supply your own guardrails because the base persona is deliberately less filtered than Claude/GPT.

**System-prompt style.** OpenAI-compatible `system/user/assistant` (Chat Completions and Responses APIs) — not a bespoke schema. Write the system prompt as **flat, direct Markdown prose**, matching xAI's own published prompts (`xai-org/grok-prompts` ships plain Jinja/prose, not XML scaffolding). Front-load: (1) identity/persona; (2) **your** safety/guardrail rules — the base model's default persona is "treat users as adults, don't moralize, be truth-seeking," so it is less filtered and follows whatever persona you give it (specify refusal behavior if you need it; it won't over-refuse); (3) tool definitions and real-time-source scoping. Heavy XML tags and defensive moralizing framing cut against the model's grain.

**Reasoning.** **Always on** on flagship 4.5 and cannot be disabled; tune depth with `reasoning_effort` = `low|medium|high` (default **high**). The exception is **Grok 4.3** (Bedrock/Foundry), which adds `effort:'none'` to disable thinking and defaults to **low** there. The **Grok 4.20 multi-agent** variant repurposes `reasoning.effort` to select **agent count (4 or 16)**, not thinking depth (correction: it exposes four levels, `low|medium|high|xhigh`). Do NOT add "think step by step" — reasoning is native and the trace isn't returned on Chat Completions (retrievable encrypted via the Responses API `include:["reasoning.encrypted_content"]`). Defaults differ from OpenAI: **temperature 0.7, top_p 0.95, `max_completion_tokens` 131072** — set them explicitly.

**Tools & context.** Native, trained-in tool use with parallel calls. Beyond your functions, xAI exposes server-side agentic tools via the `tools` param: **`x_search()`, `web_search()`, `code_execution`** — the model decides when to invoke and returns a `citations` field. `x_search()` params: `allowed_x_handles`/`excluded_x_handles` (≤20 each, mutually exclusive), `from_date`/`to_date`, image/video understanding. This X-search is Grok's standout differentiator. **Correction:** the older `search_parameters` "Live Search" block was **retired Jan 12 2026 (now returns 410 Gone)** — use the agentic tools; the fact is verified (the originally-cited aibase URL was wrong — it described the launch, not retirement). Constraint: `presence_penalty`, `frequency_penalty`, and `stop` are **not supported on reasoning models** and error. Knowledge cutoff Feb 1 2026 — route newer/fast-moving queries to live search. Set `prompt_cache_key` / `x-grok-conv-id` for reliable caching.

---

## 7. Open-Weight Self-Host — DeepSeek / Qwen / Llama (`open-weight`)

**One-liner:** Template-first and sampling-sensitive: getting the chat template, special tokens, and recommended sampling right matters more than prose prompt-craft — and "system prompt" behavior differs sharply per family. (No corrections needed — all five claims verified; two notation nits below.)

**System-prompt style.** The dominant variable is the exact **chat template / special tokens**, not Markdown-vs-XML. Render every prompt through the model's official template (HF `apply_chat_template`, or the runtime's `--jinja`) and verify it — a wrong template silently degrades everything. Then, per family:
- **DeepSeek-R1 and R1-distills:** use **NO system prompt** — put persona, instructions, constraints, and output format in the **user turn** (its RL tuning conflicts with a system persona). Avoid few-shot examples; they consistently degrade R1. Zero-shot direct instructions.
- **DeepSeek-V3/V3.1 non-thinking chat:** a normal system prompt is fine.
- **Qwen3 and Llama 4:** ship with **no baked-in default system prompt** and follow an explicit one well — spell out role, steps, output format, and (for Llama especially) **include examples**. Keep it short; small quantized models lose the thread on long multi-constraint prompts, so front-load the 2–3 must-obey rules and restate the output format near the end (recency helps).

Do not port one system prompt across families unchanged.

**Reasoning.** No single "effort" knob — per-family, template-driven. Hybrids (Qwen3, DeepSeek-V3.1) toggle via a template flag (Qwen `enable_thinking`, DeepSeek `thinking=True`) or Qwen soft switches `/think` `/no_think` (single-slash; the *most recent* switch wins in a thread). Pure reasoners (DeepSeek-R1) always think — do NOT add CoT scaffolding. **Local pitfall:** many GGUF chat templates drop the opening `<think>` tag, so the model skips reasoning or loops — pin fixed/reuploaded templates and confirm the tag is emitted. Strip prior `<think>` content from history (keep only final answers).

**Sampling (set explicitly).** Qwen3 thinking = temp 0.6 / top_p 0.95 / top_k 20; Qwen3 non-thinking = 0.7 / 0.8 / 20; DeepSeek-R1 = temp 0.6, no system prompt. **Never greedy-decode a thinking model** (degradation + endless repetition). Set generous `max_tokens` (Qwen3 ~32,768 normal / ~38,912 hard) or you truncate mid-`<think>`. For math, Qwen3 recommends the literal "Please reason step by step, and put your final answer within `\boxed{}`" — that's for *extraction*, not eliciting reasoning.

**Tools — the #1 thing that breaks at self-host.** Reliability is materially below frontier and format-fragile. Use each family's native tool template with the matching runtime parser (Qwen3 = Hermes-style / vLLM `--tool-call-parser hermes`; Llama 4 = `<|python_start|>…<|python_end|>`; DeepSeek's own tokens). Do **not** use ReAct/stopword tool loops on reasoning models (stopwords surface inside `<think>` and misfire). **DeepSeek-V3.1 tool calling is reliable only in NON-thinking mode** — thinking-mode tool calling first arrived in V3.2; route V3.1 agent turns to non-thinking. Biggest reliability lever: **constrained decoding** (llama.cpp GBNF, vLLM `guided_json`, Outlines) makes schema-invalid output mechanically impossible — always prefer it over trusting instructions, and still wrap calls with validation + retry.

**Context.** Advertised windows are large but effective use degrades, and local KV-cache/VRAM usually forces a much smaller deployed `n_ctx` than the spec sheet. Design to the actual configured window.

---

## Comparison Table

| Dimension | GPT-5.6 (Sol) | Codex (GPT-5.6) | Gemini 3.x | Opus 4.8 | Fable 5 | Grok 4.5 | Open-weight |
|---|---|---|---|---|---|---|---|
| **Prompt fencing** | XML tags + Markdown inside | Flat Markdown `##` | XML *or* MD (pick one) | Lean MD + XML tags | Lean MD + XML tags | Flat prose | Chat template is king |
| **Effort dial** | `reasoning_effort` none→max | `model_reasoning_effort` minimal→xhigh | `thinking_level` minimal→high | `effort` low→max | `effort` low→max | `reasoning_effort` low→high | per-family flag |
| **Effort default** | medium | medium | high (Pro) / **medium (Flash)** | high | **high** | high (4.5) / low (4.3) | n/a |
| **Recommended start** | medium, A/B one lower | medium | high (Pro) | **xhigh** (coding) | **high** | high | n/a |
| **Can disable thinking?** | yes (`none`) | yes (`minimal`) | 2.5 yes; 3 via level | yes (omit/disabled) | **No — always on** | **No** (4.5); yes (4.3 `none`) | yes (hybrids) |
| **Elicitation** | assume-and-proceed | assume-and-proceed | context-first | context-first | context-first | assume-and-proceed | assume-and-proceed |
| **Context placement** | Role/goal front; consistency > length | Exact files/error front | **Data first, question last** | **Docs top, query end** | Intent+spec front, task restated end | Stable content front (cache) | Rules front + restate end |
| **Structured output** | strict Structured Outputs | (via patch/tools) | `response_schema` (Pydantic/Zod) | Structured Outputs | Structured Outputs | JSON via schema | **constrained decode (GBNF)** |
| **Sampling locked?** | no | no | **temp must = 1.0** | **non-default = 400** (4.7+) | **non-default = 400** | reasoning: no penalty/stop | set family recs |
| **Signature tax on tools** | — | `apply_patch` format | **`thought_signature` round-trip** | — | pass thinking blocks back | `citations` returned | template/parser match |
| **Durable memory** | dedupe, one place | **AGENTS.md (once/session)** | — | filesystem discovery | markdown notes file | prompt_cache_key | strip stale `<think>` |
| **CoT scaffolding** | no (raise effort) | no | no (raise level) | no (say "think thoroughly") | no (& never "show reasoning") | no | no (R1/Qwen3-think) |
| **Standout** | contract-following | autonomous coder | real-time multimodal + terse | literal + long-context | long-horizon autonomy | live X/web search | template/sampling control |

---

## What Changed in 2026

**1. The effort dial replaced prompt-craft for reasoning depth — everywhere.** Every frontier model now exposes an explicit setting (GPT/Codex `reasoning_effort`, Claude/Fable `effort`, Gemini `thinking_level`, Grok `reasoning_effort`). "Think step by step" went from best practice to redundant-or-harmful. Anthropic deprecated manual `budget_tokens` (400 on Opus 4.7/4.8, Sonnet 5, Fable 5); OpenAI's true zero is now `none` (superseded `minimal`); Gemini swapped numeric budgets for categorical levels.

**2. Lean beat maximal — and the vendors quantified it.** OpenAI reports leaner prompts improving coding-agent evals ~10–15% while cutting tokens 41–66% (directional). Anthropic documented that aggressive "CRITICAL/you MUST/if in doubt use X" now *overtriggers* on Opus 4.5–4.8, and that "think thoroughly" beats hand-written step plans. Fable's entire prompting guide is built around prior-model skills being "too prescriptive." Gemini warns 300+ line instruction blocks stop being verifiable. The enumerate-every-rule mega-prompt is now a frontier-model anti-pattern. (Exception: small/quantized open-weight models and Llama still want explicit structure + examples.)

**3. Sampling params got locked down.** Gemini 3 mandates temp 1.0 (lowering it causes looping). Claude Opus 4.7+/Sonnet 5/Fable 5 reject non-default temp/top_p/top_k with a 400. Grok reasoning models reject `presence_penalty`/`frequency_penalty`/`stop`. Porting a low-temperature determinism habit across providers is now an error, not a preference.

**4. Tool loops sprouted provider-specific invariants.** Gemini 3 began strictly enforcing `thought_signature` round-tripping (breaking ADK/goose/LibreChat). xAI retired the `search_parameters` Live Search block (Jan 12 2026 → 410 Gone) for server-side agentic tools. DeepSeek moved tool-calling into thinking mode only at V3.2 (V3.1 is non-thinking-only). Hybrid think/non-think became the default open-weight architecture (Qwen3, DeepSeek-V3.1+), superseding "pick R1 vs V3." A tool harness tuned for one provider now breaks on another.

**5. Version churn accelerated — tune to primitives, not versions.** GPT went 5.1→5.6 ("Sol/Terra/Luna" tiers) in months, with 5.1 and 5.2 pulled from ChatGPT. GPT-5.3-Codex is already deprecated; Codex now runs on GPT-5.6. Gemini 3.5 Flash's default thinking level shifted from the preview's high to medium. Fable 5 launched, was pulled, and redeployed. The durable, portable primitives survived all of it: message roles, the effort dial, strict/schema-enforced structured output, XML-vs-Markdown fencing conventions, and context placement.

**6. Memory surfaces are real but easy to mis-port.** Codex's AGENTS.md is loaded **once per session** — it is *not* re-read every turn and *not* restored after compaction (those are Claude Code CLAUDE.md properties). Fable rewards an external markdown memory file; Claude discovers state from the filesystem. Getting these confused silently degrades long-horizon agents.


## Cross-model principles

- The effort/reasoning DIAL replaced prompt-craft for depth on every frontier model (GPT/Codex reasoning_effort, Claude/Fable effort, Gemini thinking_level, Grok reasoning_effort). Raise the dial rather than writing 'think step by step'. DIVERGENCE: defaults and starting points differ (Opus start xhigh, default high; Fable start/default high; Gemini high on Pro / medium on Flash; GPT-5.6 and Codex medium; Grok 4.5 high) and Fable-5 + Grok-4.5-flagship CANNOT turn thinking off, while GPT, Codex, Gemini, and Sonnet 5 can.
- Native reasoning killed hand-written chain-of-thought — 'think step by step' is redundant-to-harmful on all current reasoners. EXCEPTION: open-weight math still uses 'put your final answer in \boxed{}' as an answer-EXTRACTION instruction, not a reasoning-elicitation one.
- Lean beats maximal on frontier models: aggressive CRITICAL/you-MUST and enumerated mega-prompts now DEGRADE output (Claude tool overtriggering, Fable over-specification, GPT contract instability, Gemini over-prompting). DIVERGENCE: small/quantized open-weight models and Llama 4 STILL want explicit structure + examples ('clarity + examples = reliability').
- Structured output should be enforced by SCHEMA, not requested in prose: strict Structured Outputs (GPT/Claude), response_schema (Gemini), constrained decoding/GBNF/guided_json (open-weight). 'Please return JSON' and legacy JSON Mode are anti-patterns.
- Context placement is doctrine but model-split: Claude and Gemini are explicitly CONTEXT-FIRST (data at top, query/instructions at the very end — up to ~30% quality gain on Claude); GPT, Codex, and Grok front-load role/goal/constraints (and, for Codex, the exact files + failing test). All benefit from putting stable content first for prompt caching.
- State each rule ONCE — contradictions and redundancy destabilize contract-following/literal models (explicit for GPT-5.6, and a consequence of Claude/Fable literalism where an instruction won't generalize across items unless you say so).
- Sampling params are increasingly LOCKED and non-portable: Gemini 3 mandates temp 1.0 (lowering it loops), Claude Opus 4.7+/Sonnet 5/Fable reject non-default temp/top_p/top_k with 400, Grok reasoning models reject presence/frequency/stop. Porting a low-temperature determinism habit across providers is an error, not a preference.
- Tool loops have provider-specific invariants that break cross-provider harnesses: Gemini's thought_signature round-trip (400 if dropped), Grok's retired Live Search → agentic x_search/web_search, Codex's exact apply_patch format, and open-weight's template↔parser matching + constrained decoding. DeepSeek adds a mode split (V3.1 tool calls only in non-thinking; thinking-mode arrived in V3.2).
- Durable-memory surfaces differ and are easy to mis-port: Codex AGENTS.md is loaded ONCE per session (NOT re-read per turn, NOT compaction-restored — those are Claude Code CLAUDE.md properties); Fable rewards an external markdown notes file (one lesson per file); Claude discovers state from the filesystem, sometimes making a fresh context window better than compaction.
- Version churn is fast and version-specific tuning ages in months (GPT 5.1→5.6, GPT-5.3-Codex already deprecated → Codex on 5.6, Gemini Flash default shifting high→medium, Fable pulled then redeployed). Tune to durable primitives — message roles, the effort dial, schema-enforced output, XML-vs-Markdown fencing conventions, context placement — not version trivia.
- You own the guardrails to differing degrees: Grok's base persona is deliberately less filtered (specify refusal behavior yourself; it won't over-refuse), whereas Fable adds NEW refusal categories (reasoning-extraction, offensive-cyber, bio) that return stop_reason:'refusal' and need an Opus-4.8 fallback wired — so 'be safe' prompting is under-powered on Grok and can be actively triggered on Fable.