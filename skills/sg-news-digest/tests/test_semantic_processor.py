from __future__ import annotations

from pathlib import Path

import pipeline.semantic_processor as semantic_processor
from pipeline.semantic_processor import build_prompt


def test_prompt_mentions_top5_and_chinese_output() -> None:
    prompt = build_prompt([{"title": "A", "source": "cna"}], top_n=5, report_date="2026-03-04")
    assert "Top 5" in prompt
    assert "中文" in prompt


def test_invoke_codex_uses_stdin_for_prompt(tmp_path, monkeypatch) -> None:
    schema = tmp_path / "schema.json"
    schema.write_text("{}", encoding="utf-8")
    captured: dict = {}

    def fake_run(cmd, check, capture_output, text, timeout, input):  # noqa: A002
        captured["cmd"] = cmd
        captured["input"] = input

        output_path = Path(cmd[cmd.index("-o") + 1])
        output_path.write_text('{"clusters": []}', encoding="utf-8")

        class Result:
            stdout = ""

        return Result()

    monkeypatch.setattr(semantic_processor.subprocess, "run", fake_run)

    semantic_processor._invoke_codex(  # noqa: SLF001
        payload=[{"title": "A", "source": "cna"}],
        top_n=5,
        report_date="2026-03-04",
        schema_path=schema,
        timeout_sec=30,
        model="",
    )

    assert captured["cmd"][-1] == "-"
    assert "Top 5" in captured["input"]
