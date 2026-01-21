#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bible-format-wrapper.py — Centralized Bible formatting wrapper
=============================================================

A wrapper around dutch-diatheke.py that provides consistent formatting
across different Bible version scripts (svv, hsv, esv, etc.)

Features:
- Show verse numbers only when multiple verses are requested
- Add formatted Bible references at the end of passages
- Support different abbreviation styles per Bible version
- Configurable reference formatting (full/abbreviated, with/without version)
- Configurable output formatting

Usage:
    bible-format-wrapper.py -b MODULE [OPTIONS] REFERENCE

Reference Format Options:
    --reference-style full-with-version      # Mattheüs 22:8 SV (default)
    --reference-style full-no-version        # Mattheüs 22:8
    --reference-style abbreviated-with-version # Matt. 22:8 SV
    --reference-style abbreviated-no-version   # Matt. 22:8

Examples:
    bible-format-wrapper.py -b DutSVV "Luk 19:5"                          # (Lukas 19:5 SV)
    bible-format-wrapper.py -b DutSVV "Luk 19:5-6"                        # Multiple verses with numbers
    bible-format-wrapper.py -b HSV -r abbreviated-with-version "Johannes 3:16"  # (Joh. 3:16 HSV)
    bible-format-wrapper.py -b DutSVV -r full-no-version "Mattheüs 22:8"       # (Matthew 22:8)
    bible-format-wrapper.py -b ESV -r abbreviated-no-version "John 3:16"        # (John 3:16)
"""

import sys
import re
import argparse
import subprocess
import os
from typing import Dict, List, Tuple, Optional

__version__ = "1.0.0"

# Bible version configurations
BIBLE_CONFIGS = {
    'DutSVV': {
        'tag': 'SV',
        'dutch_names': {
            # Full Dutch book names
            "Genesis": "Genesis", "Exodus": "Exodus", "Leviticus": "Leviticus", "Numbers": "Numeri",
            "Deuteronomy": "Deuteronomium", "Joshua": "Jozua", "Judges": "Richteren", "Ruth": "Ruth",
            "1Samuel": "1 Samuel", "2Samuel": "2 Samuel", "I Samuel": "1 Samuel", "II Samuel": "2 Samuel",
            "1Kings": "1 Koningen", "2Kings": "2 Koningen", "I Kings": "1 Koningen", "II Kings": "2 Koningen",
            "1Chronicles": "1 Kronieken", "2Chronicles": "2 Kronieken", "I Chronicles": "1 Kronieken", "II Chronicles": "2 Kronieken",
            "Ezra": "Ezra", "Nehemiah": "Nehemia", "Esther": "Ester", "Job": "Job",
            "Psalms": "Psalmen", "Proverbs": "Spreuken", "Ecclesiastes": "Prediker", "Song of Songs": "Hooglied",
            "Isaiah": "Jesaja", "Jeremiah": "Jeremia", "Lamentations": "Klaagliederen", "Ezekiel": "Ezechiël",
            "Daniel": "Daniël", "Hosea": "Hosea", "Joel": "Joël", "Amos": "Amos",
            "Obadiah": "Obadja", "Jonah": "Jona", "Micah": "Micha", "Nahum": "Nahum",
            "Habakkuk": "Habakuk", "Zephaniah": "Sefanja", "Haggai": "Haggaï", "Zechariah": "Zacharia", "Malachi": "Maleachi",
            "Matthew": "Mattheüs", "Mark": "Marcus", "Luke": "Lucas", "John": "Johannes",
            "Acts": "Handelingen", "Romans": "Romeinen",
            "1Corinthians": "1 Korinthe", "2Corinthians": "2 Korinthe", "I Corinthians": "1 Korinthe", "II Corinthians": "2 Korinthe",
            "Galatians": "Galaten", "Ephesians": "Efeze", "Philippians": "Filippenzen", "Colossians": "Kolossenzen",
            "1Thessalonians": "1 Thessalonicenzen", "2Thessalonians": "2 Thessalonicenzen", "I Thessalonians": "1 Thessalonicenzen", "II Thessalonians": "2 Thessalonicenzen",
            "1Timothy": "1 Timoteüs", "2Timothy": "2 Timoteüs", "I Timothy": "1 Timoteüs", "II Timothy": "2 Timoteüs",
            "Titus": "Titus", "Philemon": "Filemon", "Hebrews": "Hebreeën", "James": "Jakobus",
            "1Peter": "1 Petrus", "2Peter": "2 Petrus", "I Peter": "1 Petrus", "II Peter": "2 Petrus",
            "1John": "1 Johannes", "2John": "2 Johannes", "3John": "3 Johannes", "I John": "1 Johannes", "II John": "2 Johannes", "III John": "3 Johannes",
            "Jude": "Judas", "Revelation": "Openbaring"
        },
        'abbreviations': {
            "Genesis": "Gen.", "Exodus": "Ex.", "Leviticus": "Lev.", "Numbers": "Num.",
            "Deuteronomy": "Deut.", "Joshua": "Joz.", "Judges": "Richt.", "Ruth": "Ruth",
            "1Samuel": "1 Sam.", "2Samuel": "2 Sam.", "I Samuel": "1 Sam.", "II Samuel": "2 Sam.",
            "1Kings": "1 Kon.", "2Kings": "2 Kon.", "I Kings": "1 Kon.", "II Kings": "2 Kon.",
            "1Chronicles": "1 Kron.", "2Chronicles": "2 Kron.", "I Chronicles": "1 Kron.", "II Chronicles": "2 Kron.",
            "Ezra": "Ezra", "Nehemiah": "Neh.", "Esther": "Est.", "Job": "Job",
            "Psalms": "Ps.", "Proverbs": "Spr.", "Ecclesiastes": "Pred.", "Song of Songs": "Hoogl.",
            "Isaiah": "Jes.", "Jeremiah": "Jer.", "Lamentations": "Klaagl.", "Ezekiel": "Ez.",
            "Daniel": "Dan.", "Hosea": "Hos.", "Joel": "Joël", "Amos": "Am.",
            "Obadiah": "Ob.", "Jonah": "Jona", "Micah": "Micha", "Nahum": "Nah.",
            "Habakkuk": "Hab.", "Zephaniah": "Zef.", "Haggai": "Hag.", "Zechariah": "Zach.", "Malachi": "Mal.",
            "Matthew": "Matt.", "Mark": "Mark", "Luke": "Luk.", "John": "Joh.",
            "Acts": "Hand.", "Romans": "Rom.",
            "1Corinthians": "1 Kor.", "2Corinthians": "2 Kor.", "I Corinthians": "1 Kor.", "II Corinthians": "2 Kor.",
            "Galatians": "Gal.", "Ephesians": "Ef.", "Philippians": "Fil.", "Colossians": "Kol.",
            "1Thessalonians": "1 Thess.", "2Thessalonians": "2 Thess.", "I Thessalonians": "1 Thess.", "II Thessalonians": "2 Thess.",
            "1Timothy": "1 Tim.", "2Timothy": "2 Tim.", "I Timothy": "1 Tim.", "II Timothy": "2 Tim.",
            "Titus": "Tit.", "Philemon": "Filem.", "Hebrews": "Hebr.", "James": "Jak.",
            "1Peter": "1 Petr.", "2Peter": "2 Petr.", "I Peter": "1 Petr.", "II Peter": "2 Petr.",
            "1John": "1 Joh.", "2John": "2 Joh.", "3John": "3 Joh.", "I John": "1 Joh.", "II John": "2 Joh.", "III John": "3 Joh.",
            "Jude": "Judas", "Revelation": "Openb."
        }
    },
    'HSV': {
        'tag': 'HSV',
        'dutch_names': {
            # Full Dutch book names (same as SV)
            "Genesis": "Genesis", "Exodus": "Exodus", "Leviticus": "Leviticus", "Numbers": "Numeri",
            "Deuteronomy": "Deuteronomium", "Joshua": "Jozua", "Judges": "Richteren", "Ruth": "Ruth",
            "1Samuel": "1 Samuel", "2Samuel": "2 Samuel", "I Samuel": "1 Samuel", "II Samuel": "2 Samuel",
            "1Kings": "1 Koningen", "2Kings": "2 Koningen", "I Kings": "1 Koningen", "II Kings": "2 Koningen",
            "1Chronicles": "1 Kronieken", "2Chronicles": "2 Kronieken", "I Chronicles": "1 Kronieken", "II Chronicles": "2 Kronieken",
            "Ezra": "Ezra", "Nehemiah": "Nehemia", "Esther": "Ester", "Job": "Job",
            "Psalms": "Psalmen", "Proverbs": "Spreuken", "Ecclesiastes": "Prediker", "Song of Songs": "Hooglied",
            "Isaiah": "Jesaja", "Jeremiah": "Jeremia", "Lamentations": "Klaagliederen", "Ezekiel": "Ezechiël",
            "Daniel": "Daniël", "Hosea": "Hosea", "Joel": "Joël", "Amos": "Amos",
            "Obadiah": "Obadja", "Jonah": "Jona", "Micah": "Micha", "Nahum": "Nahum",
            "Habakkuk": "Habakuk", "Zephaniah": "Sefanja", "Haggai": "Haggaï", "Zechariah": "Zacharia", "Malachi": "Maleachi",
            "Matthew": "Mattheüs", "Mark": "Marcus", "Luke": "Lucas", "John": "Johannes",
            "Acts": "Handelingen", "Romans": "Romeinen",
            "1Corinthians": "1 Korinthe", "2Corinthians": "2 Korinthe", "I Corinthians": "1 Korinthe", "II Corinthians": "2 Korinthe",
            "Galatians": "Galaten", "Ephesians": "Efeze", "Philippians": "Filippenzen", "Colossians": "Kolossenzen",
            "1Thessalonians": "1 Thessalonicenzen", "2Thessalonians": "2 Thessalonicenzen", "I Thessalonians": "1 Thessalonicenzen", "II Thessalonians": "2 Thessalonicenzen",
            "1Timothy": "1 Timoteüs", "2Timothy": "2 Timoteüs", "I Timothy": "1 Timoteüs", "II Timothy": "2 Timoteüs",
            "Titus": "Titus", "Philemon": "Filemon", "Hebrews": "Hebreeën", "James": "Jakobus",
            "1Peter": "1 Petrus", "2Peter": "2 Petrus", "I Peter": "1 Petrus", "II Peter": "2 Petrus",
            "1John": "1 Johannes", "2John": "2 Johannes", "3John": "3 Johannes", "I John": "1 Johannes", "II John": "2 Johannes", "III John": "3 Johannes",
            "Jude": "Judas", "Revelation": "Openbaring"
        },
        'abbreviations': {
            # Use same abbreviations as SV
            "Genesis": "Gen.", "Exodus": "Ex.", "Leviticus": "Lev.", "Numbers": "Num.",
            "Deuteronomy": "Deut.", "Joshua": "Joz.", "Judges": "Richt.", "Ruth": "Ruth",
            "1Samuel": "1 Sam.", "2Samuel": "2 Sam.", "I Samuel": "1 Sam.", "II Samuel": "2 Sam.",
            "1Kings": "1 Kon.", "2Kings": "2 Kon.", "I Kings": "1 Kon.", "II Kings": "2 Kon.",
            "1Chronicles": "1 Kron.", "2Chronicles": "2 Kron.", "I Chronicles": "1 Kron.", "II Chronicles": "2 Kron.",
            "Ezra": "Ezra", "Nehemiah": "Neh.", "Esther": "Est.", "Job": "Job",
            "Psalms": "Ps.", "Proverbs": "Spr.", "Ecclesiastes": "Pred.", "Song of Songs": "Hoogl.",
            "Isaiah": "Jes.", "Jeremiah": "Jer.", "Lamentations": "Klaagl.", "Ezekiel": "Ez.",
            "Daniel": "Dan.", "Hosea": "Hos.", "Joel": "Joël", "Amos": "Am.",
            "Obadiah": "Ob.", "Jonah": "Jona", "Micah": "Micha", "Nahum": "Nah.",
            "Habakkuk": "Hab.", "Zephaniah": "Zef.", "Haggai": "Hag.", "Zechariah": "Zach.", "Malachi": "Mal.",
            "Matthew": "Matt.", "Mark": "Mark", "Luke": "Luk.", "John": "Joh.",
            "Acts": "Hand.", "Romans": "Rom.",
            "1Corinthians": "1 Kor.", "2Corinthians": "2 Kor.", "I Corinthians": "1 Kor.", "II Corinthians": "2 Kor.",
            "Galatians": "Gal.", "Ephesians": "Ef.", "Philippians": "Fil.", "Colossians": "Kol.",
            "1Thessalonians": "1 Thess.", "2Thessalonians": "2 Thess.", "I Thessalonians": "1 Thess.", "II Thessalonians": "2 Thess.",
            "1Timothy": "1 Tim.", "2Timothy": "2 Tim.", "I Timothy": "1 Tim.", "II Timothy": "2 Tim.",
            "Titus": "Tit.", "Philemon": "Filem.", "Hebrews": "Hebr.", "James": "Jak.",
            "1Peter": "1 Petr.", "2Peter": "2 Petr.", "I Peter": "1 Petr.", "II Peter": "2 Petr.",
            "1John": "1 Joh.", "2John": "2 Joh.", "3John": "3 Joh.", "I John": "1 Joh.", "II John": "2 Joh.", "III John": "3 Joh.",
            "Jude": "Judas", "Revelation": "Openb."
        }
    },
    'ESV': {
        'tag': 'ESV',
        'dutch_names': None,  # ESV uses English names
        'abbreviations': {
            # English abbreviations for ESV
            "Genesis": "Gen.", "Exodus": "Ex.", "Leviticus": "Lev.", "Numbers": "Num.",
            "Deuteronomy": "Deut.", "Joshua": "Josh.", "Judges": "Judg.", "Ruth": "Ruth",
            "1Samuel": "1 Sam.", "2Samuel": "2 Sam.", "I Samuel": "1 Sam.", "II Samuel": "2 Sam.",
            "1Kings": "1 Kings", "2Kings": "2 Kings", "I Kings": "1 Kings", "II Kings": "2 Kings",
            "1Chronicles": "1 Chron.", "2Chronicles": "2 Chron.", "I Chronicles": "1 Chron.", "II Chronicles": "2 Chron.",
            "Ezra": "Ezra", "Nehemiah": "Neh.", "Esther": "Esth.", "Job": "Job",
            "Psalms": "Ps.", "Proverbs": "Prov.", "Ecclesiastes": "Eccl.", "Song of Songs": "Song",
            "Isaiah": "Isa.", "Jeremiah": "Jer.", "Lamentations": "Lam.", "Ezekiel": "Ezek.",
            "Daniel": "Dan.", "Hosea": "Hos.", "Joel": "Joel", "Amos": "Amos",
            "Obadiah": "Obad.", "Jonah": "Jonah", "Micah": "Mic.", "Nahum": "Nah.",
            "Habakkuk": "Hab.", "Zephaniah": "Zeph.", "Haggai": "Hag.", "Zechariah": "Zech.", "Malachi": "Mal.",
            "Matthew": "Matt.", "Mark": "Mark", "Luke": "Luke", "John": "John",
            "Acts": "Acts", "Romans": "Rom.",
            "1Corinthians": "1 Cor.", "2Corinthians": "2 Cor.", "I Corinthians": "1 Cor.", "II Corinthians": "2 Cor.",
            "Galatians": "Gal.", "Ephesians": "Eph.", "Philippians": "Phil.", "Colossians": "Col.",
            "1Thessalonians": "1 Thess.", "2Thessalonians": "2 Thess.", "I Thessalonians": "1 Thess.", "II Thessalonians": "2 Thess.",
            "1Timothy": "1 Tim.", "2Timothy": "2 Tim.", "I Timothy": "1 Tim.", "II Timothy": "2 Tim.",
            "Titus": "Titus", "Philemon": "Phlm.", "Hebrews": "Heb.", "James": "James",
            "1Peter": "1 Pet.", "2Peter": "2 Pet.", "I Peter": "1 Pet.", "II Peter": "2 Pet.",
            "1John": "1 John", "2John": "2 John", "3John": "3 John", "I John": "1 John", "II John": "2 John", "III John": "3 John",
            "Jude": "Jude", "Revelation": "Rev."
        }
    },
    'NBV21': {
        'tag': 'NBV21',
        'dutch_names': {
            # Full Dutch book names (same as SV/HSV)
            "Genesis": "Genesis", "Exodus": "Exodus", "Leviticus": "Leviticus", "Numbers": "Numeri",
            "Deuteronomy": "Deuteronomium", "Joshua": "Jozua", "Judges": "Richteren", "Ruth": "Ruth",
            "1Samuel": "1 Samuel", "2Samuel": "2 Samuel", "I Samuel": "1 Samuel", "II Samuel": "2 Samuel",
            "1Kings": "1 Koningen", "2Kings": "2 Koningen", "I Kings": "1 Koningen", "II Kings": "2 Koningen",
            "1Chronicles": "1 Kronieken", "2Chronicles": "2 Kronieken", "I Chronicles": "1 Kronieken", "II Chronicles": "2 Kronieken",
            "Ezra": "Ezra", "Nehemiah": "Nehemia", "Esther": "Ester", "Job": "Job",
            "Psalms": "Psalmen", "Proverbs": "Spreuken", "Ecclesiastes": "Prediker", "Song of Songs": "Hooglied",
            "Isaiah": "Jesaja", "Jeremiah": "Jeremia", "Lamentations": "Klaagliederen", "Ezekiel": "Ezechiël",
            "Daniel": "Daniël", "Hosea": "Hosea", "Joel": "Joël", "Amos": "Amos",
            "Obadiah": "Obadja", "Jonah": "Jona", "Micah": "Micha", "Nahum": "Nahum",
            "Habakkuk": "Habakuk", "Zephaniah": "Sefanja", "Haggai": "Haggaï", "Zechariah": "Zacharia", "Malachi": "Maleachi",
            "Matthew": "Mattheüs", "Mark": "Marcus", "Luke": "Lucas", "John": "Johannes",
            "Acts": "Handelingen", "Romans": "Romeinen",
            "1Corinthians": "1 Korinthe", "2Corinthians": "2 Korinthe", "I Corinthians": "1 Korinthe", "II Corinthians": "2 Korinthe",
            "Galatians": "Galaten", "Ephesians": "Efeze", "Philippians": "Filippenzen", "Colossians": "Kolossenzen",
            "1Thessalonians": "1 Thessalonicenzen", "2Thessalonians": "2 Thessalonicenzen", "I Thessalonians": "1 Thessalonicenzen", "II Thessalonians": "2 Thessalonicenzen",
            "1Timothy": "1 Timoteüs", "2Timothy": "2 Timoteüs", "I Timothy": "1 Timoteüs", "II Timothy": "2 Timoteüs",
            "Titus": "Titus", "Philemon": "Filemon", "Hebrews": "Hebreeën", "James": "Jakobus",
            "1Peter": "1 Petrus", "2Peter": "2 Petrus", "I Peter": "1 Petrus", "II Peter": "2 Petrus",
            "1John": "1 Johannes", "2John": "2 Johannes", "3John": "3 Johannes", "I John": "1 Johannes", "II John": "2 Johannes", "III John": "3 Johannes",
            "Jude": "Judas", "Revelation": "Openbaring"
        },
        'abbreviations': {
            # Use same abbreviations as SV
            "Genesis": "Gen.", "Exodus": "Ex.", "Leviticus": "Lev.", "Numbers": "Num.",
            "Deuteronomy": "Deut.", "Joshua": "Joz.", "Judges": "Richt.", "Ruth": "Ruth",
            "1Samuel": "1 Sam.", "2Samuel": "2 Sam.", "I Samuel": "1 Sam.", "II Samuel": "2 Sam.",
            "1Kings": "1 Kon.", "2Kings": "2 Kon.", "I Kings": "1 Kon.", "II Kings": "2 Kon.",
            "1Chronicles": "1 Kron.", "2Chronicles": "2 Kron.", "I Chronicles": "1 Kron.", "II Chronicles": "2 Kron.",
            "Ezra": "Ezra", "Nehemiah": "Neh.", "Esther": "Est.", "Job": "Job",
            "Psalms": "Ps.", "Proverbs": "Spr.", "Ecclesiastes": "Pred.", "Song of Songs": "Hoogl.",
            "Isaiah": "Jes.", "Jeremiah": "Jer.", "Lamentations": "Klaagl.", "Ezekiel": "Ez.",
            "Daniel": "Dan.", "Hosea": "Hos.", "Joel": "Joël", "Amos": "Am.",
            "Obadiah": "Ob.", "Jonah": "Jona", "Micah": "Micha", "Nahum": "Nah.",
            "Habakkuk": "Hab.", "Zephaniah": "Zef.", "Haggai": "Hag.", "Zechariah": "Zach.", "Malachi": "Mal.",
            "Matthew": "Matt.", "Mark": "Mark", "Luke": "Luk.", "John": "Joh.",
            "Acts": "Hand.", "Romans": "Rom.",
            "1Corinthians": "1 Kor.", "2Corinthians": "2 Kor.", "I Corinthians": "1 Kor.", "II Corinthians": "2 Kor.",
            "Galatians": "Gal.", "Ephesians": "Ef.", "Philippians": "Fil.", "Colossians": "Kol.",
            "1Thessalonians": "1 Thess.", "2Thessalonians": "2 Thess.", "I Thessalonians": "1 Thess.", "II Thessalonians": "2 Thess.",
            "1Timothy": "1 Tim.", "2Timothy": "2 Tim.", "I Timothy": "1 Tim.", "II Timothy": "2 Tim.",
            "Titus": "Tit.", "Philemon": "Filem.", "Hebrews": "Hebr.", "James": "Jak.",
            "1Peter": "1 Petr.", "2Peter": "2 Petr.", "I Peter": "1 Petr.", "II Peter": "2 Petr.",
            "1John": "1 Joh.", "2John": "2 Joh.", "3John": "3 Joh.", "I John": "1 Joh.", "II John": "2 Joh.", "III John": "3 Joh.",
            "Jude": "Judas", "Revelation": "Openb."
        }
    }
}

def find_module_conf(module: str) -> str:
    """Find the SWORD .conf file for a module."""
    paths = [
        os.path.expanduser("~/.sword/mods.d"),
        "/usr/share/sword/mods.d",
    ]
    for base in paths:
        if not os.path.isdir(base):
            continue
        for filename in os.listdir(base):
            if not filename.endswith(".conf"):
                continue
            conf_path = os.path.join(base, filename)
            try:
                with open(conf_path, "r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        if line.strip() == f"[{module}]":
                            return conf_path
            except OSError:
                continue
    return ""


def find_module_lang(module: str) -> str:
    """Read Lang= from module .conf if available."""
    conf_path = find_module_conf(module)
    if not conf_path:
        return ""
    try:
        with open(conf_path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if line.startswith("Lang="):
                    return line.split("=", 1)[1].strip().lower()
    except OSError:
        return ""
    return ""


def get_config(module: str) -> Dict:
    """Get configuration for a Bible module."""
    if module in BIBLE_CONFIGS:
        return BIBLE_CONFIGS[module]

    lang = find_module_lang(module)
    if lang.startswith("nl") or lang.startswith("dut"):
        return BIBLE_CONFIGS['DutSVV']

    return {
        "tag": module,
        "dutch_names": None,
        "abbreviations": {},
    }

def convert_book_name(book: str, config: Dict, use_dutch_names: bool = False) -> str:
    """Convert English book name to localized name or abbreviation."""
    if use_dutch_names and config.get('dutch_names'):
        # Use Dutch full names
        return config['dutch_names'].get(book, book)
    else:
        # Use abbreviations
        return config['abbreviations'].get(book, book)

def parse_diatheke_output(output: str, module: str, output_format: str = 'plain',
                          options: str = '') -> List[Tuple[str, str, str, str, List[str]]]:
    """
    Parse diatheke output into structured data, handling XML markup for poetic formatting.
    Returns list of (book, chapter, first_verse, last_verse, verse_lines)
    """
    config = get_config(module)
    passages = []
    current_passage = None
    current_verse_parts = []  # To accumulate text for current verse
    current_verse_info = None  # Current verse being processed

    lines = output.strip().split('\n')

    def process_verse_text(text: str, output_format: str = 'plain', options: str = '') -> str:
        """Process XML markup in verse text to create proper poetic formatting."""
        if not text:
            return ""

        def render_w_tags(src: str, options: str) -> str:
            if not options:
                return re.sub(r'</?w[^>]*>', '', src)

            want_strongs = 'n' in options
            want_lemmas = 'l' in options
            want_morph = ('m' in options) or ('M' in options)

            def repl(match: re.Match) -> str:
                attrs = match.group(1)
                content = match.group(2)
                annotations = []

                if want_strongs:
                    strongs = re.findall(r'strong:([A-Za-z0-9]+)', attrs)
                    if strongs:
                        annotations.append("Str " + ",".join(strongs))

                if want_lemmas:
                    lemmas = re.findall(r'lemma\.[^:]+:([^\s"]+)', attrs)
                    if lemmas:
                        annotations.append("Lemma " + ",".join(lemmas))

                if want_morph:
                    morphs = re.findall(r'morph:([^\s"]+)', attrs)
                    if morphs:
                        annotations.append("Morph " + ",".join(morphs))

                if annotations:
                    return f"{content} [{' | '.join(annotations)}]"
                return content

            return re.sub(r'<w\b([^>]*)>(.*?)</w>', repl, src)

        # Remove empty note tags (cross-references and footnotes with no content)
        text = re.sub(r'<note[^>]*/>\s*', '', text)
        text = re.sub(r'<note[^>]*></note>\s*', '', text)

        # Handle small-caps HEERE based on output format
        if output_format.lower() == 'plain':
            # For plain text, just remove the markup and keep the text
            text = re.sub(r'<hi type="small-caps">([^<]+)</hi>', r'\1', text)
            # Drop superscript markers (footnote refs) in plain output
            text = re.sub(r'<hi type="super">([^<]+)</hi>', r'', text)
        else:
            # For other formats, use asterisks for now (could be customized per format)
            text = re.sub(r'<hi type="small-caps">([^<]+)</hi>', r'*\1*', text)

        # Remove chapter markers and other structural XML
        text = re.sub(r'<chapter[^>]*/?>', '', text)

        # Render or strip OSIS word-level markup (lemmas/strongs/morph, etc.)
        text = render_w_tags(text, options)

        # Render notes as inline brackets
        text = re.sub(r'<note[^>]*>(.*?)</note>', r'[\1]', text)

        # Convert XML line markers to actual line breaks
        # Only add newline when <l sID> directly follows <l eID> (with only whitespace between)
        # Pattern: </l eID="..."/> [whitespace] <l sID="..."/> should become newline
        text = re.sub(r'<l eID="[^"]*"/>\s*<l sID="[^"]*"/>', '\n', text)

        # Remove remaining line markers
        text = re.sub(r'<l [se]ID="[^"]*"/>', '', text)

        # Strip any remaining OSIS/XML tags for plain output
        text = re.sub(r'<[^>]+>', '', text)

        # Clean up extra whitespace but preserve intentional line breaks
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)

        return '\n'.join(lines)

    def finalize_current_verse():
        """Finalize the current verse by processing XML and preserving poetic formatting."""
        nonlocal current_verse_parts, current_verse_info, current_passage

        if current_verse_info and current_verse_parts:
            verse_num, book, chapter = current_verse_info
            # Process each part for XML markup first, then join with spaces
            processed_parts = []
            for part in current_verse_parts:
                processed_part = process_verse_text(part, output_format, options)
                if processed_part:
                    processed_parts.append(processed_part)

            # Join processed parts - use newline if any part contains newlines, else use space
            if any('\n' in part for part in processed_parts):
                formatted_text = '\n'.join(processed_parts)
            else:
                formatted_text = ' '.join(processed_parts)

            if formatted_text:  # Only add non-empty verses
                # Check if this starts a new passage
                if (current_passage is None or
                    current_passage[0] != book or
                    current_passage[1] != chapter):

                    # Finalize previous passage
                    if current_passage:
                        passages.append(current_passage)

                    # Start new passage
                    current_passage = [book, chapter, verse_num, verse_num, []]

                # Add verse to current passage
                current_passage[4].append((verse_num, formatted_text))
                current_passage[3] = verse_num  # Update last verse

        # Reset current verse
        current_verse_parts = []
        current_verse_info = None

    for line in lines:
        line = line.strip()

        if line == f"({module})":
            # End marker - finalize everything
            finalize_current_verse()
            if current_passage:
                passages.append(current_passage)
                current_passage = None
            continue

        if not line:
            # Empty line - continue accumulating current verse
            continue

        # Match verse pattern: Book Chapter:Verse: Text (text might be empty)
        match = re.match(r'^(.+)\s+(\d+):(\d+):\s*(.*)$', line)
        if match:
            # This is a new verse - finalize previous verse first
            finalize_current_verse()

            book, chapter, verse, text = match.groups()
            text = text.strip()

            # Start new verse
            current_verse_info = (verse, book, chapter)
            current_verse_parts = [text] if text else []
        else:
            # This is continuation text for the current verse
            if current_verse_info:
                # Add this line to current verse parts
                if line:  # Only add non-empty lines
                    current_verse_parts.append(line)

    # Handle any remaining verse and passage
    finalize_current_verse()
    if current_passage:
        passages.append(current_passage)

    return passages

def format_passage(book: str, chapter: str, first_verse: str, last_verse: str,
                  verse_lines: List[Tuple[str, str]], config: Dict,
                  reference_style: str = 'full-with-version') -> str:
    """Format a single passage with appropriate verse numbering and reference."""
    output_lines = []

    # Determine if we should show verse numbers
    show_verse_numbers = (first_verse != last_verse)

    # Format verse content
    for verse_num, text in verse_lines:
        if show_verse_numbers:
            output_lines.append(f"{verse_num}. {text}")
        else:
            output_lines.append(text)

    # Determine if we should use Dutch names (for Dutch Bible versions)
    use_dutch_names = config.get('dutch_names') is not None

    # Add reference based on style
    if reference_style == 'full-with-version':
        # Default: Mattheüs 22:8 SV (Dutch) or Matthew 22:8 ESV (English)
        book_name = convert_book_name(book, config, use_dutch_names=use_dutch_names)
        version_tag = f" {config['tag']}"
    elif reference_style == 'full-no-version':
        # Mattheüs 22:8 (Dutch) or Matthew 22:8 (English)
        book_name = convert_book_name(book, config, use_dutch_names=use_dutch_names)
        version_tag = ""
    elif reference_style == 'abbreviated-with-version':
        # Matt. 22:8 SV
        book_name = convert_book_name(book, config, use_dutch_names=False)  # Always use abbreviations
        version_tag = f" {config['tag']}"
    elif reference_style == 'abbreviated-no-version':
        # Matt. 22:8
        book_name = convert_book_name(book, config, use_dutch_names=False)  # Always use abbreviations
        version_tag = ""
    else:
        # Fallback to default
        book_name = convert_book_name(book, config, use_dutch_names=use_dutch_names)
        version_tag = f" {config['tag']}"

    if first_verse == last_verse:
        reference = f"({book_name} {chapter}:{first_verse}{version_tag})"
    else:
        # Check if verses are consecutive
        verse_nums = [int(v[0]) for v in verse_lines]
        is_consecutive = all(verse_nums[i] + 1 == verse_nums[i + 1] for i in range(len(verse_nums) - 1))

        if is_consecutive:
            # Show as range: Ex 9:9-11
            reference = f"({book_name} {chapter}:{first_verse}-{last_verse}{version_tag})"
        else:
            # Show individual verses: Ex 9:9,25
            verse_list = ','.join(v[0] for v in verse_lines)
            reference = f"({book_name} {chapter}:{verse_list}{version_tag})"

    output_lines.append(reference)

    return '\n'.join(output_lines)

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Bible formatting wrapper around dutch-diatheke.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('-b', '--module', required=True,
                       help='Bible module (DutSVV, HSV, ESV, etc.)')
    parser.add_argument('-f', '--format', default='plain',
                       help='Output format (default: plain)')
    parser.add_argument('-r', '--reference-style', default='full-with-version',
                       choices=['full-with-version', 'full-no-version', 
                               'abbreviated-with-version', 'abbreviated-no-version'],
                       help='Reference format style (default: full-with-version)')
    parser.add_argument('-o', '--options',
                       help='Module option filters (e.g., fr, m, cv)')
    parser.add_argument('--raw', action='store_true',
                       help='Pass through raw output without formatting')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('reference', nargs='*',
                       help='Bible reference (e.g., "Johannes 3:16")')
    
    args = parser.parse_args()
    
    if not args.reference:
        parser.error("Bible reference is required")
    
    # Join reference parts
    reference = ' '.join(args.reference)
    
    # Call dutch-diatheke.py to convert the reference, but then use diatheke directly
    # to get the XML markup for proper poetic formatting
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dutch_diatheke_path = os.path.join(script_dir, 'dutch-diatheke.py')

    # First get the English reference from dutch-diatheke.py
    cmd = [dutch_diatheke_path, '--dry-run', '-b', args.module, reference]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Extract the diatheke command that would be run
        cmd_line = None
        for line in result.stdout.split('\n'):
            if line.startswith('[CMD] '):
                cmd_line = line[6:]  # Remove '[CMD] ' prefix
                break

        if not cmd_line:
            raise RuntimeError("Could not extract diatheke command from dutch-diatheke.py")

        # Parse the command to get the English reference
        cmd_parts = cmd_line.split()
        if '-k' in cmd_parts:
            k_index = cmd_parts.index('-k')
            if k_index + 1 < len(cmd_parts):
                english_reference = ' '.join(cmd_parts[k_index + 1:])
            else:
                raise RuntimeError("Invalid diatheke command format")
        else:
            raise RuntimeError("No -k parameter found in diatheke command")

        # Now call diatheke directly with the requested format
        # For plain text we need XML to process poetic formatting, for others use the requested format
        cmd = ['diatheke', '-b', args.module]
        if args.options:
            cmd.extend(['-o', args.options])
        if args.format.lower() != 'plain':
            cmd.extend(['-f', args.format])
        cmd.extend(['-k', english_reference])
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    except subprocess.CalledProcessError as e:
        if 'dutch-diatheke.py' in str(e):
            print(f"ERROR: dutch-diatheke.py failed: {e.stderr}", file=sys.stderr)
        else:
            print(f"ERROR: diatheke failed: {e.stderr}", file=sys.stderr)
        return e.returncode
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    try:
        
        if args.raw:
            # Just pass through the output
            print(result.stdout, end='')
        elif args.format.lower() == 'plain':
            # Parse and format the output for plain text (with XML processing)
            passages = parse_diatheke_output(result.stdout, args.module, args.format, args.options or "")
            config = get_config(args.module)

            formatted_passages = []
            for book, chapter, first_verse, last_verse, verse_lines in passages:
                formatted = format_passage(book, chapter, first_verse, last_verse,
                                         verse_lines, config, args.reference_style)
                formatted_passages.append(formatted)

            # Output with blank lines between passages
            print('\n\n'.join(formatted_passages))
        else:
            # For non-plain formats, just pass through (they're already formatted by diatheke)
            print(result.stdout, end='')
            
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: dutch-diatheke.py failed: {e.stderr}", file=sys.stderr)
        return e.returncode
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
