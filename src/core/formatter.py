"""
Utility to convert literal '\\n' and '\\r\\n' escape sequences into real line breaks,
preserving 100% of the original Markdown formatting without modifying words or structure.
"""

from typing import Tuple


def replace_escaped_newlines(text: str) -> Tuple[str, int]:
    """
    Replaces literal '\\r\\n' and '\\n' escape strings with real newline characters.
    Does NOT alter any words, punctuation, or Markdown syntax.
    Returns (cleaned_text: str, total_replacements: int).
    """
    if not text:
        return text, 0

    count_crlf = text.count(r"\r\n")
    count_lf = text.count(r"\n")
    total = count_crlf + count_lf

    if total == 0:
        return text, 0

    # Replace literal \r\n first, then literal \n
    repaired = text.replace(r"\r\n", "\n").replace(r"\n", "\n")
    return repaired, total


def has_escaped_newlines(text: str) -> bool:
    """
    Returns True if the text contains literal '\\n' or '\\r\\n' strings.
    """
    return bool(text and (r"\n" in text or r"\r\n" in text))
