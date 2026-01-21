#!/usr/bin/env python3
"""
bible-to-format_v2.py - Convert diatheke HTML output to various formats

Supports: typst, latex, markdown, org-mode, plain
Preserves poetic line breaks from Psalms and other poetic books.

Usage:
    dutch-diatheke.py -b HSV -f HTML "Psalm 3:9" | bible-to-format_v2.py --format tex
    dutch-diatheke.py -b HSV -f HTML "Psalm 3:9" | bible-to-format_v2.py --format md
    dutch-diatheke.py -b HSV -f HTML "Psalm 3:9" | bible-to-format_v2.py --format typ
    dutch-diatheke.py -b HSV -f HTML "Psalm 3:9" | bible-to-format_v2.py --format org
    dutch-diatheke.py -b HSV -f HTML "Psalm 3:9" | bible-to-format_v2.py --format plain
"""

import sys
import re
import argparse
from typing import List, Tuple, Optional

# Dutch modules that should use Dutch book names
DUTCH_MODULES = {'HSV', 'DutSVV', 'NBV21', 'BGT', 'GBS', 'DutSVVA'}

# English to Dutch book name mapping
DUTCH_BOOK_NAMES = {
    "Genesis": "Genesis", "Exodus": "Exodus", "Leviticus": "Leviticus", "Numbers": "Numeri",
    "Deuteronomy": "Deuteronomium", "Joshua": "Jozua", "Judges": "Richteren", "Ruth": "Ruth",
    "1Samuel": "1 Samuël", "2Samuel": "2 Samuël", "I Samuel": "1 Samuël", "II Samuel": "2 Samuël",
    "1Kings": "1 Koningen", "2Kings": "2 Koningen", "I Kings": "1 Koningen", "II Kings": "2 Koningen",
    "1Chronicles": "1 Kronieken", "2Chronicles": "2 Kronieken", "I Chronicles": "1 Kronieken", "II Chronicles": "2 Kronieken",
    "Ezra": "Ezra", "Nehemiah": "Nehemia", "Esther": "Esther", "Job": "Job",
    "Psalms": "Psalmen", "Proverbs": "Spreuken", "Ecclesiastes": "Prediker", "Song of Solomon": "Hooglied",
    "Isaiah": "Jesaja", "Jeremiah": "Jeremia", "Lamentations": "Klaagliederen", "Ezekiel": "Ezechiël",
    "Daniel": "Daniël", "Hosea": "Hosea", "Joel": "Joël", "Amos": "Amos",
    "Obadiah": "Obadja", "Jonah": "Jona", "Micah": "Micha", "Nahum": "Nahum",
    "Habakkuk": "Habakuk", "Zephaniah": "Zefanja", "Haggai": "Haggaï", "Zechariah": "Zacharia", "Malachi": "Maleachi",
    "Matthew": "Mattheüs", "Mark": "Marcus", "Luke": "Lucas", "John": "Johannes",
    "Acts": "Handelingen", "Romans": "Romeinen",
    "1Corinthians": "1 Korinthe", "2Corinthians": "2 Korinthe", "I Corinthians": "1 Korinthe", "II Corinthians": "2 Korinthe",
    "Galatians": "Galaten", "Ephesians": "Efeze", "Philippians": "Filippenzen", "Colossians": "Kolossenzen",
    "1Thessalonians": "1 Thessalonicenzen", "2Thessalonians": "2 Thessalonicenzen",
    "1Timothy": "1 Timotheüs", "2Timothy": "2 Timotheüs", "I Timothy": "1 Timotheüs", "II Timothy": "2 Timotheüs",
    "Titus": "Titus", "Philemon": "Filemon", "Hebrews": "Hebreeën", "James": "Jakobus",
    "1Peter": "1 Petrus", "2Peter": "2 Petrus", "I Peter": "1 Petrus", "II Peter": "2 Petrus",
    "1John": "1 Johannes", "2John": "2 Johannes", "3John": "3 Johannes",
    "Jude": "Judas", "Revelation": "Openbaring"
}

DUTCH_BOOK_ABBREV = {
    "Genesis": "Gen.", "Exodus": "Ex.", "Leviticus": "Lev.", "Numbers": "Num.",
    "Deuteronomy": "Deut.", "Joshua": "Joz.", "Judges": "Richt.", "Ruth": "Ruth",
    "1Samuel": "1 Sam.", "2Samuel": "2 Sam.", "I Samuel": "1 Sam.", "II Samuel": "2 Sam.",
    "1Kings": "1 Kon.", "2Kings": "2 Kon.", "I Kings": "1 Kon.", "II Kings": "2 Kon.",
    "1Chronicles": "1 Kron.", "2Chronicles": "2 Kron.", "I Chronicles": "1 Kron.", "II Chronicles": "2 Kron.",
    "Ezra": "Ezra", "Nehemiah": "Neh.", "Esther": "Est.", "Job": "Job",
    "Psalms": "Ps.", "Proverbs": "Spr.", "Ecclesiastes": "Pred.", "Song of Solomon": "Hoogl.",
    "Isaiah": "Jes.", "Jeremiah": "Jer.", "Lamentations": "Klaagl.", "Ezekiel": "Ez.",
    "Daniel": "Dan.", "Hosea": "Hos.", "Joel": "Joël", "Amos": "Am.",
    "Obadiah": "Ob.", "Jonah": "Jona", "Micah": "Micha", "Nahum": "Nah.",
    "Habakkuk": "Hab.", "Zephaniah": "Zef.", "Haggai": "Hag.", "Zechariah": "Zach.", "Malachi": "Mal.",
    "Matthew": "Matt.", "Mark": "Mark", "Luke": "Luk.", "John": "Joh.",
    "Acts": "Hand.", "Romans": "Rom.",
    "1Corinthians": "1 Kor.", "2Corinthians": "2 Kor.", "I Corinthians": "1 Kor.", "II Corinthians": "2 Kor.",
    "Galatians": "Gal.", "Ephesians": "Ef.", "Philippians": "Fil.", "Colossians": "Kol.",
    "1Thessalonians": "1 Thess.", "2Thessalonians": "2 Thess.",
    "1Timothy": "1 Tim.", "2Timothy": "2 Tim.", "I Timothy": "1 Tim.", "II Timothy": "2 Tim.",
    "Titus": "Tit.", "Philemon": "Filem.", "Hebrews": "Hebr.", "James": "Jak.",
    "1Peter": "1 Petr.", "2Peter": "2 Petr.", "I Peter": "1 Petr.", "II Peter": "2 Petr.",
    "1John": "1 Joh.", "2John": "2 Joh.", "3John": "3 Joh.",
    "Jude": "Judas", "Revelation": "Openb."
}

VERSION_ABBREV = {
    "DutSVV": "SV",
    "GBS2": "SV-GBS",
}

ENGLISH_BOOK_ABBREV = {
    "Genesis": "Gen.", "Exodus": "Ex.", "Leviticus": "Lev.", "Numbers": "Num.",
    "Deuteronomy": "Deut.", "Joshua": "Josh.", "Judges": "Judg.", "Ruth": "Ruth",
    "1Samuel": "1 Sam.", "2Samuel": "2 Sam.", "I Samuel": "1 Sam.", "II Samuel": "2 Sam.",
    "1Kings": "1 Kings", "2Kings": "2 Kings", "I Kings": "1 Kings", "II Kings": "2 Kings",
    "1Chronicles": "1 Chron.", "2Chronicles": "2 Chron.", "I Chronicles": "1 Chron.", "II Chronicles": "2 Chron.",
    "Ezra": "Ezra", "Nehemiah": "Neh.", "Esther": "Est.", "Job": "Job",
    "Psalms": "Ps.", "Proverbs": "Prov.", "Ecclesiastes": "Eccl.", "Song of Solomon": "Song",
    "Isaiah": "Isa.", "Jeremiah": "Jer.", "Lamentations": "Lam.", "Ezekiel": "Ezek.",
    "Daniel": "Dan.", "Hosea": "Hos.", "Joel": "Joel", "Amos": "Amos",
    "Obadiah": "Obad.", "Jonah": "Jon.", "Micah": "Mic.", "Nahum": "Nah.",
    "Habakkuk": "Hab.", "Zephaniah": "Zeph.", "Haggai": "Hag.", "Zechariah": "Zech.", "Malachi": "Mal.",
    "Matthew": "Matt.", "Mark": "Mark", "Luke": "Luke", "John": "John",
    "Acts": "Acts", "Romans": "Rom.",
    "1Corinthians": "1 Cor.", "2Corinthians": "2 Cor.", "I Corinthians": "1 Cor.", "II Corinthians": "2 Cor.",
    "Galatians": "Gal.", "Ephesians": "Eph.", "Philippians": "Phil.", "Colossians": "Col.",
    "1Thessalonians": "1 Thess.", "2Thessalonians": "2 Thess.",
    "1Timothy": "1 Tim.", "2Timothy": "2 Tim.", "I Timothy": "1 Tim.", "II Timothy": "2 Tim.",
    "Titus": "Titus", "Philemon": "Philem.", "Hebrews": "Heb.", "James": "Jas.",
    "1Peter": "1 Pet.", "2Peter": "2 Pet.", "I Peter": "1 Pet.", "II Peter": "2 Pet.",
    "1John": "1 John", "2John": "2 John", "3John": "3 John",
    "Jude": "Jude", "Revelation": "Rev."
}

def get_dutch_book_name(english_name: str) -> str:
    """Convert English book name to Dutch."""
    return DUTCH_BOOK_NAMES.get(english_name, english_name)


def get_book_name(book: str, module: Optional[str], book_style: str) -> str:
    if module and module in DUTCH_MODULES:
        if book_style == "abbr":
            return DUTCH_BOOK_ABBREV.get(book, book)
        return DUTCH_BOOK_NAMES.get(book, book)
    if book_style == "abbr":
        return ENGLISH_BOOK_ABBREV.get(book, book)
    return book


def get_version_tag(module: Optional[str], version_abbrev: str) -> str:
    if not module or version_abbrev == "none":
        return ""
    if version_abbrev == "auto":
        return VERSION_ABBREV.get(module, module)
    return module


def extract_reference(html_content: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extract book, chapter, verse range, and module from HTML content.

    Returns: (book, chapter, verse_range, module)
    """
    # Extract module name from end: (HSV) or (DutSVV)
    module_match = re.search(r'\(([A-Za-z0-9]+)\)\s*</body>', html_content)
    module = module_match.group(1) if module_match else None

    # Extract book, chapter, verse from first verse reference
    ref_match = re.search(r'([A-Za-z0-9]+)\s+(\d+):(\d+):', html_content)
    if ref_match:
        book = ref_match.group(1)
        chapter = ref_match.group(2)
        first_verse = ref_match.group(3)

        # Find all verses to determine range
        all_verses = re.findall(r'[A-Za-z0-9]+\s+\d+:(\d+):', html_content)
        if all_verses:
            last_verse = all_verses[-1]
            if first_verse == last_verse:
                verse_range = first_verse
            else:
                verse_range = f"{first_verse}-{last_verse}"
        else:
            verse_range = first_verse

        return book, chapter, verse_range, module

    return None, None, None, module


def extract_notes(text: str, inline_notes: bool) -> Tuple[str, List[Tuple[str, str, str]]]:
    notes: List[Tuple[str, str, str]] = []
    note_idx = 0

    def repl(match: re.Match) -> str:
        attrs = match.group(1)
        content = match.group(2).strip()
        if not content:
            return ''

        label = "note"
        if 'type="crossReference"' in attrs:
            label = "ref"

        nonlocal note_idx
        note_idx += 1
        marker_match = re.search(r'\bn="([^"]+)"', attrs)
        marker = marker_match.group(1) if marker_match else str(note_idx)
        notes.append((label, content, marker))
        return f"__NOTE{note_idx}__"

    text = re.sub(r'<note([^>]*)>(.*?)</note>', repl, text, flags=re.DOTALL)
    text = re.sub(r'<note[^>]*/>', '', text)
    text = re.sub(r'<note[^>]*></note>', '', text)

    return text, notes


def note_marker(fmt: str, marker: str) -> str:
    if fmt == 'org':
        return f"[fn:{marker}]"
    if fmt == 'md':
        return f"[^{marker}]"
    return f"[{marker}]"


def render_notes_in_text(text: str, fmt: str, notes: List[Tuple[str, str, str]],
                         options: str, inline_notes: bool) -> str:
    def repl(match: re.Match) -> str:
        idx = int(match.group(1))
        label, content, marker = notes[idx - 1]
        content_txt = process_text(content, fmt, options)

        if inline_notes:
            if fmt == 'org':
                return f"[fn:: {marker}. {content_txt}] "
            if fmt == 'md':
                return f"^[{marker}. {content_txt}] "
            if fmt == 'tex':
                return f"\\footnote{{{marker}. {content_txt}}} "
            if fmt == 'typ':
                return f"#footnote[{marker}. {content_txt}] "
            return f"[{marker}. {content_txt}] "
        if fmt == 'tex':
            return f"\\textsuperscript{{{marker}}}"
        if fmt == 'typ':
            return f"#super[{marker}]"
        return note_marker(fmt, marker)

    return re.sub(r'__NOTE(\d+)__', repl, text)


def parse_html_verses(html_content: str, inline_notes: bool = False
                      ) -> List[Tuple[str, str, int, List[str], bool, List[Tuple[str, str, str]]]]:
    """
    Parse HTML content from diatheke into structured verse data.

    Returns: List of (book, chapter, verse_number, lines, has_smallcaps, notes) tuples
    """
    verses = []

    # Remove structural tags
    html_content = re.sub(r'<(chapter|div)[^>]*/>', '', html_content)

    # Check if input has proper HTML verse formatting
    has_verse_html_tags = bool(re.search(r'<span[^>]*>', html_content))

    if not has_verse_html_tags:
        # Plain text format
        verse_blocks = re.findall(
            r'([A-Za-z]+) (\d+):(\d+): (.+?)(?=\n(?:[A-Za-z]+ \d+:\d+:|\Z))',
            html_content, re.DOTALL | re.MULTILINE
        )
        for book, chapter, verse_number, verse_content in verse_blocks:
            verse_content = re.sub(r'<milestone type="line"[^>]*/?>', '\n', verse_content)
            verse_content, notes = extract_notes(verse_content, inline_notes)
            lines = [line.strip() for line in verse_content.split('\n') if line.strip()]
            has_smallcaps = '<hi type="small-caps">' in verse_content
            if lines:
                verses.append((book, chapter, int(verse_number), lines, has_smallcaps, notes))
    else:
        # HTML format - check for poetic <l> tags
        has_l_tags = bool(re.search(r'<l sID="[^"]*"/>', html_content))

        # Extract verse blocks - match span with any attributes
        verse_blocks = re.findall(
            r'([A-Za-z0-9]+) (\d+):(\d+): <span[^>]*>(.*?)</span><br\s*/>',
            html_content, re.DOTALL
        )

        for book, chapter, verse_number, verse_content in verse_blocks:
            verse_number = int(verse_number)
            verse_content, notes = extract_notes(verse_content, inline_notes)
            has_smallcaps = '<hi type="small-caps">' in verse_content

            if has_l_tags:
                # Poetic content - process line breaks
                processed = verse_content

                # Convert line markers to newlines
                processed = re.sub(r'<l eID="[^"]*"/>\s*<l sID="[^"]*"/>', '\n', processed)

                # Remove remaining line markers
                processed = re.sub(r'<l [se]ID="[^"]*"/>', '', processed)

                # Remove chapter markers
                processed = re.sub(r'<chapter[^>]*/?>', '', processed)

                # Split into lines and clean
                lines = [line.strip() for line in processed.split('\n') if line.strip()]
            else:
                # Prose content - single line
                lines = [verse_content.strip()]

            if lines:
                verses.append((book, chapter, verse_number, lines, has_smallcaps, notes))

    return verses


def process_text(text: str, format: str, options: str = '') -> str:
    """Process text for specific output format (handle smallcaps, italics, notes, etc.)"""
    # Handle small-caps (HEERE/HEER)
    if format == 'typ':
        text = re.sub(r'<hi type="small-caps">([^<]+)</hi>', r'#smallcaps[\1]', text)
        text = re.sub(r'<i>(.*?)</i>', r'#emph[\1]', text)
    elif format == 'tex':
        text = re.sub(r'<hi type="small-caps">([^<]+)</hi>', r'\\textsc{\1}', text)
        text = re.sub(r'<i>(.*?)</i>', r'\\emph{\1}', text)
    elif format == 'md':
        # Markdown doesn't have native small-caps, use bold as approximation
        text = re.sub(r'<hi type="small-caps">([^<]+)</hi>', r'**\1**', text)
        text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)
    elif format == 'org':
        # Org-mode: use bold for small-caps, slashes for italics
        text = re.sub(r'<hi type="small-caps">([^<]+)</hi>', r'*\1*', text)
        text = re.sub(r'<i>(.*?)</i>', r'/\1/', text)

    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    return text.strip()


def format_note_text(fmt: str, marker: str, label: str, content: str, options: str) -> str:
    label_txt = "ref" if label == "ref" else "note"
    content_txt = process_text(content, fmt, options)
    if fmt == 'tex':
        return f"\\textsuperscript{{{marker}}} {label_txt}: {content_txt}"
    if fmt == 'typ':
        return f"#super[{marker}] {label_txt}: {content_txt}"
    return f"{note_marker(fmt, marker)} {label_txt}: {content_txt}"


def format_ref_text(book: Optional[str], chapter: Optional[str], verse_range: Optional[str],
                    module: Optional[str], book_style: str, version_abbrev: str) -> str:
    if not book or not chapter or not verse_range:
        return ""

    display_book = get_book_name(book, module, book_style)
    version_tag = get_version_tag(module, version_abbrev)

    ref = f"{display_book} {chapter}:{verse_range}"
    if version_tag:
        ref = f"{ref} {version_tag}"
    return ref


def wrap_ref_inline(fmt: str, ref_text: str) -> str:
    if fmt == 'tex':
        return f"\\hfill ({ref_text})"
    if fmt == 'typ':
        return f"#align(right)[({ref_text})]"
    if fmt == 'md':
        return f"*({ref_text})*"
    if fmt == 'org':
        return f"/({ref_text})/"
    return f"({ref_text})"


def ref_marker(fmt: str) -> str:
    if fmt == 'org':
        return "[fn:ref]"
    if fmt == 'md':
        return "[^ref]"
    return ""


def format_ref_footnote(fmt: str, ref_text: str) -> Tuple[str, str]:
    if fmt == 'tex':
        return f"\\footnote{{{ref_text}}}", ""
    if fmt == 'typ':
        return f"#footnote[{ref_text}]", ""
    marker = ref_marker(fmt)
    if marker:
        return marker, f"{marker} {ref_text}"
    return wrap_ref_inline(fmt, ref_text), ""


def format_verse_prefix(fmt: str, verse_num: int, verse_nums: str) -> str:
    if verse_nums == 'none':
        return ''
    if fmt in ('tex', 'typ'):
        return ''
    if verse_nums == 'colons':
        return f"{verse_num}: "
    return f"{verse_num}. "


def format_verse_label(fmt: str, verse_num: int, verse_nums: str) -> str:
    if verse_nums == 'none':
        return ''
    suffix = ':' if verse_nums == 'colons' else '.'
    return f"{verse_num}{suffix}"


def group_passages(verses: List[Tuple[str, str, int, List[str], bool, List[Tuple[str, str]]]]
                   ) -> List[Tuple[str, str, List[Tuple[int, List[str], bool, List[Tuple[str, str]]]]]]:
    passages = []
    current = None
    for book, chapter, verse_num, lines, has_smallcaps, notes in verses:
        if current is None or current[0] != book or current[1] != chapter:
            current = (book, chapter, [])
            passages.append(current)
        current[2].append((verse_num, lines, has_smallcaps, notes))
    return passages


def build_reference_block(book: Optional[str], chapter: Optional[str], verse_range: Optional[str],
                          module: Optional[str], fmt: str, book_style: str,
                          version_abbrev: str, ref_type: str) -> Tuple[str, str]:
    ref_text = format_ref_text(book, chapter, verse_range, module, book_style, version_abbrev)
    if not ref_text:
        return "", ""
    return build_reference_block_from_text(ref_text, fmt, ref_type)


def build_reference_block_from_text(ref_text: str, fmt: str, ref_type: str) -> Tuple[str, str]:
    if ref_type == "inline":
        return wrap_ref_inline(fmt, ref_text), ""
    if ref_type == "footnote":
        return format_ref_footnote(fmt, ref_text)
    return wrap_ref_inline(fmt, ref_text), ""


def format_typst(verses: List[Tuple[int, List[str], bool, List[str]]], style: str = 'table',
                 options: str = '', verse_nums: str = 'dots', inline_notes: bool = False) -> str:
    """Format verses as Typst."""

    if style == 'table':
        rows = []
        for verse_num, lines, _, notes in verses:
            label = format_verse_label('typ', verse_num, verse_nums)
            for i, line in enumerate(lines):
                line_text = render_notes_in_text(process_text(line, 'typ', options), 'typ', notes, options, inline_notes)
                if i == 0:
                    if label:
                        rows.append(f'    [#text(size:11pt)[{label}]], [{line_text}],')
                    else:
                        rows.append(f'    [], [{line_text}],')
                else:
                    rows.append(f'    [], [{line_text}],')
            if not inline_notes:
                for _, (label, content, marker) in enumerate(notes, start=1):
                    rows.append(f'    [], [{format_note_text("typ", marker, label, content, options)}],')

        return '#table(columns: (auto, auto), stroke: none,\n' + '\n'.join(rows) + '\n)'
    else:
        # Simple format for docx export
        output = []
        for verse_num, lines, _, notes in verses:
            label = format_verse_label('typ', verse_num, verse_nums)
            verse_text = '\n'.join(render_notes_in_text(process_text(line, 'typ', options), 'typ', notes, options, inline_notes) for line in lines)
            if not inline_notes:
                note_text = '\n'.join(format_note_text("typ", marker, label, content, options)
                                      for _, (label, content, marker) in enumerate(notes, start=1))
                if note_text:
                    verse_text = f"{verse_text}\n{note_text}"
            prefix = f'#super[{label}] ' if label else ''
            output.append(f'{prefix}{verse_text}')
        return '\n\n'.join(output)


def format_latex(verses: List[Tuple[int, List[str], bool, List[str]]], options: str = '',
                 verse_nums: str = 'dots', inline_notes: bool = False) -> str:
    """Format verses as LaTeX with proper poetic structure."""

    output = []

    for verse_num, lines, _, notes in verses:
        label = format_verse_label('tex', verse_num, verse_nums)
        verse_marker = f'\\textsuperscript{{{label}}} ' if label else ''
        if len(lines) == 1:
            # Single line verse
            line_text = render_notes_in_text(process_text(lines[0], 'tex', options), 'tex', notes, options, inline_notes)
            output.append(f'{verse_marker}{line_text}')
        else:
            # Multi-line (poetic) verse
            verse_lines = []
            for i, line in enumerate(lines):
                line_text = render_notes_in_text(process_text(line, 'tex', options), 'tex', notes, options, inline_notes)
                if i == 0:
                    verse_lines.append(f'{verse_marker}{line_text}')
                else:
                    verse_lines.append(f'\\vin {line_text}')
            output.append('\\\\\n'.join(verse_lines))
        if not inline_notes:
            for _, (label, content, marker) in enumerate(notes, start=1):
                output.append(f'\\quad {format_note_text("tex", marker, label, content, options)}')

    # Wrap in verse environment for poetry
    has_poetry = any(len(lines) > 1 for _, lines, _, _ in verses)
    if has_poetry:
        return '\\begin{verse}\n' + '\\\\\n\n'.join(output) + '\n\\end{verse}'
    else:
        return '\n\n'.join(output)


def format_latex_simple(verses: List[Tuple[int, List[str], bool, List[str]]], options: str = '',
                        verse_nums: str = 'dots', inline_notes: bool = False) -> str:
    """Format verses as simple LaTeX (no verse environment)."""

    output = []

    for verse_num, lines, _, notes in verses:
        label = format_verse_label('tex', verse_num, verse_nums)
        verse_marker = f'\\textsuperscript{{{label}}} ' if label else ''
        verse_lines = []
        for i, line in enumerate(lines):
            line_text = render_notes_in_text(process_text(line, 'tex', options), 'tex', notes, options, inline_notes)
            if i == 0:
                verse_lines.append(f'{verse_marker}{line_text}')
            else:
                verse_lines.append(line_text)
        if not inline_notes:
            for _, (label, content, marker) in enumerate(notes, start=1):
                verse_lines.append(f'\\quad {format_note_text("tex", marker, label, content, options)}')
        output.append(' \\\\\n'.join(verse_lines))

    return ' \\\\\n\n'.join(output)


def format_markdown(verses: List[Tuple[int, List[str], bool, List[str]]], options: str = '',
                    verse_nums: str = 'dots', inline_notes: bool = False) -> str:
    """Format verses as Markdown with proper line breaks."""

    output = []

    for verse_num, lines, _, notes in verses:
        verse_lines = []
        for i, line in enumerate(lines):
            line_text = render_notes_in_text(process_text(line, 'md', options), 'md', notes, options, inline_notes)
            if i == 0:
                verse_lines.append(f'{format_verse_prefix("md", verse_num, verse_nums)}{line_text}')
            else:
                # Indent continuation lines
                verse_lines.append(f'    {line_text}')
        if not inline_notes:
            for _, (label, content, marker) in enumerate(notes, start=1):
                verse_lines.append(f'    {format_note_text("md", marker, label, content, options)}')
        output.append('\n'.join(verse_lines))

    return '\n\n'.join(output)


def format_markdown_simple(verses: List[Tuple[int, List[str], bool, List[str]]], options: str = '',
                           verse_nums: str = 'dots', inline_notes: bool = False) -> str:
    """Format verses as simple Markdown (using <br> for line breaks)."""

    output = []

    for verse_num, lines, _, notes in verses:
        verse_lines = []
        for i, line in enumerate(lines):
            line_text = render_notes_in_text(process_text(line, 'md', options), 'md', notes, options, inline_notes)
            if i == 0:
                verse_lines.append(f'{format_verse_prefix("md", verse_num, verse_nums)}{line_text}')
            else:
                verse_lines.append(line_text)
        if not inline_notes:
            for _, (label, content, marker) in enumerate(notes, start=1):
                verse_lines.append(format_note_text("md", marker, label, content, options))
        output.append('  \n'.join(verse_lines))  # Two spaces + newline = <br> in MD

    return '\n\n'.join(output)


def format_plain(verses: List[Tuple[int, List[str], bool, List[str]]], options: str = '',
                 verse_nums: str = 'dots', inline_notes: bool = False) -> str:
    output = []
    for verse_num, lines, _, notes in verses:
        verse_lines = []
        for i, line in enumerate(lines):
            line_text = render_notes_in_text(process_text(line, 'plain', options), 'plain', notes, options, inline_notes)
            if i == 0:
                verse_lines.append(f'{format_verse_prefix("plain", verse_num, verse_nums)}{line_text}')
            else:
                verse_lines.append(f'    {line_text}')
        if not inline_notes:
            for _, (label, content, marker) in enumerate(notes, start=1):
                note_text = format_note_text("plain", marker, label, content, options)
                verse_lines.append(f'    {note_text}')
        output.append('\n'.join(verse_lines))
    return '\n\n'.join(output)


def format_org(verses: List[Tuple[int, List[str], bool, List[str]]], options: str = '',
               verse_nums: str = 'dots', inline_notes: bool = False) -> str:
    """Format verses as Org-mode with proper poetic structure."""

    output = []

    for verse_num, lines, _, notes in verses:
        verse_lines = []
        for i, line in enumerate(lines):
            line_text = render_notes_in_text(process_text(line, 'org', options), 'org', notes, options, inline_notes)
            if i == 0:
                verse_lines.append(f'{format_verse_prefix("org", verse_num, verse_nums)}{line_text}')
            else:
                # Indent continuation lines
                verse_lines.append(f'   {line_text}')
        if not inline_notes:
            for _, (label, content, marker) in enumerate(notes, start=1):
                verse_lines.append(f'   {format_note_text("org", marker, label, content, options)}')
        output.append('\n'.join(verse_lines))

    return '\n\n'.join(output)


def format_org_verse(verses: List[Tuple[int, List[str], bool, List[str]]], options: str = '',
                     verse_nums: str = 'dots', inline_notes: bool = False) -> str:
    """Format verses as Org-mode using verse block for poetry."""

    output = []
    has_poetry = any(len(lines) > 1 for _, lines, _, _ in verses)

    for verse_num, lines, _, notes in verses:
        verse_lines = []
        for i, line in enumerate(lines):
            line_text = render_notes_in_text(process_text(line, 'org', options), 'org', notes, options, inline_notes)
            if i == 0:
                verse_lines.append(f'{format_verse_prefix("org", verse_num, verse_nums)}{line_text}')
            else:
                verse_lines.append(f'   {line_text}')
        if not inline_notes:
            for _, (label, content, marker) in enumerate(notes, start=1):
                verse_lines.append(f'   {format_note_text("org", marker, label, content, options)}')
        output.append('\n'.join(verse_lines))

    content = '\n\n'.join(output)

    if has_poetry:
        return f'#+BEGIN_VERSE\n{content}\n#+END_VERSE'
    else:
        return content


def main():
    parser = argparse.ArgumentParser(
        description='Convert diatheke HTML Bible output to various formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '-f', '--format',
        choices=['typ', 'typst', 'tex', 'latex', 'md', 'markdown', 'org', 'plain'],
        default='typ',
        help='Output format (default: typ)'
    )
    parser.add_argument(
        '--style',
        choices=['table', 'simple'],
        default='table',
        help='Output style: table (default) or simple'
    )
    parser.add_argument(
        '-o', '--options',
        help='Module option filters (e.g., fs, fnl)'
    )
    parser.add_argument(
        '-i', '--inline-notes',
        action='store_true',
        help='Render footnotes/crossrefs inline instead of under each verse'
    )
    parser.add_argument(
        '--ref-pos',
        choices=['start', 'end', 'none'],
        default='end',
        help='Reference position (default: end)'
    )
    parser.add_argument(
        '--ref-type',
        choices=['inline', 'footnote', 'combined'],
        default='inline',
        help='Reference type (default: inline)'
    )
    parser.add_argument(
        '--verse-nums',
        choices=['dots', 'colons', 'none'],
        default='dots',
        help='Verse numbering style (default: dots)'
    )
    parser.add_argument(
        '--book-style',
        choices=['full', 'abbr'],
        default='full',
        help='Book name style (default: full)'
    )
    parser.add_argument(
        '--version-abbrev',
        choices=['auto', 'none'],
        default='auto',
        help='Version abbreviation (default: auto)'
    )

    args = parser.parse_args()

    # Normalize format names
    fmt = args.format
    if fmt in ('typst', 'typ'):
        fmt = 'typ'
    elif fmt in ('latex', 'tex'):
        fmt = 'tex'
    elif fmt in ('markdown', 'md'):
        fmt = 'md'

    # Read HTML from stdin
    html_content = sys.stdin.read()
    if not html_content.strip():
        print("Error: No input received from stdin", file=sys.stderr)
        sys.exit(1)

    try:
        # Extract reference information
        _, _, _, module = extract_reference(html_content)

        verses_raw = parse_html_verses(html_content, inline_notes=args.inline_notes)

        if not verses_raw:
            print("Error: No verses found in input", file=sys.stderr)
            sys.exit(1)

        passages = group_passages(verses_raw)
        outputs = []
        combined_refs = []

        for book, chapter, verses in passages:
            if fmt == 'typ':
                passage_out = format_typst(verses, args.style, args.options or '', args.verse_nums, args.inline_notes)
            elif fmt == 'tex':
                if args.style == 'simple':
                    passage_out = format_latex_simple(verses, args.options or '', args.verse_nums, args.inline_notes)
                else:
                    passage_out = format_latex(verses, args.options or '', args.verse_nums, args.inline_notes)
            elif fmt == 'md':
                if args.style == 'simple':
                    passage_out = format_markdown_simple(verses, args.options or '', args.verse_nums, args.inline_notes)
                else:
                    passage_out = format_markdown(verses, args.options or '', args.verse_nums, args.inline_notes)
            elif fmt == 'org':
                if args.style == 'simple':
                    passage_out = format_org(verses, args.options or '', args.verse_nums, args.inline_notes)
                else:
                    passage_out = format_org_verse(verses, args.options or '', args.verse_nums, args.inline_notes)
            elif fmt == 'plain':
                passage_out = format_plain(verses, args.options or '', args.verse_nums, args.inline_notes)
            else:
                print(f"Error: Unknown format: {fmt}", file=sys.stderr)
                sys.exit(1)

            first_verse = str(verses[0][0])
            last_verse = str(verses[-1][0])
            verse_range = first_verse if first_verse == last_verse else f"{first_verse}-{last_verse}"

            if args.ref_type == "combined":
                ref_text = format_ref_text(book, chapter, verse_range, module, args.book_style, args.version_abbrev)
                if ref_text:
                    combined_refs.append(ref_text)
            elif args.ref_pos != "none":
                ref_inline, ref_footer = build_reference_block(
                    book, chapter, verse_range, module, fmt,
                    args.book_style, args.version_abbrev, args.ref_type
                )
                if ref_inline:
                    if args.ref_pos == "start":
                        passage_out = f"{ref_inline}\n{passage_out}"
                    else:
                        passage_out = f"{passage_out}\n{ref_inline}"
                if ref_footer:
                    passage_out = f"{passage_out}\n{ref_footer}"

            outputs.append(passage_out)

        output = "\n\n".join(outputs)

        if args.ref_type == "combined" and args.ref_pos != "none":
            combined_text = "; ".join(combined_refs)
            if combined_text:
                ref_inline, ref_footer = build_reference_block_from_text(combined_text, fmt, "inline")
                if ref_inline:
                    if args.ref_pos == "start":
                        output = f"{ref_inline}\n{output}"
                    else:
                        output = f"{output}\n{ref_inline}"
                if ref_footer:
                    output = f"{output}\n{ref_footer}"

        print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
