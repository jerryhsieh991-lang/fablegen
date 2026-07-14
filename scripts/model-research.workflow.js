export const meta = {
  name: 'model-prompt-research',
  description: 'Deep-research per-model prompting guidance (GPT/Codex/Gemini/Claude/Fable/Grok/open) to refresh fablegen profiles',
  phases: [
    { title: 'Research', detail: 'one web-research agent per model family' },
    { title: 'Verify', detail: 'adversarially refute shaky prompting claims per model' },
    { title: 'Synthesize', detail: 'merge into report + fablegen profile JSONs' },
  ],
}

const TODAY = '2026-07-13'

const MODELS = [
  { key: 'openai-gpt',   name: 'OpenAI ChatGPT / GPT-5.x (instant + thinking)', family: 'openai',
    focus: 'system-prompt style, reasoning_effort + verbosity params, structured outputs, tool/function calling format, Markdown-vs-XML preference, over-asking penalties, what degrades it' },
  { key: 'openai-codex', name: 'OpenAI Codex (codex CLI / coding agent)', family: 'openai',
    focus: 'how prompting a coding AGENT differs from a chat model, AGENTS.md conventions, autonomy/approval, tool use, planning, what makes Codex agents drift or over-edit' },
  { key: 'google-gemini', name: 'Google Gemini 2.5 / 3.x', family: 'google',
    focus: 'system_instruction usage, very-long-context behavior, thinking/reasoning mode, structured output/JSON mode, what is unique vs GPT/Claude, known prompting quirks' },
  { key: 'anthropic-claude', name: 'Anthropic Claude Opus/Sonnet/Haiku 4.x', family: 'claude',
    focus: 'XML tags, extended thinking, tool use, context-before-task, lean-prompt behavior, why over-prescriptive prompts DEGRADE frontier Claude, effort scaling' },
  { key: 'anthropic-fable', name: 'Anthropic Fable 5 (frontier reasoning)', family: 'claude',
    focus: 'how to prompt Fable 5 specifically, give-full-spec-up-front behavior, reasoning effort, where it differs from Opus, cost/limits implications for prompting' },
  { key: 'xai-grok', name: 'xAI Grok 4.x', family: 'xai',
    focus: 'system prompt style, reasoning mode, tool use, real-time/X integration, prompting quirks vs other frontier models' },
  { key: 'open-weight', name: 'Open-weight (DeepSeek, Qwen, Llama) for local/self-host', family: 'open',
    focus: 'prompting quantized/local instruct models, chat templates, system-prompt sensitivity, tool-use reliability at small scale, what breaks vs frontier' },
]

const RESEARCH_SCHEMA = {
  type: 'object',
  required: ['model_key', 'one_liner', 'system_prompt_style', 'reasoning_control', 'verbosity_control', 'tool_use', 'context_handling', 'elicitation', 'idioms', 'guardrails', 'recent_changes', 'claims'],
  properties: {
    model_key: { type: 'string' },
    one_liner: { type: 'string', description: 'one-sentence prompting character of this model' },
    system_prompt_style: { type: 'string', description: 'how to structure the system prompt (Markdown/XML/flat, context placement)' },
    reasoning_control: { type: 'string', description: 'how to control reasoning/effort/thinking for this model' },
    verbosity_control: { type: 'string', description: 'how to control output length/verbosity' },
    tool_use: { type: 'string', description: 'tool/function-calling format and reliability notes' },
    context_handling: { type: 'string', description: 'context window, long-context behavior, what to front-load' },
    elicitation: { type: 'string', enum: ['ask-heavy', 'balanced', 'context-first', 'assume-and-proceed'], description: 'how much this model should ask vs assume' },
    idioms: { type: 'array', items: { type: 'string' }, description: '2-4 concrete DO patterns specific to this model' },
    guardrails: { type: 'array', items: { type: 'string' }, description: '2-4 concrete AVOID patterns (model-specific anti-patterns)' },
    recent_changes: { type: 'array', items: { type: 'string' }, description: 'notable prompting-relevant changes in the last ~3 months (2026)' },
    claims: { type: 'array', items: { type: 'object', required: ['claim', 'source', 'confidence'], properties: { claim: { type: 'string' }, source: { type: 'string' }, confidence: { type: 'string', enum: ['high', 'medium', 'low'] } } }, description: 'the 3-5 most load-bearing, falsifiable claims with a source URL each' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['model_key', 'verified', 'corrections'],
  properties: {
    model_key: { type: 'string' },
    verified: { type: 'array', items: { type: 'string' }, description: 'claims that held up' },
    corrections: { type: 'array', items: { type: 'string' }, description: 'claims that were myths/outdated/wrong, with the correction' },
  },
}

phase('Research')
const researched = await pipeline(
  MODELS,
  (m) => agent(
    `You are a prompt-engineering researcher. Today is ${TODAY}. Research CURRENT (2026) prompting best practices for: ${m.name}.\n` +
    `Use web search — your training may be stale. Focus on: ${m.focus}.\n` +
    `Goal: this feeds a multi-model master-prompt generator that tunes prompts PER MODEL. So report what ACTUALLY differs for this model when writing its system prompt / task prompt — not generic advice.\n` +
    `Be skeptical of prompt-engineering folklore; prefer official docs (model cards, prompting guides, cookbooks) and recent primary sources. Give a source URL for each load-bearing claim.\n` +
    `Return the structured schema for model_key="${m.key}".`,
    { label: `research:${m.key}`, phase: 'Research', schema: { ...RESEARCH_SCHEMA, properties: { ...RESEARCH_SCHEMA.properties } } }
  ),
  (r) => r && agent(
    `Adversarially fact-check this model's prompting claims. Today is ${TODAY}. Model: ${r.model_key}.\n` +
    `For EACH claim below, try to REFUTE it with web search — is it a myth, outdated, or vendor hype? Default to skepticism. A claim only "verifies" if a current primary source supports it.\n` +
    `Claims:\n${(r.claims || []).map((c, i) => `${i + 1}. ${c.claim} (they cited: ${c.source})`).join('\n')}\n` +
    `Return verified[] (claims that held) and corrections[] (myths/outdated, each with the fix).`,
    { label: `verify:${r.model_key}`, phase: 'Verify', schema: VERDICT_SCHEMA }
  ).then((v) => ({ research: r, verdict: v }))
)

const clean = researched.filter(Boolean).filter((x) => x.research)

phase('Synthesize')
const PROFILE = {
  type: 'object',
  required: ['id', 'display', 'family', 'tagline', 'effort_line', 'elicitation', 'idioms', 'guardrail_extra', 'notes'],
  properties: {
    id: { type: 'string' }, display: { type: 'string' }, family: { type: 'string' },
    tagline: { type: 'string' }, role_hint: { type: ['string', 'null'] },
    effort_line: { type: 'string' }, elicitation: { type: 'string' },
    idioms: { type: 'array', items: { type: 'string' } },
    guardrail_extra: { type: 'array', items: { type: 'string' } },
    verify_note: { type: ['string', 'null'] }, loop_override: { type: ['string', 'null'] },
    notes: { type: 'string' },
  },
}
const SYNTH = {
  type: 'object',
  required: ['report_md', 'profiles', 'cross_model_principles'],
  properties: {
    report_md: { type: 'string', description: 'a thorough markdown report: per-model prompting guide + a comparison table + what changed in 2026' },
    cross_model_principles: { type: 'array', items: { type: 'string' }, description: 'principles that hold across all frontier models, and where they diverge' },
    profiles: { type: 'array', items: PROFILE, description: 'one fablegen profile per model researched (id = model_key), corrections folded in' },
  },
}

const synth = await agent(
  `You synthesize per-model prompting research into (1) a rigorous markdown report and (2) fablegen "profiles".\n` +
  `Today is ${TODAY}. fablegen tunes a master-prompt PER MODEL; a profile is JSON with: id, display, family, tagline, role_hint(null ok), effort_line (how to set effort+verbosity for THIS model), elicitation (ask-heavy|balanced|context-first|assume-and-proceed), idioms[] (DO), guardrail_extra[] (AVOID model-specific), verify_note(null ok), loop_override(null ok), notes (dense prose guidance).\n` +
  `CRITICAL: fold each model's verified findings AND corrections (drop myths). Make profiles concrete and model-distinct — a reader must see how prompting GPT differs from Claude differs from Gemini differs from Codex. Lean prompts for frontier reasoners; explicit structure for others.\n` +
  `The report must include: a per-model section, a comparison table, and a "what changed in 2026" section.\n\n` +
  `Per-model verified research + corrections:\n${JSON.stringify(clean.map((x) => ({ model: x.research.model_key, research: x.research, verdict: x.verdict })), null, 1)}`,
  { label: 'synthesize', phase: 'Synthesize', effort: 'high', schema: SYNTH }
)

return { models: clean.length, synth }
