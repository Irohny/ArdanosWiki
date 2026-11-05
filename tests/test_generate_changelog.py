import subprocess
import tempfile
import unittest
from pathlib import Path


GENERATOR = Path(__file__).resolve().parents[1] / "generate_changelog.sh"


class ChangelogGeneratorTests(unittest.TestCase):
    def _git(self, repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )

    def _commit(self, repo: Path, subject: str) -> None:
        (repo / "history.txt").write_text(subject, encoding="utf-8")
        self._git(repo, "add", "history.txt")
        self._git(repo, "commit", "-m", subject)

    def _initialize_repo(self, repo: Path) -> None:
        self._git(repo, "init", "-q")
        self._git(repo, "config", "user.name", "Changelog Test")
        self._git(repo, "config", "user.email", "changelog@example.test")

    def _generate(self, repo: Path) -> str:
        result = subprocess.run(
            ["bash", str(GENERATOR)],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def test_outputs_scoped_commits_to_stdout_without_writing_wiki_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self._initialize_repo(repo)
            self._commit(repo, "chore: initialize")
            self._commit(repo, "feat(parser): add parser")
            self._commit(repo, "fix(parser): repair parser")

            changelog = self._generate(repo)

            self.assertTrue(
                changelog.startswith(
                    "---\ntyp:\nstatus:\nkampagne:\nregion:\ntags: []\n"
                    "zeit_text:\nzeit_von_jahr:\nzeit_bis_jahr:\nerstellt:\n"
                    "---\n\n# Changelog 0.1.1\n"
                )
            )
            self.assertIn("* feat(parser) (", changelog)
            self.assertIn("* fix(parser) (", changelog)
            self.assertIn("* chore (", changelog)
            self.assertFalse((repo / "World" / "CHANGELOG.md").exists())

    def test_uses_tag_range_and_breaking_scope_for_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self._initialize_repo(repo)
            self._commit(repo, "feat: previous release")
            self._git(repo, "tag", "v2.4.5")
            self._commit(repo, "feat(api)!: change the api")

            changelog = self._generate(repo)

            self.assertIn("# Changelog 3.0.0\n", changelog)
            self.assertIn("* feat(api)! (", changelog)
            self.assertNotIn("previous release", changelog)


if __name__ == "__main__":
    unittest.main()