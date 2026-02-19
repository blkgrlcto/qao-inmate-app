"""Detect whether user input is a docket number or a person name."""
import re


def detect_mode(input_str: str) -> tuple[str, str]:
    """
    Detect search mode: 'docket' or 'name'.
    Returns (mode, normalized_query).
    """
    if not input_str or not isinstance(input_str, str):
        return "name", ""

    normalized = " ".join(input_str.strip().split())
    if not normalized:
        return "name", ""

    # Docket patterns (case-insensitive)
    # 1) cv, cr, mj, bk, mc with colon: e.g. 1:23-cv-01234, 2:22-cr-00012
    if re.search(r":\s*(cv|cr|mj|bk|mc)\b", normalized, re.I):
        return "docket", normalized

    # 2) Appellate/supreme: 23A994, 21-1234 (digits + optional letter + digits)
    if re.match(r"^\d+[A-Za-z]?\d+$", normalized.replace("-", "").replace(":", "")):
        return "docket", normalized

    # 3) Many digits with separators: digits + (-|:) + digits (docket-like)
    digit_sep = re.findall(r"\d+", normalized)
    separators = re.findall(r"[-:]", normalized)
    if len(digit_sep) >= 2 and len(separators) >= 1:
        return "docket", normalized

    # Otherwise treat as name
    # Accept "Last, First" and "First Last" - pass as phrase to party:(...)
    return "name", normalized
