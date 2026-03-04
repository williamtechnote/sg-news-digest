from __future__ import annotations

from pipeline.rss_client import parse_feed


def test_parse_feed_extracts_entries() -> None:
    xml = """<?xml version=\"1.0\"?><rss><channel><item><title>A</title><link>https://a</link><description>desc</description></item></channel></rss>"""
    entries = parse_feed(xml)
    assert len(entries) == 1
    assert entries[0]["title"] == "A"
    assert entries[0]["link"] == "https://a"
