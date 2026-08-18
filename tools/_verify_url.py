"""
_verify_url.py — Anti-hallucination verifier for LLM-suggested decydents.

For each LLM result, fetch the suggested source URL and check that the
decydent's name appears in the page content. Returns True only if verified.
"""
import re
import urllib.request


def _normalize_name(name: str) -> str:
    """Normalize name for fuzzy matching — drop titles, accents, case."""
    if not name:
        return ""
    n = name.lower()
    # Remove titles
    for t in [
        "ing.", "ing ", "mgr.", "mgr ", "bc.", "bc ", "rndr.", "rndr ",
        "phd.", "phd ", "doc.", "doc ", "prof.", "prof ",
        "dr.", "dr ", "mba", "msc.", "msc ",
    ]:
        n = n.replace(t, " ")
    # Remove accents
    accents = {"á": "a", "č": "c", "ď": "d", "é": "e", "ě": "e", "í": "i",
               "ľ": "l", "ň": "n", "ó": "o", "ř": "r", "š": "s", "ť": "t",
               "ú": "u", "ů": "u", "ý": "y", "ž": "z", "ä": "a", "ö": "o",
               "ü": "u", "ß": "ss", "ł": "l", "ą": "a", "ę": "e", "ć": "c",
               "ń": "n", "ś": "s", "ź": "z", "ż": "z"}
    for src, dst in accents.items():
        n = n.replace(src, dst)
    # Collapse whitespace
    n = re.sub(r"\s+", " ", n).strip()
    return n


def verify_name_in_url(name: str, source_url: str, timeout: int = 8) -> dict:
    """Fetch source URL, check if decydent name appears in content.

    Returns:
        {
          "verified": bool,
          "confidence": "high" | "medium" | "low",
          "match_count": int,
          "error": str | None,
          "snippet": str | None
        }
    """
    if not name or not source_url or not source_url.startswith(("http://", "https://")):
        return {"verified": False, "error": "missing name or URL", "match_count": 0}
    try:
        req = urllib.request.Request(
            source_url,
            headers={
                "User-Agent": "Mozilla/5.0 BILLSzuka/1.0 research@bills.pl",
                "Accept-Language": "pl,en;q=0.7,sk;q=0.5,de;q=0.5",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ct = r.headers.get("content-type", "").lower()
            data = r.read()
        # Decode
        for enc in ("utf-8", "windows-1250", "windows-1251", "iso-8859-2", "latin-1"):
            try:
                html = data.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            html = data.decode("utf-8", errors="ignore")
    except Exception as e:
        return {"verified": False, "error": str(e)[:200], "match_count": 0}
    # If it's a PDF or binary, skip (would need OCR)
    if "pdf" in ct or "octet" in ct:
        return {"verified": False, "error": "PDF/binary content", "match_count": 0}
    # Strip HTML
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    text_lower = text.lower()
    # Normalize both
    target = _normalize_name(name)
    text_normalized = _normalize_name(text)
    # Try various matching strategies
    matches = 0
    snippet = None
    # 1. Exact full name in normalized text
    if target and target in text_normalized:
        matches += 2
        # Get snippet
        idx = text_normalized.find(target)
        if idx > 0:
            snippet = text_normalized[max(0, idx - 80):idx + len(target) + 80]
    # 2. Last name only (more specific)
    parts = target.split()
    if len(parts) >= 2:
        last_name = parts[-1]
        if len(last_name) >= 4 and last_name in text_normalized:
            matches += 1
    # 3. First name + last name pair (with various separators)
    if len(parts) >= 2:
        first = parts[0]
        last = parts[-1]
        for sep in [" ", ", ", "-", "."]:
            pair = f"{first}{sep}{last}"
            if pair in text_normalized:
                matches += 1
                break
    confidence = "high" if matches >= 3 else ("medium" if matches >= 1 else "low")
    return {
        "verified": matches >= 1,
        "confidence": confidence,
        "match_count": matches,
        "error": None,
        "snippet": snippet[:300] if snippet else None,
    }
