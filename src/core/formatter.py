"""
Utility to convert literal '\\n' and '\\r\\n' escape sequences into real line breaks,
and extract clean filesystem-safe filenames from Markdown headings/first lines.
"""

import re
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

    repaired = text.replace(r"\r\n", "\n").replace(r"\n", "\n")
    return repaired, total


def has_escaped_newlines(text: str) -> bool:
    """
    Returns True if the text contains literal '\\n' or '\\r\\n' strings.
    """
    return bool(text and (r"\n" in text or r"\r\n" in text))


def sanitize_first_line_as_filename(text: str, max_length: int = 80) -> str:
    """
    Extracts the first non-empty line of text, removes markdown heading/bullet syntax,
    and returns a clean, filesystem-safe filename string for Windows, Linux, and macOS.
    """
    if not text:
        return "documento"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Strip leading markdown symbols: #, >, -, *, +
        clean = re.sub(r'^[#>\-\*\+\s]+', '', line).strip()

        # Replace colon and slash separators with space-dash-space
        clean = re.sub(r'[:/\\|]', ' - ', clean)

        # Remove remaining illegal filesystem characters: * ? " < >
        clean = re.sub(r'[\*\?\"<>]', '', clean)

        # Collapse whitespace and redundant dashes
        clean = re.sub(r'\s+', ' ', clean)
        clean = re.sub(r'( - )+', ' - ', clean).strip(' .-_')

        if clean:
            return clean[:max_length].rstrip(' .-_')

    return "documento"
