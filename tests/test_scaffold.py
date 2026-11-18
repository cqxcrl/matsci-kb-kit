import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SC = ROOT / "scaffold"


class TestScaffold(unittest.TestCase):
    def test_dirs_cover_required(self):
        dirs = {ln.strip() for ln in (SC / "dirs.txt").read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")}
        for need in ("wiki/sources", "wiki/concepts", "wiki/entities", "raw/pdf",
                     "raw/notes/lit-watch/state", "projects", "_archive", "_scratch"):
            self.assertIn(need, dirs)

    def test_meta_files_exist(self):
        for f in ("index.md", "tags.md", "log_ops.md", "log_insights.md"):
            self.assertTrue((SC / "meta" / f).is_file())

    def test_templates_have_no_real_email(self):
        for f in ("profile.template.md", "lit_config.template.yaml"):
            text = (SC / f).read_text(encoding="utf-8")
            for m in re.finditer(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
                self.assertTrue(m.group(0).endswith("example.org"), m.group(0))

    def test_obsidian_layer_isolated(self):
        self.assertTrue((SC / "obsidian" / "app.json").is_file())
        self.assertTrue((SC / "bases").is_dir())

    def test_index_sources_anchor(self):
        # lit_finish.insert_rows 的落点契约：Sources 标题 + 四列表头，勿改列数或删标题
        text = (SC / "meta" / "index.md").read_text(encoding="utf-8")
        self.assertIn("## 来源 Sources", text)
        self.assertIn("| 页面 | 摘要 | 入站链接数 | 最近更新 |", text)

    def test_gitignore_tracks_archive_register(self):
        text = (SC / "gitignore.template").read_text(encoding="utf-8")
        self.assertIn("!_archive/README.md", text)

    def test_archive_readme_template(self):
        """Task 6 遗留项 G：空登记册骨架（表头 日期/对象/原因/落点，无真实数据）。"""
        t = (SC / "archive-README.template.md").read_text(encoding="utf-8")
        self.assertIn("| 日期 | 对象 | 原因 | 落点 |", t)


if __name__ == "__main__":
    unittest.main()
