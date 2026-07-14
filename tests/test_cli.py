"""CLI smoke tests — exercise each subcommand through main()."""
import contextlib
import io
import unittest

from fablegen.cli import main, _to_profile


def _run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = main(argv)
    return code, buf.getvalue()


class TestCli(unittest.TestCase):
    def test_new_with_model_flag(self):
        code, out = _run(["new", "build a thing", "--model", "opus"])
        self.assertEqual(code, 0)
        self.assertIn("Claude Opus 4.8", out)

    def test_profiles_and_skills_and_detect(self):
        for cmd in (["profiles"], ["skills"], ["detect"]):
            code, out = _run(cmd)
            self.assertEqual(code, 0, cmd)
            self.assertTrue(out.strip())

    def test_diff_shows_differences(self):
        code, out = _run(["diff", "opus-4.8", "gpt-5.6", "draft launch copy"])
        self.assertEqual(code, 0)
        # unified diff markers + the differing discovery headers
        self.assertIn("---", out)
        self.assertIn("bias to action", out)  # gpt-5.6-only discovery line (assume-and-proceed)

    def test_diff_unknown_model_errors(self):
        code, _ = _run(["diff", "opus-4.8", "wibble-x9000", "x"])
        self.assertEqual(code, 2)

    def test_to_profile_maps_model_ids(self):
        self.assertEqual(_to_profile("claude-opus-4-8"), "opus-4.8")
        self.assertEqual(_to_profile("sonnet-5"), "sonnet-5")
        with self.assertRaises(ValueError):
            _to_profile("nope")


if __name__ == "__main__":
    unittest.main()
