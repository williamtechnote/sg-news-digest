from __future__ import annotations

from pipeline.normalize import is_same_sg_day


def test_is_same_sg_day_accepts_item_on_target_day() -> None:
    assert is_same_sg_day("2026-03-03T18:00:00+00:00", "2026-03-04")


def test_is_same_sg_day_rejects_item_outside_target_day() -> None:
    assert not is_same_sg_day("2026-03-04T16:01:00+00:00", "2026-03-04")
