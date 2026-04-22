from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from trusted_search.web_ingest import parse_html


ROOT = Path(__file__).resolve().parents[1]


class TrustedSearchTests(unittest.TestCase):
    def test_parse_html_extracts_title_text_and_links(self) -> None:
        html = """
        <html>
          <head><title>Oracle RMAN Notes</title></head>
          <body>
            <main>
              <h1>RMAN Best Practices</h1>
              <p>Use real-time redo with Recovery Appliance.</p>
              <a href="https://docs.oracle.com/example">docs</a>
            </main>
          </body>
        </html>
        """
        title, text, links = parse_html(html)
        self.assertIn("Oracle RMAN Notes", title)
        self.assertIn("RMAN Best Practices", text)
        self.assertIn("real-time redo", text)
        self.assertIn("https://docs.oracle.com/example", links)

    def test_build_and_search(self) -> None:
        tmp_path = Path(self._testMethodName)
        index_dir = ROOT / "build" / tmp_path
        source_dir = ROOT / "sample_sources"
        if index_dir.exists():
            for path in sorted(index_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                else:
                    path.rmdir()

        build = subprocess.run(
            [
                sys.executable,
                "-m",
                "trusted_search",
                "build",
                "--source-dir",
                str(source_dir),
                "--index-dir",
                str(index_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        stats = json.loads(build.stdout)
        self.assertGreaterEqual(stats["documents"], 4)
        self.assertGreaterEqual(stats["chunks"], 4)

        search = subprocess.run(
            [
                sys.executable,
                "-m",
                "trusted_search",
                "search",
                "dual approval",
                "--index-dir",
                str(index_dir),
                "--top-k",
                "3",
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        results = json.loads(search.stdout)
        self.assertTrue(results)
        self.assertIn("citation", results[0])
        self.assertIn("confidence", results[0])
        self.assertGreater(results[0]["score"], 0)
        self.assertIn("approval", results[0]["text"].lower())

        acl_filtered = subprocess.run(
            [
                sys.executable,
                "-m",
                "trusted_search",
                "search",
                "revenue",
                "--index-dir",
                str(index_dir),
                "--acl-group",
                "finance",
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        filtered_results = json.loads(acl_filtered.stdout)
        self.assertTrue(filtered_results)
        self.assertIn("finance", filtered_results[0]["acl_groups"])

    def test_answer_returns_citations(self) -> None:
        tmp_path = Path(self._testMethodName)
        index_dir = ROOT / "build" / tmp_path
        source_dir = ROOT / "sample_sources"
        if index_dir.exists():
            for path in sorted(index_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                else:
                    path.rmdir()

        subprocess.run(
            [
                sys.executable,
                "-m",
                "trusted_search",
                "build",
                "--source-dir",
                str(source_dir),
                "--index-dir",
                str(index_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

        answer = subprocess.run(
            [
                sys.executable,
                "-m",
                "trusted_search",
                "answer",
                "why use hybrid retrieval",
                "--index-dir",
                str(index_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        payload = json.loads(answer.stdout)
        self.assertTrue(payload["citations"])
        self.assertIn("answer", payload)

    def test_build_from_json_web_document(self) -> None:
        source_dir = ROOT / "build" / "oracle_json_source"
        index_dir = ROOT / "build" / "oracle_json_index"
        source_dir.mkdir(parents=True, exist_ok=True)
        document = {
            "title": "Oracle ZDLRA Public Doc",
            "text": "Recovery Appliance integrates with RMAN and supports incremental forever backups.",
            "source_uri": "https://docs.oracle.com/example/zdlra",
            "acl_groups": ["oracle", "dba"],
        }
        (source_dir / "doc.json").write_text(json.dumps(document), encoding="utf-8")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "trusted_search",
                "build",
                "--source-dir",
                str(source_dir),
                "--index-dir",
                str(index_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

        search = subprocess.run(
            [
                sys.executable,
                "-m",
                "trusted_search",
                "search",
                "incremental forever backups",
                "--index-dir",
                str(index_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        results = json.loads(search.stdout)
        self.assertTrue(results)
        self.assertTrue(results[0]["citation"].startswith("https://docs.oracle.com/example/zdlra"))


if __name__ == "__main__":
    unittest.main()
