import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestManifests(unittest.TestCase):
    def _load(self, rel):
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def test_both_manifests_parse(self):
        for rel in (".claude-plugin/plugin.json", ".qoder-plugin/plugin.json"):
            data = self._load(rel)
            self.assertEqual(data["name"], "matsci-knowledge-base")
            self.assertEqual(data["version"], "0.4.0")

    def test_qoder_display_name_and_skills(self):
        data = self._load(".qoder-plugin/plugin.json")
        self.assertEqual(data["displayName"], "Matsci Knowledge Base")
        self.assertEqual(data["skills"], "./skills/")

    def test_anonymous_author(self):
        for rel in (".claude-plugin/plugin.json", ".qoder-plugin/plugin.json",
                    "package.json"):
            data = self._load(rel)
            author = data["author"]
            name = author["name"] if isinstance(author, dict) else author
            self.assertEqual(name, "Matsci Knowledge Base contributors")
            self.assertNotIn("@", json.dumps(data))

    def test_package_files_whitelist_excludes_private(self):
        files = self._load("package.json")["files"]
        self.assertFalse(any(e == "build" or e.startswith("build/") for e in files))
        self.assertFalse(any("superpowers" in e for e in files))


if __name__ == "__main__":
    unittest.main()
