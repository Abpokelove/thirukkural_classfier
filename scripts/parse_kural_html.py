#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW_HTML_CANDIDATES = [
    ROOT / "data" / "raw" / "thirukkural.html",
    ROOT / "thirukkural.html",
]
RAW_HTML = next((path for path in RAW_HTML_CANDIDATES if path.exists()), RAW_HTML_CANDIDATES[0])
PROCESSED_DIR = ROOT / "data" / "processed"


def normalize_space(value: str) -> str:
    value = unescape(value or "")
    value = value.replace("\ufeff", "")
    value = value.replace("\xa0", " ")
    value = value.replace("\u200b", "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_kurals() -> list[dict]:
    html_text = RAW_HTML.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html_text, "html.parser")
    body = soup.body or soup
    lines = [normalize_space(line) for line in body.get_text("\n").splitlines() if normalize_space(line)]

    records: list[dict] = []
    chapter = "unknown"
    pending_line: str | None = None
    started = False

    for raw_line in lines:
        if not started:
            if "அகர முதல எழுத்தெல்லாம்" in raw_line:
                started = True
            else:
                continue
        if raw_line.startswith("This page was"):
            break
        if re.match(r"^\d+(?:\.\d+)+\s+.*", raw_line):
            title = re.sub(r"^\d+(?:\.\d+)+\s*", "", raw_line).strip()
            if title:
                chapter = title
            continue
        if not re.search(r"[\u0B80-\u0BFF]", raw_line):
            continue

        number_match = re.search(r"(\d+)\s*$", raw_line)
        if number_match:
            second_line = re.sub(r"\s*" + re.escape(number_match.group(1)) + r"\s*$", "", raw_line).strip()
            if pending_line and second_line:
                records.append({
                    "raw_number": int(number_match.group(1)),
                    "chapter": chapter,
                    "line1": pending_line,
                    "line2": second_line,
                    "text": f"{pending_line} {second_line}".strip(),
                })
                pending_line = None
            continue

        if pending_line is None:
            pending_line = raw_line
        elif len(raw_line) > len(pending_line):
            pending_line = raw_line

    if len(records) != 1330:
        raise ValueError(f"Expected 1330 couplets, parsed {len(records)} after recovery")

    for index, record in enumerate(records, start=1):
        record["kural_number"] = index
        record["chapter_number"] = str(((index - 1) // 10) + 1)
        record["chapter"] = record["chapter_number"]

    expected_numbers = list(range(1, 1331))
    found_numbers = [int(item["kural_number"]) for item in records]
    if found_numbers != expected_numbers:
        missing = sorted(set(expected_numbers) - set(found_numbers))[:10]
        extra = sorted(set(found_numbers) - set(expected_numbers))[:10]
        raise ValueError(f"Canonical numbering mismatch: missing={missing}, extra={extra}, total={len(records)}")
    return records


def write_processed_files(records: list[dict]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    json_path = PROCESSED_DIR / "thirukkural.json"
    csv_path = PROCESSED_DIR / "thirukkural.csv"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["kural_number", "chapter", "chapter_number", "line1", "line2", "text"])
        writer.writeheader()
        for item in records:
            writer.writerow({
                "kural_number": item["kural_number"],
                "chapter": item["chapter"],
                "chapter_number": item["chapter_number"],
                "line1": item["line1"],
                "line2": item["line2"],
                "text": item["text"],
            })

    checksum = hashlib.sha256(RAW_HTML.read_bytes()).hexdigest()
    metadata = {
        "source": "Project Madurai",
        "source_file": str(RAW_HTML.name),
        "corpus_size": len(records),
        "chapter_count": 133,
        "encoding": "UTF-8",
        "normalization": "NFC",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_checksum": checksum,
    }
    (ROOT / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    records = parse_kurals()
    write_processed_files(records)
    print(f"Parsed {len(records)} Kurals and wrote dataset to {PROCESSED_DIR}")
    print(f"Metadata written to {ROOT / 'metadata.json'}")
