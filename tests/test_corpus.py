import json
import subprocess
import unicodedata
from pathlib import Path

from backend.app.services.verifier import browse_corpus, load_corpus, verify_quote

ROOT = Path(__file__).resolve().parents[1]


def test_parser_creates_corpus():
    result = subprocess.run(
        ["python", str(ROOT / "scripts" / "parse_kural_html.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr

    corpus_path = ROOT / "data" / "processed" / "thirukkural.json"
    assert corpus_path.exists(), "Corpus JSON should be created by the parser"

    with corpus_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    assert len(data) == 1330
    assert data[0]["kural_number"] == 1
    assert data[-1]["kural_number"] == 1330
    assert data[0]["text"].startswith("அகர முதல எழுத்தெல்லாம்")


def test_validation_script_reports_valid():
    result = subprocess.run(
        ["python", str(ROOT / "scripts" / "validate_corpus.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert "1330" in result.stdout


def test_corpus_browse_paginates_and_searches_tamil():
    first_page = browse_corpus(limit=2)
    last_page = browse_corpus(offset=1329, limit=20)
    search_result = browse_corpus(query="அகர முதல எழுத்தெல்லாம்", limit=5)
    assert first_page["total"] == 1330
    assert [item["kural_number"] for item in first_page["items"]] == [1, 2]
    assert last_page["items"][0]["kural_number"] == 1330
    assert search_result["items"][0]["kural_number"] == 1


def test_canonical_two_line_kural_from_processed_corpus():
    kural = load_corpus()[0]
    exact = verify_quote(f"{kural['line1']}\n{kural['line2']}")
    assert exact["text_status"] == "AUTHENTIC_EXACT"
    assert exact["content_status"] == "AUTHENTIC_EXACT"
    assert exact["normalization"]["L0_match"] is True
    assert exact["structure_status"] == "KURAL_STRUCTURE"
    assert exact["possible_originals"][0]["kural_number"] == 1
    assert exact["possible_originals"][0]["score"] == 1.0
    assert exact["signals"]["semantic_similarity"] is None


def test_extra_words_after_full_kural_are_not_kural_structure():
    kural = load_corpus()[0]
    result = verify_quote(f"{kural['line1']}\n{kural['line2']} கூடுதல்")

    assert result["text_status"] == "NOT_KURAL_STRUCTURE"
    assert result["content_status"] == "AUTHENTIC_PARTIAL"
    assert result["structure_status"] == "NOT_KURAL_STRUCTURE"
    assert result["extra_words"] == ["கூடுதல்"]
    assert result["evidence"]["matched_kural"] == 1


def test_extra_words_inserted_into_full_kural_are_not_kural_structure():
    kural = load_corpus()[0]
    line1 = kural["line1"].replace(" ஆதி", " கூடுதல் ஆதி")
    result = verify_quote(f"{line1}\n{kural['line2']}")

    assert result["text_status"] == "NOT_KURAL_STRUCTURE"
    assert result["structure_status"] == "NOT_KURAL_STRUCTURE"
    assert result["extra_words"] == ["கூடுதல்"]
    assert result["evidence"]["matched_kural"] == 1


def test_canonical_two_line_layout_and_final_punctuation_are_required():
    kural = load_corpus()[0]
    correct_layout = verify_quote(f"{kural['line1']}\n{kural['line2']}")
    flattened = verify_quote(kural["text"])
    missing_period = verify_quote(f"{kural['line1']}\n{kural['line2'].removesuffix('.')}")

    assert correct_layout["text_status"] == "AUTHENTIC_EXACT"
    assert correct_layout["structure_status"] == "KURAL_STRUCTURE"
    assert flattened["text_status"] == "NOT_KURAL_STRUCTURE"
    assert flattened["structure_status"] == "NOT_KURAL_STRUCTURE"
    assert missing_period["text_status"] == "NOT_KURAL_STRUCTURE"
    assert missing_period["structure_status"] == "NOT_KURAL_STRUCTURE"
    assert any("punctuation" in issue for issue in missing_period["structure_issues"])


def test_reordered_canonical_lines_are_not_kural_structure():
    kural = load_corpus()[0]
    result = verify_quote(f"{kural['line2']}\n{kural['line1']}")

    assert result["text_status"] == "NOT_KURAL_STRUCTURE"
    assert result["structure_status"] == "NOT_KURAL_STRUCTURE"
    assert result["extra_words"] == []
    assert result["evidence"]["matched_kural"] == 1


def test_formatting_whitespace_is_separated_from_exact_text():
    text = load_corpus()[0]["text"]
    formatting = verify_quote(text.replace(" ", "    ", 1).replace(" ", "\n", 1))
    assert formatting["text_status"] == "AUTHENTIC_FORMAT"
    assert formatting["normalization"]["L0_match"] is False
    assert formatting["normalization"]["L1_match"] is True


def test_word_joining_normalization():
    text = load_corpus()[0]["text"]
    joined = verify_quote("".join(text.split()))
    assert joined["text_status"] == "AUTHENTIC_JOINING"
    assert joined["normalization"]["L2_match"] is True


def test_zero_width_and_bom_unicode_formatting():
    text = load_corpus()[0]["text"]
    formatted = verify_quote("\ufeff" + text.replace(" ", "\u200b ", 1))
    assert formatted["text_status"] == "AUTHENTIC_FORMAT"


def test_small_character_change_is_modified():
    text = load_corpus()[0]["text"]
    typo = text[:-2] + text[-1:]
    modified = verify_quote(typo)
    assert modified["text_status"] in {"MODIFIED_MINIMAL", "MODIFIED"}


def test_partial_kural_uses_contiguous_corpus_span():
    first_line = load_corpus()[0]["line1"]
    partial = verify_quote(first_line)
    assert partial["text_status"] == "AUTHENTIC_PARTIAL"
    assert partial["evidence"]["matched_kural"] == 1


def test_blended_quote_requires_two_corpus_spans():
    corpus = load_corpus()
    first_span = " ".join(corpus[0]["text"].split()[:3])
    second_span = " ".join(corpus[10]["text"].split()[:3])
    result = verify_quote(f"{first_span} {second_span}")
    assert result["text_status"] == "BLENDED"
    assert {item["kural_number"] for item in result["evidence"]["blend_sources"]} == {1, 11}
    assert {item["kural_number"] for item in result["possible_originals"]} >= {1, 11}


def test_wrong_attribution_does_not_change_text_status():
    text = load_corpus()[0]["text"]
    wrong_attribution = verify_quote(text, claimed_kural_number=500)
    assert wrong_attribution["text_status"] == "AUTHENTIC_EXACT"
    assert wrong_attribution["attribution_status"] == "INCORRECT"


def test_unrelated_and_empty_quotations_are_not_authenticated():
    fabricated = verify_quote("இந்த குரல் காப்பியத்தில் இல்லை என்பது உறுதி.")
    assert fabricated["text_status"] in {"FABRICATED", "AMBIGUOUS"}
    empty = verify_quote("")
    assert empty["text_status"] in {"AMBIGUOUS", "FABRICATED"}


def test_out_of_range_claim_is_unsupported():
    result = verify_quote(load_corpus()[0]["text"], claimed_kural_number=1331)
    assert result["attribution_status"] == "UNSUPPORTED"
