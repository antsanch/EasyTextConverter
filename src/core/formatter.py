"""
Auto-formatting and repair utilities for Markdown text.
Fixes common formatting defects when copying/pasting from PDFs, web pages, or LLMs,
such as glued headings, missing newlines, broken lists, and damaged bold markers.
"""

import re
from typing import Tuple


def auto_format_markdown(text: str) -> Tuple[str, int]:
    """
    Cleans, repairs, and formats markdown text to ensure headings, lists,
    tables, and blockquotes have correct newlines and spacing.
    Returns (repaired_text: str, total_repairs_count: int).
    """
    if not text or not text.strip():
        return text, 0

    original = text
    repairs = 0

    # 1. Normalize line endings (CRLF / CR -> LF)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Fix headings glued to previous text or punctuation:
    # e.g.: "...texto anterior.—### 2. Título" or "...párrafo.#### Subtítulo"
    def fix_heading_prefix(m):
        nonlocal repairs
        repairs += 1
        heading = m.group(2)
        return "\n\n" + heading

    text = re.sub(r'([^\n])\s*[-—–]*\s*(#{1,6}\s+)', fix_heading_prefix, text)

    # 3. Fix headings closing with parenthesis glued to next sentence:
    # e.g.: "#### A) Barrido Panorámico (Skimming)en examinar el texto..."
    # -> "#### A) Barrido Panorámico (Skimming)\n\nEn examinar el texto..."
    def fix_paren_heading_end(m):
        nonlocal repairs
        repairs += 1
        heading_part = m.group(1)
        next_word = m.group(2)
        return f"{heading_part}\n\n{next_word.capitalize()}"

    text = re.sub(
        r'(#{1,6}\s+[^\n#]{2,80}?\))\s*([a-záéíóú][a-záéíóúñA-ZÁÉÍÓÚ\s]{2,})',
        fix_paren_heading_end,
        text
    )

    # 4. Fix words glued between heading title and paragraph body:
    # e.g.: "### 2. Lectura Explorativa: Topografía y Rastreolectura explorativa es..."
    # -> "### 2. Lectura Explorativa: Topografía y Rastreo\n\nLectura explorativa es..."
    common_starters = (
        r'lectura|consiste|en |es una|una vez|el |la |los |las |un |una |este |esta |estos |'
        r'estas |para |por |cuando |como |si |al |según |de acuerdo|en cuanto|cuyo|cuya'
    )
    def fix_heading_word_glue(m):
        nonlocal repairs
        repairs += 1
        h_prefix = m.group(1)
        last_word = m.group(2)
        starter = m.group(3)
        rest = m.group(4)
        return f"{h_prefix}{last_word}\n\n{starter.capitalize()}{rest}"

    pattern_glue = (
        r'(#{1,6}\s+[^\n#]{4,70}?)'
        r'([A-ZÁÉÍÓÚ][a-zñáéíóú]+)'
        f'({common_starters})'
        r'([a-zñáéíóú\s].*)'
    )
    text = re.sub(pattern_glue, fix_heading_word_glue, text)

    # 5. Fix multiple headings accidentally placed on the same line
    # e.g.: "### Título 1 #### Título 2"
    def fix_inline_headings(m):
        nonlocal repairs
        repairs += 1
        return "\n\n" + m.group(1)

    text = re.sub(r'(?<=[^\n])\s+(#{1,6}\s+)', fix_inline_headings, text)

    # 6. Ensure headings always have an empty line after them if followed directly by text
    lines = text.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        # If line is a heading and next line is non-empty and not another heading/list
        if re.match(r'^#{1,6}\s+', line.strip()):
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith("#"):
                    new_lines.append("")
                    repairs += 1
        i += 1
    text = "\n".join(new_lines)

    # 7. Fix lists glued to preceding text without a newline
    # e.g.: "...párrafo anterior.- Elemento 1" -> "...párrafo anterior.\n\n- Elemento 1"
    def fix_list_prefix(m):
        nonlocal repairs
        repairs += 1
        return m.group(1) + "\n\n" + m.group(2)

    text = re.sub(r'([^\n\s])\s*([—–-]\s+[A-Z0-9ÁÉÍÓÚ])', fix_list_prefix, text)
    text = re.sub(r'([^\n\s])\s*(\d+\.\s+[A-ZÁÉÍÓÚ])', fix_list_prefix, text)

    # 8. Fix period-dot list bullets like ".. Leer el título" or ". Leer la primera"
    def fix_dot_bullets(m):
        nonlocal repairs
        repairs += 1
        return m.group(1) + "\n- " + m.group(2)

    text = re.sub(r'([^\n])\s*\.{1,2}\s+([A-ZÁÉÍÓÚ][a-zñáéíóú\s]{3,})', fix_dot_bullets, text)

    # 9. Fix tables glued to text: lines with "|" preceded by non-table content
    def fix_table_glue(m):
        nonlocal repairs
        repairs += 1
        return m.group(1) + "\n" + m.group(2)

    text = re.sub(r'([^\n\|])\s*(\|)', fix_table_glue, text)

    # 10. Fix malformed bold markers like "*Texto:**" -> "**Texto:**"
    def fix_bold_marker(m):
        nonlocal repairs
        repairs += 1
        return f"**{m.group(1)}:**"

    text = re.sub(r'(?<!\*)\*([A-Za-z0-9ÁÉÍÓÚáéíóú][^*]{1,80}?)\:\*\*', fix_bold_marker, text)

    # 11. Normalize excessive blank lines (max 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip(), repairs


def has_potential_formatting_defects(text: str) -> bool:
    """
    Fast check to detect if text contains headings glued without newlines,
    which would cause Pandoc to treat multiple paragraphs as a single header.
    """
    if not text or not text.strip():
        return False

    # Glued headings like '...texto.—###' or '...texto.###'
    if re.search(r'[^\n]\s*[-—–]*\s*#{1,6}\s+', text):
        return True

    # Heading lines that are abnormally long (> 200 chars) usually contain glued paragraphs
    for line in text.splitlines():
        trimmed = line.strip()
        if re.match(r'^#{1,6}\s+', trimmed) and len(trimmed) > 180:
            return True

    return False
