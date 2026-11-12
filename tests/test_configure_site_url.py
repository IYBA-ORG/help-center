import importlib.util
from pathlib import Path
import tomllib
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/configure-site-url.py"
SPEC = importlib.util.spec_from_file_location("configure_site_url", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class PagesURLTests(unittest.TestCase):
    CONFIG = '[project]\nsite_url = "https://old.example/"\nnav = ["index.md"]\n[project.theme]\nlanguage = "en"\n'

    def test_project_subpath_and_custom_domain_preserve_navigation(self):
        for url in ("https://iyba-org.github.io/help-center", "https://help.iyba.org/"):
            with self.subTest(url=url):
                updated = tomllib.loads(module.configure(self.CONFIG, url))
                self.assertEqual(updated["project"]["site_url"], url.rstrip("/") + "/")
                self.assertEqual(updated["project"]["nav"], ["index.md"])
                self.assertEqual(updated["project"]["theme"], {"language": "en"})

    def test_bad_or_secret_bearing_urls_are_rejected(self):
        for url in ("", "/help-center", "http://example.com", "https://user:secret@example.com", "https://example.com/?key=secret", "https://example.com/#fragment", "https://example.com/\ninjected"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                module.configure(self.CONFIG, url)

    def test_missing_or_wrong_scope_does_not_silently_change_config(self):
        for config in ('[project]\nsite_name = "Help"\n', '[project]\nsite_name = "Help"\n[unrelated]\nsite_url = "https://old.example/"\n'):
            with self.subTest(config=config), self.assertRaises(ValueError):
                module.configure(config, "https://example.com")


if __name__ == "__main__":
    unittest.main()
