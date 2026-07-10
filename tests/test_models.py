"""Auto model-detection + profile resolution."""
import json
import os
import tempfile
import unittest

from fablegen.models import (normalize_model, model_to_profile,
                             detect_model, resolve_profile)
from fablegen import config


class TestMapping(unittest.TestCase):
    def test_normalize_strips_suffix(self):
        self.assertEqual(normalize_model("claude-fable-5[1m]"), "claude-fable-5")

    def test_known_aliases(self):
        self.assertEqual(model_to_profile("claude-opus-4-8"), "opus-4.8")
        self.assertEqual(model_to_profile("gpt-5.5"), "gpt-5.5-instant")
        self.assertEqual(model_to_profile("sonnet"), "sonnet-5")
        self.assertEqual(model_to_profile("claude-fable-5[1m]"), "fable-5")

    def test_unknown_model_returns_none(self):
        self.assertIsNone(model_to_profile("llama-9000"))


class TestDetect(unittest.TestCase):
    def test_env_wins(self):
        m, src = detect_model(env={"ANTHROPIC_MODEL": "claude-sonnet-5"})
        self.assertEqual(m, "claude-sonnet-5")
        self.assertIn("ANTHROPIC_MODEL", src)

    def test_settings_file_fallback(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"model": "claude-opus-4-8[1m]"}, f)
            path = f.name
        try:
            m, src = detect_model(env={}, settings_path=path)
            self.assertEqual(m, "claude-opus-4-8[1m]")
            self.assertIn("settings.json", src)
        finally:
            os.unlink(path)


class TestResolve(unittest.TestCase):
    def test_explicit_profile_wins(self):
        prof, reason = resolve_profile(explicit_profile="opus-4.8", config={})
        self.assertEqual(prof, "opus-4.8")
        self.assertIn("explicit", reason)

    def test_model_auto_detects_from_env(self):
        prof, reason = resolve_profile(model="auto",
                                       env={"ANTHROPIC_MODEL": "gpt-5.5"}, config={})
        self.assertEqual(prof, "gpt-5.5-instant")
        self.assertIn("auto", reason)

    def test_model_flag_maps(self):
        prof, _ = resolve_profile(model="opus", config={})
        self.assertEqual(prof, "opus-4.8")

    def test_unknown_model_raises(self):
        with self.assertRaises(ValueError):
            resolve_profile(model="llama-9000", config={})

    def test_falls_back_to_settings_then_default(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"model": "claude-fable-5[1m]"}, f)
            path = f.name
        try:
            prof, reason = resolve_profile(env={}, config={}, settings_path=path)
            self.assertEqual(prof, "fable-5")
        finally:
            os.unlink(path)

    def test_default_when_nothing_known(self):
        prof, reason = resolve_profile(env={}, config={}, settings_path="/nope/x.json")
        self.assertEqual(prof, "fable-5")
        self.assertEqual(reason, "default")


class TestConfig(unittest.TestCase):
    def test_set_read_clear_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, ".fablegen.json")
            config.set_active("sonnet-5", path=path)
            self.assertEqual(config.read_active(path=path).get("profile"), "sonnet-5")
            config.clear_active(path=path)
            self.assertEqual(config.read_active(path=path), {})


if __name__ == "__main__":
    unittest.main()
