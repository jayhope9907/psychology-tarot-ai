"""B2B privacy: PII anonymization for society / org dashboards."""
from __future__ import annotations

import re
from typing import Any, Dict, Tuple

# Korean + intl phone / email / RRNs / names heuristics
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(
    r"(?<!\d)(?:0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}|01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}|\+82[-.\s]?\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4})(?!\d)"
)
_RRN_RE = re.compile(r"\b\d{6}[-\s]?[1-8]\d{6}\b")
_CARD_RE = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
# 「저는 김민수예요」「제 이름은 이서연」
_NAME_RE = re.compile(
    r"(?:(?:제\s*이름(?:은|은요)?|저는|난|내가)\s*)([가-힣]{2,4})(?:입니다|이에요|예요|야|임)?"
)
_ADDRESS_RE = re.compile(
    r"(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)"
    r"[가-힣0-9\s]{0,24}(?:시|군|구|동|로|길)\s*\d*"
)

MASK = "[비식별화]"


def anonymize_pii(text: str) -> Tuple[str, Dict[str, int]]:
    """Replace PII with [비식별화]. Returns (masked_text, hit_counts)."""
    if not text:
        return "", {}
    counts: Dict[str, int] = {}
    out = text

    def _sub(pattern: re.Pattern[str], label: str, src: str) -> str:
        found = pattern.findall(src)
        if not found:
            return src
        counts[label] = counts.get(label, 0) + len(found)
        return pattern.sub(MASK, src)

    out = _sub(_EMAIL_RE, "email", out)
    out = _sub(_PHONE_RE, "phone", out)
    out = _sub(_RRN_RE, "rrn", out)
    out = _sub(_CARD_RE, "card", out)
    out = _sub(_ADDRESS_RE, "address", out)

    def _name_repl(m: re.Match[str]) -> str:
        counts["name"] = counts.get("name", 0) + 1
        return m.group(0).replace(m.group(1), MASK)

    out = _NAME_RE.sub(_name_repl, out)
    return out, counts


def anonymize_messages(messages: Any) -> Dict[str, Any]:
    """Anonymize a chat transcript list for B2B export / SOS payloads."""
    rows = []
    total_hits: Dict[str, int] = {}
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        content = str(m.get("content") or "")
        masked, hits = anonymize_pii(content)
        for k, v in hits.items():
            total_hits[k] = total_hits.get(k, 0) + v
        rows.append(
            {
                "role": m.get("role"),
                "content": masked,
                "pii_masked": bool(hits),
            }
        )
    return {
        "messages": rows,
        "pii_hit_counts": total_hits,
        "mask_token": MASK,
    }


def maybe_anonymize_for_license(text: str, *, license_type: str) -> Dict[str, Any]:
    from app.models.commercial_license import is_b2b_license

    if not is_b2b_license(license_type):
        return {"text": text, "masked": False, "pii_hit_counts": {}, "licenseType": license_type}
    masked, hits = anonymize_pii(text)
    return {
        "text": masked,
        "masked": True,
        "pii_hit_counts": hits,
        "licenseType": license_type,
        "original_length": len(text or ""),
    }
