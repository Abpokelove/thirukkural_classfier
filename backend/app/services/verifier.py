from __future__ import annotations

import json
import math
import re
import subprocess
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CORPUS_PATH = ROOT / "data" / "processed" / "thirukkural.json"

TEXT_STATUS_LABELS = {
    "AUTHENTIC_EXACT": "Authentic Quotation",
    "AUTHENTIC_FORMAT": "Authentic — Formatting Difference",
    "AUTHENTIC_JOINING": "Authentic — Word Joining Difference",
    "AUTHENTIC_VARIANT": "Authentic Variant",
    "AUTHENTIC_PARTIAL": "Authentic Partial Quotation",
    "NOT_KURAL_STRUCTURE": "Not a Kural Structure",
    "MODIFIED_MINIMAL": "Modified Quotation",
    "MODIFIED": "Modified Quotation",
    "BLENDED": "Blended From Multiple Kurals",
    "PARAPHRASED": "Paraphrase",
    "FABRICATED": "No Canonical Match Found",
    "AMBIGUOUS": "Needs Review",
}


def normalize_text(value: str | None, level: str = "L0") -> str:
    text = value or ""
    if level == "L0":
        return text
    text = text.replace("\ufeff", "").replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    text = text.replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    text = text.replace("–", "-").replace("—", "-")
    text = unicodedata.normalize("NFC", text)
    if level in {"L1", "L2"}:
        text = re.sub(r"\s+", " ", text).strip()
    if level == "L2":
        text = re.sub(r"\s+", "", text)
    return text.strip()


def _tokenize_tamil(text: str) -> list[str]:
    return re.findall(r"[\u0B80-\u0BFF]+", text)


def _extra_words_outside_canonical_kural(query: str, corpus: list[dict]) -> list[str]:
    query_words = re.findall(r"[\u0B80-\u0BFF]+|[A-Za-z0-9]+", query)
    for item in corpus:
        canonical_words = _tokenize_tamil(normalize_text(item.get("text", ""), "L1"))
        if not canonical_words or len(query_words) <= len(canonical_words):
            continue

        matched_indices: list[int] = []
        query_index = 0
        for word in canonical_words:
            while query_index < len(query_words) and query_words[query_index] != word:
                query_index += 1
            if query_index == len(query_words):
                break
            matched_indices.append(query_index)
            query_index += 1
        else:
            matched_index_set = set(matched_indices)
            return [
                word for index, word in enumerate(query_words)
                if index not in matched_index_set
            ]
    return []


def _blend_evidence(query: str, corpus: list[dict]) -> list[dict]:
    query_tokens = _tokenize_tamil(query)
    if len(query_tokens) < 6:
        return []

    matches: list[dict] = []
    for item in corpus:
        candidate_tokens = _tokenize_tamil(normalize_text(item.get("text", ""), "L1"))
        longest: tuple[int, int, int] | None = None
        for query_start in range(len(query_tokens)):
            for candidate_start in range(len(candidate_tokens)):
                length = 0
                while (
                    query_start + length < len(query_tokens)
                    and candidate_start + length < len(candidate_tokens)
                    and query_tokens[query_start + length] == candidate_tokens[candidate_start + length]
                ):
                    length += 1
                if longest is None or length > longest[0]:
                    longest = (length, query_start, query_start + length)
        if longest and longest[0] >= 3:
            matches.append({"item": item, "length": longest[0], "start": longest[1], "end": longest[2]})

    matches.sort(key=lambda match: match["length"], reverse=True)
    for first_index, first in enumerate(matches):
        for second in matches[first_index + 1:]:
            if first["item"]["kural_number"] == second["item"]["kural_number"]:
                continue
            if first["start"] < second["end"] and second["start"] < first["end"]:
                continue
            coverage = (first["length"] + second["length"]) / len(query_tokens)
            if coverage >= 0.6:
                return [first, second]
    return []


def _sequence_similarity(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def _graphemes(text: str) -> list[str]:
    clusters: list[str] = []
    for char in text:
        if clusters and unicodedata.category(char).startswith("M"):
            clusters[-1] += char
        else:
            clusters.append(char)
    return clusters


@lru_cache(maxsize=8192)
def _edit_distance(left: str, right: str) -> int:
    left_clusters = _graphemes(left)
    right_clusters = _graphemes(right)
    if left_clusters == right_clusters:
        return 0
    if not left_clusters:
        return len(right_clusters)
    if not right_clusters:
        return len(left_clusters)
    previous = list(range(len(right_clusters) + 1))
    for i, char_left in enumerate(left_clusters, start=1):
        current = [i]
        for j, char_right in enumerate(right_clusters, start=1):
            insertion = current[j - 1] + 1
            deletion = previous[j] + 1
            substitution = previous[j - 1] + (char_left != char_right)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


def _character_similarity(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    edit_distance = _edit_distance(left, right)
    max_length = max(len(_graphemes(left)), len(_graphemes(right)))
    return 1.0 - (edit_distance / max_length) if max_length else 0.0


def _tfidf_cosine_similarity(query: str, candidate: str) -> float:
    query_tokens = _tokenize_tamil(query)
    candidate_tokens = _tokenize_tamil(candidate)
    if not query_tokens and not candidate_tokens:
        return 1.0
    if not query_tokens or not candidate_tokens:
        return 0.0
    q_counter = Counter(query_tokens)
    c_counter = Counter(candidate_tokens)
    vocab = set(q_counter) | set(c_counter)
    if not vocab:
        return 0.0
    idf = {token: math.log((2.0) / (1.0 + (1 if token in c_counter else 0))) + 1.0 for token in vocab}
    q_vec = {token: q_counter.get(token, 0) * idf[token] for token in vocab}
    c_vec = {token: c_counter.get(token, 0) * idf[token] for token in vocab}
    numerator = sum(q_vec.get(token, 0) * c_vec.get(token, 0) for token in vocab)
    q_norm = math.sqrt(sum(value * value for value in q_vec.values()))
    c_norm = math.sqrt(sum(value * value for value in c_vec.values()))
    if q_norm == 0 or c_norm == 0:
        return 0.0
    return numerator / (q_norm * c_norm)


@lru_cache(maxsize=1)
def _load_semantic_model() -> Any | None:
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    except Exception:
        return None


def _semantic_similarity(query: str, candidate: str) -> float | None:
    model = _load_semantic_model()
    if model is None:
        return None
    try:
        embeddings = model.encode([query, candidate], convert_to_tensor=False)
        numerator = sum(a * b for a, b in zip(embeddings[0], embeddings[1]))
        denom = math.sqrt(sum(a * a for a in embeddings[0])) * math.sqrt(sum(b * b for b in embeddings[1]))
        return 0.0 if denom == 0 else numerator / denom
    except Exception:
        return None


def _fused_similarity(character: float, lexical: float, semantic: float | None) -> float:
    weighted_score = (character * 0.45) + (lexical * 0.35)
    available_weight = 0.80
    if semantic is not None:
        weighted_score += semantic * 0.20
        available_weight += 0.20
    return weighted_score / available_weight


def load_corpus() -> list[dict]:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def search_corpus(query: str | None, limit: int = 10) -> list[dict]:
    text = (query or "").strip()
    if not text:
        return []
    corpus = load_corpus()
    normalized = normalize_text(text, "L1")
    results: list[dict] = []
    for item in corpus:
        haystack = normalize_text(item.get("text", "") + " " + item.get("chapter", "") + " " + str(item.get("kural_number", "")), "L1")
        score = 0.0
        if normalized in haystack or haystack in normalized:
            score = 1.0
        else:
            score = _sequence_similarity(normalized, haystack)
        if score > 0.1:
            results.append({
                "kural_number": item.get("kural_number"),
                "chapter": item.get("chapter"),
                "line1": item.get("line1"),
                "line2": item.get("line2"),
                "text": item.get("text"),
                "score": round(score, 4),
            })
    return sorted(results, key=lambda row: row["score"], reverse=True)[:limit]


def browse_corpus(query: str | None = None, chapter: str | None = None, offset: int = 0, limit: int = 20) -> dict:
    normalized_query = normalize_text(query, "L1").casefold()
    normalized_chapter = (chapter or "").strip()
    matches = []
    for item in load_corpus():
        if normalized_chapter and str(item.get("chapter_number", item.get("chapter"))) != normalized_chapter:
            continue
        if normalized_query:
            searchable = normalize_text(
                f"{item.get('kural_number', '')} {item.get('chapter', '')} {item.get('text', '')}",
                "L1",
            ).casefold()
            if normalized_query not in searchable:
                continue
        matches.append(item)
    safe_offset = max(0, offset)
    safe_limit = min(max(1, limit), 100)
    return {
        "items": matches[safe_offset:safe_offset + safe_limit],
        "total": len(matches),
        "offset": safe_offset,
        "limit": safe_limit,
    }


def _matching_reason(score: float, lexical_similarity: float, semantic_similarity: float | None) -> str:
    if score >= 0.92:
        return "Very strong lexical and text overlap"
    if lexical_similarity >= 0.7:
        return "Strong lexical overlap"
    if semantic_similarity is not None and semantic_similarity >= 0.8:
        return "Semantic alignment with a nearby canonical verse"
    return "Moderate similarity to a candidate Kural"


def _candidate_for_entry(item: dict, query: str, score: float, lexical_similarity: float, semantic_similarity: float | None) -> dict:
    chapter = item.get("chapter") or item.get("chapter_number") or "unknown"
    return {
        "kural_number": item.get("kural_number"),
        "chapter": chapter,
        "text": item.get("text"),
        "score": round(score, 4),
        "matching_reason": _matching_reason(score, lexical_similarity, semantic_similarity),
        "chapter_number": item.get("chapter_number"),
    }


def _ground_truth_for_number(kural_number: int | str | None) -> dict | None:
    if not kural_number:
        return None
    try:
        target = int(kural_number)
    except (TypeError, ValueError):
        return None
    corpus = load_corpus()
    for item in corpus:
        if int(item.get("kural_number")) == target:
            return item
    return None


def verify_quote(quote: str | None, claimed_kural_number: int | str | None = None) -> dict:
    raw_text = quote or ""
    normalized_input = normalize_text(raw_text, "L1")
    if not normalized_input.strip():
        return {
            "text_status": "AMBIGUOUS",
            "human_label": "Needs Review",
            "presentation_status": "NOT_CLEAR",
            "attribution_status": "NOT_PROVIDED" if claimed_kural_number is None else "UNSUPPORTED",
            "normalization": {
                "L0_match": False,
                "L1_match": False,
                "L2_match": False,
                "L0": "",
                "L1": "",
                "L2": "",
            },
            "signals": {
                "character_similarity": 0.0,
                "edit_distance": 0,
                "lexical_similarity": 0.0,
                "semantic_similarity": None,
            },
            "possible_originals": [],
            "evidence": {
                "matched_kural": None,
                "coverage": 0.0,
                "contiguous": False,
                "candidate_rank": None,
                "claim_supported": False,
            },
            "why": ["The quotation field was empty, so no evidence-based match could be made."],
            "claimed_kural_number": claimed_kural_number,
            "best_candidate": None,
            "technical_label": "AMBIGUOUS",
            "content_status": "AMBIGUOUS",
            "structure_status": "NOT_ASSESSED",
            "extra_words": [],
        }

    corpus = load_corpus()
    l0 = normalize_text(raw_text, "L0")
    l1 = normalize_text(raw_text, "L1")
    l2 = normalize_text(raw_text, "L2")
    l0_matches = []
    l1_matches = []
    l2_matches = []
    for item in corpus:
        item_l0 = normalize_text(item.get("text", ""), "L0")
        item_l1 = normalize_text(item.get("text", ""), "L1")
        item_l2 = normalize_text(item.get("text", ""), "L2")
        if item_l0 == l0:
            l0_matches.append(item)
        if item_l1 == l1:
            l1_matches.append(item)
        if item_l2 == l2:
            l2_matches.append(item)
    blend_matches = _blend_evidence(l1, corpus) if not (l0_matches or l1_matches or l2_matches) else []

    best_match: dict | None = None
    if l0_matches:
        best_match = l0_matches[0]
        text_status = "AUTHENTIC_EXACT"
    elif l1_matches:
        best_match = l1_matches[0]
        text_status = "AUTHENTIC_FORMAT"
    elif l2_matches:
        best_match = l2_matches[0]
        text_status = "AUTHENTIC_JOINING"
    else:
        candidate_scores: list[dict] = []
        for item in corpus:
            candidate_text = normalize_text(item.get("text", ""), "L1")
            if not candidate_text:
                continue
            char_similarity = _character_similarity(l1, candidate_text)
            lexical_similarity = max(_tfidf_cosine_similarity(l1, candidate_text), _sequence_similarity(l1, candidate_text))
            semantic_similarity = _semantic_similarity(l1, candidate_text)
            score = _fused_similarity(char_similarity, lexical_similarity, semantic_similarity)
            candidate_scores.append({
                "item": item,
                "score": score,
                "character_similarity": char_similarity,
                "lexical_similarity": lexical_similarity,
                "semantic_similarity": semantic_similarity,
                "edit_distance": _edit_distance(l1, candidate_text),
            })
        ranked = sorted(candidate_scores, key=lambda item: item["score"], reverse=True)
        best_candidate = ranked[0] if ranked else None
        best_match = best_candidate["item"] if best_candidate else None
        if best_candidate is not None:
            score = best_candidate["score"]
            char_similarity = best_candidate["character_similarity"]
            lexical_similarity = best_candidate["lexical_similarity"]
            semantic_similarity = best_candidate["semantic_similarity"]
            if l1 in normalize_text(best_match.get("text", ""), "L1") or normalize_text(best_match.get("text", ""), "L1") in l1:
                text_status = "AUTHENTIC_PARTIAL"
            elif char_similarity >= 0.92 and lexical_similarity >= 0.8:
                text_status = "MODIFIED_MINIMAL"
            elif char_similarity >= 0.78 and lexical_similarity >= 0.55:
                text_status = "MODIFIED"
            elif semantic_similarity is not None and semantic_similarity >= 0.8 and lexical_similarity <= 0.5:
                text_status = "PARAPHRASED"
            else:
                text_status = "AMBIGUOUS"
            if best_candidate["score"] < 0.35:
                text_status = "FABRICATED"
        else:
            best_match = None
            text_status = "FABRICATED"

    if blend_matches:
        text_status = "BLENDED"

    content_status = text_status
    extra_words = _extra_words_outside_canonical_kural(l1, corpus)
    if extra_words:
        text_status = "NOT_KURAL_STRUCTURE"

    if best_match is None:
        return {
            "text_status": "FABRICATED",
            "human_label": TEXT_STATUS_LABELS["FABRICATED"],
            "presentation_status": "NOT_CLEAR",
            "attribution_status": "NOT_PROVIDED" if claimed_kural_number is None else "UNSUPPORTED",
            "normalization": {"L0_match": False, "L1_match": False, "L2_match": False, "L0": l0, "L1": l1, "L2": l2},
            "signals": {"character_similarity": 0.0, "edit_distance": 0, "lexical_similarity": 0.0, "semantic_similarity": None},
            "possible_originals": [],
            "evidence": {"matched_kural": None, "coverage": 0.0, "contiguous": False, "candidate_rank": None, "claim_supported": False},
            "why": ["No reasonable canonical match was found in the 1,330-Kural corpus.", "The quotation does not exhibit sufficient exact, lexical, or semantic support for a canonical attribution."],
            "claimed_kural_number": claimed_kural_number,
            "best_candidate": None,
            "technical_label": "FABRICATED",
            "content_status": "FABRICATED",
            "structure_status": "NOT_ASSESSED",
            "extra_words": [],
        }

    candidate_scores: list[dict] = []
    for item in corpus:
        candidate_text = normalize_text(item.get("text", ""), "L1")
        if not candidate_text:
            continue
        char_similarity = _character_similarity(l1, candidate_text)
        lexical_similarity = max(_tfidf_cosine_similarity(l1, candidate_text), _sequence_similarity(l1, candidate_text))
        semantic_similarity = _semantic_similarity(l1, candidate_text)
        score = _fused_similarity(char_similarity, lexical_similarity, semantic_similarity)
        candidate_scores.append({
            "item": item,
            "score": score,
            "character_similarity": char_similarity,
            "lexical_similarity": lexical_similarity,
            "semantic_similarity": semantic_similarity,
            "edit_distance": _edit_distance(l1, candidate_text),
        })
    ranked_candidates = sorted(candidate_scores, key=lambda item: item["score"], reverse=True)[:3]
    top_3 = [
        _candidate_for_entry(
            candidate["item"],
            l1,
            candidate["score"],
            candidate["lexical_similarity"],
            candidate["semantic_similarity"],
        )
        for candidate in ranked_candidates
    ]
    displayed_numbers = {candidate["kural_number"] for candidate in top_3}
    for blend_match in blend_matches:
        source_number = blend_match["item"]["kural_number"]
        if source_number in displayed_numbers:
            continue
        source_score = next(
            candidate for candidate in candidate_scores
            if candidate["item"]["kural_number"] == source_number
        )
        source_candidate = _candidate_for_entry(
            source_score["item"], l1, source_score["score"],
            source_score["lexical_similarity"], source_score["semantic_similarity"],
        )
        if len(top_3) < 3:
            top_3.append(source_candidate)
        else:
            top_3[-1] = source_candidate
        displayed_numbers.add(source_number)

    best_candidate = ranked_candidates[0]
    best_match_text = normalize_text(best_match.get("text", ""), "L1")
    candidate_text = best_match_text
    coverage = 0.0
    contiguous = False
    if l1 and candidate_text:
        if l1 in candidate_text or candidate_text in l1:
            coverage = min(len(l1), len(candidate_text)) / max(len(l1), len(candidate_text))
            contiguous = True
        else:
            overlap = 0
            for start in range(len(l1)):
                for end in range(start + 1, len(l1) + 1):
                    fragment = l1[start:end]
                    if fragment and fragment in candidate_text:
                        overlap = max(overlap, len(fragment))
            coverage = overlap / max(len(l1), 1)
            contiguous = overlap > 0
    char_similarity = best_candidate["character_similarity"]
    lexical_similarity = best_candidate["lexical_similarity"]
    semantic_similarity = best_candidate["semantic_similarity"]
    matched_kural = int(best_match.get("kural_number"))
    claimed_number = str(claimed_kural_number).strip() if claimed_kural_number is not None else None
    attribution_status = "NOT_PROVIDED"
    if claimed_number:
        try:
            claimed_int = int(claimed_number)
            if not 1 <= claimed_int <= 1330:
                attribution_status = "UNSUPPORTED"
            elif claimed_int == matched_kural:
                attribution_status = "CORRECT"
            else:
                attribution_status = "INCORRECT"
        except ValueError:
            attribution_status = "UNSUPPORTED"
    else:
        attribution_status = "NOT_PROVIDED"

    presentation_status = "PRESENTED_AS_CANONICAL"
    if text_status in {"PARAPHRASED"}:
        presentation_status = "PRESENTED_AS_PARAPHRASE"
    elif text_status in {"AUTHENTIC_PARTIAL"}: 
        presentation_status = "PRESENTED_AS_ORIGINAL"
    elif text_status == "NOT_KURAL_STRUCTURE":
        presentation_status = "NOT_KURAL_STRUCTURE"
    elif text_status == "FABRICATED":
        presentation_status = "NOT_CLEAR"

    user_label = TEXT_STATUS_LABELS.get(text_status, "Needs Review")
    why_lines = [
        (
            f"Extra word(s) were found around the wording of a canonical Kural: "
            f"{', '.join(extra_words)}."
            if extra_words
            else "The quotation was normalized and compared against the verified corpus."
        ),
        f"It was most similar to Kural {matched_kural} with a similarity score of {best_candidate['score']:.2f}.",
        f"Coverage of the matched canonical text was {coverage:.2f} and contiguous evidence was {'present' if contiguous else 'not present'}.",
    ]
    if attribution_status == "INCORRECT":
        why_lines.append(f"The supplied attribution claimed Kural {claimed_number}, but the evidence points to Kural {matched_kural}.")
    elif attribution_status == "CORRECT":
        why_lines.append("The claimed Kural number matches the strongest corpus evidence.")
    else:
        why_lines.append("No explicit Kural number attribution was supplied for this quotation.")
    if text_status in {"MODIFIED_MINIMAL", "MODIFIED"}:
        why_lines.append("The quotation retains most of the original wording but includes a small text difference.")
    elif text_status == "BLENDED":
        source_numbers = [match["item"]["kural_number"] for match in blend_matches]
        why_lines.append(
            f"Separate contiguous wording spans were found in Kurals {source_numbers[0]} and {source_numbers[1]}."
        )
    elif text_status == "AUTHENTIC_PARTIAL":
        why_lines.append("The submitted quotation is a contiguous excerpt of the canonical Kural.")
    elif text_status == "FABRICATED":
        why_lines.append("No sufficient textual or semantic evidence connected the quotation to the reference corpus.")
    elif text_status == "PARAPHRASED":
        why_lines.append("The wording shifts semantically while preserving the general idea, rather than matching the canonical passage.")
    if extra_words:
        why_lines.append(
            f"All words of Kural {matched_kural} appear in order, but the additional words mean the submitted text is not a canonical Kural structure."
        )

    result = {
        "text_status": text_status,
        "human_label": user_label,
        "technical_label": text_status,
        "presentation_status": presentation_status,
        "attribution_status": attribution_status,
        "normalization": {
            "L0_match": any(normalize_text(item.get("text", ""), "L0") == l0 for item in corpus),
            "L1_match": any(normalize_text(item.get("text", ""), "L1") == l1 for item in corpus),
            "L2_match": any(normalize_text(item.get("text", ""), "L2") == l2 for item in corpus),
            "L0": l0,
            "L1": l1,
            "L2": l2,
        },
        "signals": {
            "character_similarity": round(char_similarity, 4),
            "edit_distance": int(best_candidate["edit_distance"]),
            "lexical_similarity": round(lexical_similarity, 4),
            "semantic_similarity": None if semantic_similarity is None else round(semantic_similarity, 4),
        },
        "possible_originals": top_3,
        "evidence": {
            "matched_kural": matched_kural,
            "coverage": round(coverage, 4),
            "contiguous": bool(contiguous),
            "candidate_rank": 1,
            "claim_supported": attribution_status == "CORRECT",
            "blend_sources": [
                {"kural_number": match["item"]["kural_number"], "matched_words": match["length"]}
                for match in blend_matches
            ],
        },
        "why": why_lines,
        "claimed_kural_number": claimed_kural_number,
        "content_status": content_status,
        "structure_status": (
            "NOT_KURAL_STRUCTURE"
            if extra_words
            else "KURAL_STRUCTURE"
            if content_status in {"AUTHENTIC_EXACT", "AUTHENTIC_FORMAT", "AUTHENTIC_JOINING"}
            else "NOT_ASSESSED"
        ),
        "extra_words": extra_words,
        "best_candidate": {
            "kural_number": matched_kural,
            "chapter": best_match.get("chapter"),
            "chapter_number": best_match.get("chapter_number"),
            "text": best_match.get("text"),
            "score": round(best_candidate["score"], 4),
        },
        "matched_text": best_match.get("text"),
        "chapter_number": best_match.get("chapter_number"),
        "line1": best_match.get("line1"),
        "line2": best_match.get("line2"),
    }
    return result


def get_corpus_stats() -> dict:
    corpus = load_corpus()
    chapter_numbers = {str(item["chapter_number"]) for item in corpus}
    return {
        "records": len(corpus),
        "chapters": len(chapter_numbers),
        "first_kural": corpus[0]["kural_number"],
        "last_kural": corpus[-1]["kural_number"],
        "source": "Project Madurai",
    }


def get_corpus_by_number(kural_number: int) -> dict | None:
    for item in load_corpus():
        if int(item["kural_number"]) == int(kural_number):
            return item
    return None


def validate_corpus() -> dict:
    corpus = load_corpus()
    errors: list[str] = []
    if len(corpus) != 1330:
        errors.append(f"Expected 1330 records, found {len(corpus)}")
    numbers = [int(item["kural_number"]) for item in corpus]
    if sorted(numbers) != list(range(1, 1331)):
        missing = sorted(set(range(1, 1331)) - set(numbers))
        errors.append(f"Missing or duplicate Kural numbers: {missing[:10]}")
    chapter_counts = Counter(str(item["chapter_number"]) for item in corpus)
    if len(chapter_counts) != 133 or any(count != 10 for count in chapter_counts.values()):
        errors.append(f"Chapter totals invalid: {dict(chapter_counts)}")
    normalized_couplets = [
        unicodedata.normalize("NFC", re.sub(r"\s+", " ", str(item.get("text", ""))).strip())
        for item in corpus
    ]
    duplicate_couplets = [text for text, count in Counter(normalized_couplets).items() if count > 1]
    if duplicate_couplets:
        errors.append(f"Duplicate couplets found: {len(duplicate_couplets)}")
    for item in corpus:
        text = str(item.get("text", ""))
        if not (text and item.get("line1") and item.get("line2")):
            errors.append(f"Empty entry at Kural {item.get('kural_number')}")
        if not unicodedata.is_normalized("NFC", text):
            errors.append(f"Non-NFC text at Kural {item.get('kural_number')}")
        if not any("\u0b80" <= char <= "\u0bff" for char in text):
            errors.append(f"Tamil text missing at Kural {item.get('kural_number')}")
        if "<" in text or ">" in text:
            errors.append(f"HTML-like content remains in Kural {item.get('kural_number')}")
    return {
        "valid": not errors,
        "record_count": len(corpus),
        "chapter_count": len(chapter_counts),
        "missing_records": sorted(set(range(1, 1331)) - set(numbers))[:10],
        "errors": errors,
    }


def parse_dataset() -> dict:
    script_path = ROOT / "scripts" / "parse_kural_html.py"
    result = subprocess.run(["python", str(script_path)], capture_output=True, text=True, cwd=str(ROOT), encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    stats = get_corpus_stats()
    return {"status": "ok", "records": stats["records"], "chapters": stats["chapters"], "source": stats["source"]}
