#!/usr/bin/env python3
"""Apply model-research workflow output to fablegen profiles.

Usage: python3 scripts/apply_profiles.py <workflow-output.json>

Takes the JSON produced by scripts/model-research.workflow.js (the {synth:{report_md,
profiles,...}} object, possibly wrapped in {result:{...}}), and writes:
  - docs/model-prompting-guide.md   (the full reference)
  - fablegen/profiles/*.json         (lean, per-model profiles)

Keeps profiles LEAN (fablegen's whole thesis): role_hint nulled (role is task-inferred),
idioms trimmed to 2 first-sentences, one first-sentence guardrail, loop guidance folded into
notes (never replacing the operating loop). Run the unittest suite after — it enforces
leanness + shape: `python3 -m unittest discover -s tests -q`.
"""
import json, pathlib, re, sys

FAB = pathlib.Path(__file__).resolve().parent.parent
PDIR = FAB / "fablegen" / "profiles"
FIELDS = ["id", "display", "family", "tagline", "role_hint", "effort_line",
          "elicitation", "idioms", "guardrail_extra", "verify_note", "loop_override", "notes"]

# research family id -> [(fablegen id, display, extra note)]
MAP = {
    "openai-gpt":       [("gpt-5.6", "GPT-5.6 (ChatGPT / Sol·Terra)", "")],
    "openai-codex":     [("codex", "OpenAI Codex (GPT-5.6)", "")],
    "google-gemini":    [("gemini-3", "Google Gemini 3.x", "")],
    "xai-grok":         [("grok-4", "xAI Grok 4.x", "")],
    "open-weight":      [("local", "Open-weight / local (DeepSeek·Qwen·Llama)", "")],
    "anthropic-fable":  [("fable-5", "Claude Fable 5", "")],
    "anthropic-claude": [("opus-4.8", "Claude Opus 4.8", ""),
                         ("sonnet-5", "Claude Sonnet 5",
                          " Sonnet-specific: faster and more literal than Opus — spell out structure; it infers less.")],
}


def first_sentence(s):
    return re.split(r"(?<=[.!?]) ", (s or "").strip())[0]


def lean(p, fid, display, extra_note):
    out = {}
    for k in FIELDS:
        v = p.get(k)
        if k == "id":                out[k] = fid
        elif k == "display":         out[k] = display
        elif k == "role_hint":       out[k] = None        # role is task-inferred (keeps has_role + lean)
        elif k == "loop_override":   out[k] = None         # never replace the operating loop
        elif k == "verify_note":     out[k] = v if v else None
        elif k == "idioms":          out[k] = [first_sentence(x) for x in (v or [])[:2]]
        elif k == "guardrail_extra": out[k] = [first_sentence((v or [""])[0])] if v else []
        elif k == "notes":
            note = (v or "").strip()
            if p.get("loop_override"):
                note = (note + " Loop note: " + p["loop_override"]).strip()
            out[k] = (note + extra_note).strip()
        else:                        out[k] = v or ""
    return out


def main(path):
    data = json.loads(pathlib.Path(path).read_text())
    synth = data.get("synth") or (data.get("result") or {}).get("synth")
    if not synth:
        sys.exit("no synth in output")
    by = {p["id"]: p for p in synth["profiles"]}

    (FAB / "docs").mkdir(exist_ok=True)
    report = ("# Model Prompting Guide\n\n> Auto-researched reference. Feeds fablegen's "
              "per-model profiles.\n\n") + synth["report_md"]
    if synth.get("cross_model_principles"):
        report += "\n\n## Cross-model principles\n\n" + "\n".join("- " + x for x in synth["cross_model_principles"])
    (FAB / "docs" / "model-prompting-guide.md").write_text(report)
    print("wrote docs/model-prompting-guide.md")

    written = 0
    for rid, targets in MAP.items():
        if rid not in by:
            print("  WARN research missing:", rid); continue
        for fid, display, extra in targets:
            (PDIR / (fid + ".json")).write_text(
                json.dumps(lean(by[rid], fid, display, extra), indent=2, ensure_ascii=False) + "\n")
            written += 1
            print("  wrote profile:", fid)
    print("done: {} profiles".format(written))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: apply_profiles.py <workflow-output.json>")
    main(sys.argv[1])
