"""fablegen command-line interface."""
import argparse
import sys
from pathlib import Path

from . import __version__
from .generator import build_prompt
from .refine import refine, score_prompt
from .skills import load_registry
from .profiles import list_profiles, load_profile
from .models import resolve_profile, detect_model, model_to_profile
from .config import set_active, clear_active


def _add_build_args(p):
    p.add_argument("task", help="what you want the model to do (quote it)")
    p.add_argument("--profile", default=None,
                   help="force a profile: " + ", ".join(list_profiles()))
    p.add_argument("--model", default=None, metavar="ID|auto",
                   help="pick the profile by model id, or 'auto' to detect the current model")
    p.add_argument("--role", help="override the role line")
    p.add_argument("--success", help="concrete, testable success criteria")
    p.add_argument("--skills", help="comma-separated skill names to force in")
    p.add_argument("--no-loop", dest="loop", action="store_false",
                   help="omit the operating-loop block")
    p.add_argument("--save", metavar="PATH", help="also write the prompt to a file")


def _resolve(args):
    return resolve_profile(explicit_profile=args.profile, model=args.model)


def _build_kwargs(args, profile):
    forced = [s for s in (args.skills.split(",") if args.skills else []) if s.strip()]
    return dict(profile=profile, role=args.role, success=args.success,
                skills=forced or None, loop=args.loop)


def _emit(text, save):
    if save:
        Path(save).write_text(text, encoding="utf-8")
        print("saved -> {}".format(save), file=sys.stderr)
    print(text)


def cmd_new(args):
    profile, reason = _resolve(args)
    text = build_prompt(args.task, **_build_kwargs(args, profile))
    _emit(text, args.save)
    score, _, findings = score_prompt(text, args.loop)
    note = " · to improve: {}".format(", ".join(findings)) if findings else " · clean"
    print("\n# {} ({}) · lint {:.2f}{}".format(profile, reason, score, note), file=sys.stderr)
    return 0


def cmd_loop(args):
    profile, reason = _resolve(args)
    prompt, trail = refine(args.task, _build_kwargs(args, profile),
                           iterations=args.iterations, api=args.api, model=args.api_model)
    _emit(prompt, args.save)
    print("\n# refine trail ({} · {}):".format(profile, reason), file=sys.stderr)
    for t in trail:
        line = "  iter {} [{}] score {:.2f}".format(t["iter"], t["mode"], t["score"])
        if t["action"] != "none":
            line += " · " + t["action"]
        if t["findings"]:
            line += " · left: " + ", ".join(t["findings"])
        print(line, file=sys.stderr)
    return 0


def cmd_interview(args):
    from .interview import run_interview
    prompt = run_interview()
    if prompt and args.save:
        Path(args.save).write_text(prompt, encoding="utf-8")
        print("saved -> {}".format(args.save), file=sys.stderr)
    return 0


def cmd_detect(args):
    m, src = detect_model()
    profile, reason = resolve_profile()
    print("detected model: {}{}".format(m or "(none found)",
                                         " (via {})".format(src) if src else ""))
    print("resolves to profile: {}  — {}".format(profile, reason))
    return 0


def cmd_use(args):
    if args.clear:
        clear_active()
        print("cleared active profile")
        return 0
    if not args.name:
        print("error: give a profile/model, or --clear", file=sys.stderr)
        return 2
    valid = set(list_profiles())
    prof = args.name if args.name in valid else model_to_profile(args.name)
    if not prof or prof not in valid:
        print("error: unknown profile/model '{}'. profiles: {}".format(
            args.name, ", ".join(sorted(valid))), file=sys.stderr)
        return 2
    set_active(prof)
    print("active profile -> {}".format(prof))
    return 0


def cmd_profiles(args):
    for pid in list_profiles():
        prof = load_profile(pid)
        print("{:<18} {}".format(pid, prof.get("tagline", "")))
    return 0


def cmd_skills(args):
    for e in load_registry():
        print("{:<24} {}".format(e["name"], ", ".join(e["triggers"])))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="fablegen",
        description="Generate lean, model-tuned master prompts "
                    "(discovery + goal + loop + skills + final check).")
    ap.add_argument("--version", action="version",
                    version="fablegen {}".format(__version__))
    sub = ap.add_subparsers(dest="cmd")

    p_new = sub.add_parser("new", help="generate a master prompt")
    _add_build_args(p_new)
    p_new.set_defaults(func=cmd_new)

    p_loop = sub.add_parser("loop", help="generate, then refine over N iterations")
    _add_build_args(p_loop)
    p_loop.add_argument("--iterations", type=int, default=3)
    p_loop.add_argument("--api", action="store_true",
                        help="use the model to rewrite (needs ANTHROPIC_API_KEY)")
    p_loop.add_argument("--api-model", default=None,
                        help="override the API model id (default: mapped from profile)")
    p_loop.set_defaults(func=cmd_loop)

    p_int = sub.add_parser("interview",
                           help="interactively answer questions, then generate")
    p_int.add_argument("--save", metavar="PATH", help="write the final prompt to a file")
    p_int.set_defaults(func=cmd_interview)

    p_det = sub.add_parser("detect", help="show the detected model and resolved profile")
    p_det.set_defaults(func=cmd_detect)

    p_use = sub.add_parser("use", help="set the active profile (by profile or model)")
    p_use.add_argument("name", nargs="?", help="profile id or model id")
    p_use.add_argument("--clear", action="store_true", help="clear the active profile")
    p_use.set_defaults(func=cmd_use)

    p_prof = sub.add_parser("profiles", help="list the available model profiles")
    p_prof.set_defaults(func=cmd_profiles)

    p_sk = sub.add_parser("skills", help="list the built-in skill hooks")
    p_sk.set_defaults(func=cmd_skills)

    args = ap.parse_args(argv)
    if not getattr(args, "func", None):
        ap.print_help()
        return 1
    try:
        return args.func(args)
    except (ValueError, RuntimeError) as e:
        print("error: {}".format(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
