from __future__ import annotations

from pathlib import Path


def test_skill_layout_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "SKILL.md").exists()
    assert (root / "scripts" / "run.sh").exists()


def test_skill_doc_mentions_openclaw_boundary() -> None:
    root = Path(__file__).resolve().parents[1]
    content = (root / "SKILL.md").read_text(encoding="utf-8")
    assert "cron" in content.lower()
    assert "stdout" in content.lower()
