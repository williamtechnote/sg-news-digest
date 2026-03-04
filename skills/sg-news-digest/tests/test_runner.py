from __future__ import annotations

from pipeline.runner import parse_args


def test_parse_args_default_top5() -> None:
    args = parse_args([])
    assert args.top == 5
