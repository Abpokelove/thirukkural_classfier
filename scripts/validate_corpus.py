#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data" / "processed" / "thirukkural.json"


def validate() -> None:
    if not CORPUS_PATH.exists():
        raise FileNotFoundError(f"Corpus file not found: {CORPUS_PATH}")

    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    if len(corpus) != 1330:
        raise ValueError(f"Expected 1330 records, found {len(corpus)}")

    numbers = [item["kural_number"] for item in corpus]
    if sorted(numbers) != list(range(1, 1331)):
        missing = sorted(set(range(1, 1331)) - set(numbers))
        raise ValueError(f"Missing or duplicate Kural numbers: first missing={missing[:10]}")

    expected_chapters = list(range(1, 134))
    chapter_counts = Counter(str(item["chapter"]) for item in corpus)
    observed = sorted(int(chapter) for chapter in chapter_counts)
    if observed != expected_chapters:
        raise ValueError(f"Expected chapter labels 1..133, found {observed[:10]} ...")
    if any(count != 10 for count in chapter_counts.values()):
        bad = {chapter: count for chapter, count in chapter_counts.items() if count != 10}
        raise ValueError(f"Chapters do not all have exactly 10 Kurals: {bad}")

    normalized_couplets = [
        unicodedata.normalize("NFC", re.sub(r"\s+", " ", item["text"]).strip())
        for item in corpus
    ]
    duplicate_couplets = [text for text, count in Counter(normalized_couplets).items() if count > 1]
    if duplicate_couplets:
        raise ValueError(f"Duplicate couplets found: {len(duplicate_couplets)}")

    for item in corpus:
        chapter_number = str(item.get("chapter_number", item.get("chapter")))
        if int(chapter_number) not in expected_chapters:
            raise ValueError(f"Invalid chapter number for Kural {item['kural_number']}: {chapter_number}")

    for item in corpus:
        if not item["text"] or not item["line1"] or not item["line2"]:
            raise ValueError(f"Empty text in Kural {item['kural_number']}")
        if not unicodedata.is_normalized("NFC", item["text"]):
            raise ValueError(f"Text is not Unicode NFC in Kural {item['kural_number']}")
        if not any("\u0b80" <= char <= "\u0bff" for char in item["text"]):
            raise ValueError(f"Tamil text is missing in Kural {item['kural_number']}")
        if "<" in item["text"] or ">" in item["text"]:
            raise ValueError(f"HTML tags remain in Kural {item['kural_number']}")
        if item["kural_number"] in {0, None}:
            raise ValueError(f"Invalid Kural number in corpus: {item}")

    print("✓ 1330 Kurals detected")
    print("✓ Kural numbers 1–1330")
    print("✓ 133 chapters")
    print("✓ 10 Kurals per chapter")
    print("✓ UTF-8 valid")
    print("✓ Unicode normalization checked")
    print("✓ Unique Kural numbers and couplets")
    print("✓ Missing records: 0")


if __name__ == "__main__":
    try:
        validate()
    except Exception as exc:  # pragma: no cover
        print(f"Validation failed: {exc}")
        raise SystemExit(1)
