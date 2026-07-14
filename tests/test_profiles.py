"""Profile + interview coverage."""
import unittest

from fablegen.generator import build_prompt
from fablegen.profiles import list_profiles, load_profile
from fablegen.interview import run_interview


EXPECTED = {"fable-5", "opus-4.8", "sonnet-5", "gpt-5.5-instant", "claude-design"}


class TestProfiles(unittest.TestCase):
    def test_all_expected_profiles_present(self):
        self.assertTrue(EXPECTED.issubset(set(list_profiles())))

    def test_every_profile_loads_with_required_fields(self):
        for pid in list_profiles():
            prof = load_profile(pid)
            for field in ("id", "display", "tagline", "elicitation"):
                self.assertIn(field, prof, "{} missing {}".format(pid, field))

    def test_unknown_profile_raises(self):
        with self.assertRaises(ValueError):
            load_profile("does-not-exist")

    def test_every_profile_builds_full_prompt(self):
        for pid in list_profiles():
            p = build_prompt("build a small tool", profile=pid)
            self.assertIn("## Discovery", p)
            self.assertIn("## Final check", p)
            self.assertIn(load_profile(pid)["display"], p)

    def test_elicitation_differs_by_model(self):
        self.assertIn("bias to action", build_prompt("x", profile="gpt-5.6"))
        self.assertIn("mine context", build_prompt("x", profile="opus-4.8"))
        self.assertIn("interview first", build_prompt("x", profile="claude-design"))

    def test_gpt_profile_bans_claude_isms(self):
        p = build_prompt("draft something", profile="gpt-5.5-instant")
        self.assertIn("Avoid Claude-isms", p)

    def test_design_profile_uses_custom_loop(self):
        p = build_prompt("design a landing page", profile="claude-design")
        self.assertIn("Operating loop", p)
        self.assertIn("**Understand**", p)  # design-specific loop step
        self.assertIn("**Verify**", p)


class TestInterview(unittest.TestCase):
    def test_non_tty_aborts_cleanly(self):
        out = []
        result = run_interview(read=lambda _q: "", out=out.append, isatty=False)
        self.assertIsNone(result)
        self.assertTrue(any("interactive terminal" in m for m in out))

    def test_scripted_interview_builds_prompt(self):
        answers = iter([
            "build a CLI todo app",          # task
            "for solo devs, offline only",   # context
            "adds/lists/deletes 100 todos with no data loss",  # success
            "opus-4.8",                      # profile
            "dev-loop",                      # skills
            "",                              # accept (no more refine)
        ])
        out = []
        prompt = run_interview(read=lambda _q: next(answers),
                               out=out.append, isatty=True)
        self.assertIn("build a CLI todo app", prompt)
        self.assertIn("offline only", prompt)
        self.assertIn("Claude Opus 4.8", prompt)
        self.assertIn("dev-loop", prompt)


if __name__ == "__main__":
    unittest.main()
