"""fablegen command-line interface."""
import argparse
import sys
from pathlib import Path

from . import __version__
from .generator import build_prompt
from .refine import refine, score_prompt
from .skills import load_registry


def _add_build_args(p):
    p.add_argument("task", help="what you want the model to do (quote it)")
    p.add_argument("--role", help="override the role line")
    p.add_argument("--success", help="concrete, testable success criteria")
    p.add_argument("--skills", help="comma-separated skill names to force in")
    p.add_argument("--no-loop", dest="loop", action="store_false",
                   help="omit the operating-loop block")
    p.add_argument("--save", metavar="PATH", help="also write the prompt to a file")


def _build_kwargs(args):
    forced = [s for s in (args.skills.split(",") if args.skills else []) if s.strip()]
    return dict(role=args.role, success=args.success,
                skills=forced or None, loop=args.loop)


def _emit(text, save):
    if save:
        Path(save).write_text(text, encoding="utf-8")
        print("saved -> {}".format(save), file=sys.stderr)
    print(text)


def cmd_new(args):
    text = build_prompt(args.task, **_build_kwargs(args))
    _emit(text, args.save)
    score, _, findings = score_prompt(text, args.loop)
    note = " · to improve: {}".format(", ".join(findings)) if findings else " · clean"
    print("\n# lint: score {:.2f}{}".format(score, note), file=sys.stderr)
    return 0


def cmd_loop(args):
    prompt, trail = refine(args.task, _build_kwargs(args),
                           iterations=args.iterations, api=args.api, model=args.model)
    _emit(prompt, args.save)
    print("\n# refine trail:", file=sys.stderr)
    for t in trail:
        line = "  iter {} [{}] score {:.2f}".format(t["iter"], t["mode"], t["score"])
        if t["action"] != "none":
            line += " · " + t["action"]
        if t["findings"]:
            line += " · left: " + ", ".join(t["findings"])
        print(line, file=sys.stderr)
    return 0


def cmd_skills(args):
    for e in load_registry():
        print("{:<24} {}".format(e["name"], ", ".join(e["triggers"])))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="fablegen",
        description="Generate lean, Fable-5-tuned master prompts (goal + loop + skills).")
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
                        help="use Fable 5 to rewrite (needs ANTHROPIC_API_KEY)")
    p_loop.add_argument("--model", default="claude-fable-5")
    p_loop.set_defaults(func=cmd_loop)

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
