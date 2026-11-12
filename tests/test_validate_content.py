"""Regression coverage for broken navigation, links, and public source layout."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-content.py"
SPEC = importlib.util.spec_from_file_location("validate_content", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ContentValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.docs = self.root / "docs"
        for path in validator.REQUIRED_PAGES:
            self.page(path)
        (self.root / "requirements.txt").write_text("zensical==0.1.1\n", encoding="utf-8")
        self.nav = list(validator.REQUIRED_PAGES)
        self.config()

    def page(self, path, body="Welcome to the help center.\n"):
        destination = self.docs / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            "---\ntitle: Help\ndescription: Find product help.\n---\n\n# Help\n\n" + body,
            encoding="utf-8",
        )

    def config(self, suffix=""):
        paths = ",\n".join(f'  {{ "Page {index}" = "{path}" }}' for index, path in enumerate(self.nav))
        features = ", ".join(f'"{feature}"' for feature in sorted(validator.REQUIRED_FEATURES))
        (self.root / "zensical.toml").write_text(
            '[project]\nsite_name = "IYBA Help Center"\n'
            'site_url = "https://help.iyba.org/"\n'
            'site_description = "Product documentation"\n'
            f"nav = [\n{paths}\n]\n[project.theme]\nlanguage = \"en\"\nfeatures = [{features}]\n" + suffix,
            encoding="utf-8",
        )

    def errors(self):
        return "\n".join(validator.validate(self.root))

    def test_valid_structure_and_supported_link_forms(self):
        asset = self.docs / "assets" / "logo.png"
        asset.parent.mkdir()
        asset.write_bytes(b"image fixture")
        self.page(
            "index.md",
            '[Support](support/index.md#help)\n'
            '[Contact][support]\n'
            '[support]: support/contact.md "Contact support"\n'
            '![Logo](assets/logo.png)\n'
            '<a href="/boatdox/">BoatDox</a><img src="assets/logo.png" alt="Brand">\n'
            '[Website](https://iyba.org/) [Email](mailto:example@example.org)\n'
            '[Section](#help)\n',
        )
        self.assertEqual(validator.validate(self.root), [])

    def test_missing_and_duplicate_navigation_are_rejected(self):
        self.nav.remove("iyba/index.md")
        self.nav.append("index.md")
        self.config()
        errors = self.errors()
        self.assertIn("missing from explicit navigation: iyba/index.md", errors)
        self.assertIn("appears 2 times in navigation: index.md", errors)

    def test_deleted_navigation_destination_is_rejected(self):
        self.nav.append("iyba/missing.md")
        self.config()
        self.assertIn("Navigation page does not exist: iyba/missing.md", self.errors())

    def test_navigation_cannot_escape_docs(self):
        (self.root / "private.md").write_text("Private", encoding="utf-8")
        self.nav.append("../private.md")
        self.config()
        self.assertIn("Invalid navigation path: ../private.md", self.errors())

    def test_broken_markdown_reference_and_html_targets_are_rejected(self):
        self.page("index.md", '[Missing](missing.md)\n![Missing image][image]\n[image]: absent.png\n<img src="lost.svg">\n')
        errors = self.errors()
        for target in ("missing.md", "absent.png", "lost.svg"):
            self.assertIn(f"missing internal target '{target}'", errors)

    def test_undefined_explicit_reference_is_rejected(self):
        self.page("index.md", "[Support][missing]\n")
        self.assertIn("undefined link reference [missing]", self.errors())

    def test_encoded_traversal_cannot_link_private_repository_files(self):
        (self.root / "private.md").write_text("Private", encoding="utf-8")
        self.page("index.md", "[Private](%2e%2e/private.md)\n")
        self.assertIn("link escapes the docs directory", self.errors())

    def test_symlinked_asset_cannot_escape_docs(self):
        target = self.root / "private.png"
        target.write_bytes(b"private fixture")
        (self.docs / "logo.png").symlink_to(target)
        self.page("index.md", "![Logo](logo.png)\n")
        self.assertIn("link escapes the docs directory", self.errors())

    def test_code_examples_are_not_validated_as_links_or_headings(self):
        self.page("index.md", '```markdown\n# Example\n[Missing](missing.md)\n```\n\n`[Missing](missing.md)`\n')
        self.assertEqual(validator.validate(self.root), [])

    def test_paths_require_lowercase_kebab_case(self):
        self.page("iyba/Getting_Started.md")
        self.nav.append("iyba/Getting_Started.md")
        self.config()
        self.assertIn("Use lowercase kebab-case", self.errors())

    def test_required_metadata_and_single_heading(self):
        (self.docs / "index.md").write_text('---\ntitle: ""\n---\n# One\n# Two\n', encoding="utf-8")
        errors = self.errors()
        self.assertIn("title must be a nonempty", errors)
        self.assertIn("description must be a nonempty", errors)
        self.assertIn("exactly one level-one", errors)

    def test_search_and_version_pin_are_required(self):
        self.config("\n[project.plugins.search]\nenabled = false\n")
        (self.root / "requirements.txt").write_text("zensical>=0.1.1\n", encoding="utf-8")
        errors = self.errors()
        self.assertIn("search must remain enabled", errors)
        self.assertIn("pin one exact Zensical release", errors)


if __name__ == "__main__":
    unittest.main()
