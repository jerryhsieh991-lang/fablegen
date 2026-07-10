"""Stdlib unittest suite — run with: python -m unittest discover -s tests"""
import unittest

from fablegen.generator import build_prompt
from fablegen.refine import refine, score_prompt
from fablegen.skills import match_skills


class TestBuild(unittest.TestCase):
    def test_contains_goal_and_task(self):
        p = build_prompt("Fix the login bug and add tests")
        self.assertIn("## Goal", p)
        self.assertIn("Fix the login bug", p)

    def test_loop_included_by_default(self):
        self.assertIn("Operating loop", build_prompt("build a thing"))

    def test_no_loop_flag_omits_block(self):
        self.assertNotIn("Operating loop", build_prompt("build a thing", loop=False))

    def test_empty_task_raises(self):
        with self.assertRaises(ValueError):
            build_prompt("   ")

    def test_custom_success_and_role(self):
        p = build_prompt("do x", role="You are a wizard.",
                         success="the CLI exits 0 on all inputs")
        self.assertIn("You are a wizard.", p)
        self.assertIn("exits 0", p)


class TestSkills(unittest.TestCase):
    def test_bug_task_matches_dev_loop(self):
        names = [e["name"] for e in match_skills("fix a bug and write a test")]
        self.assertIn("dev-loop", names)

    def test_forced_skill_included_even_if_unknown(self):
        names = [e["name"] for e in match_skills("anything", forced=["my-custom-skill"])]
        self.assertIn("my-custom-skill", names)


class TestRefine(unittest.TestCase):
    def test_score_in_range(self):
        score, _, _ = score_prompt(build_prompt("build a small app"))
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_offline_loop_returns_trail(self):
        prompt, trail = refine("build a small app", {"loop": True}, iterations=2)
        self.assertTrue(prompt.strip())
        self.assertGreaterEqual(len(trail), 1)
        self.assertIn("score", trail[0])


if __name__ == "__main__":
    unittest.main()
