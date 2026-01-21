#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dutch-diatheke.py — Unified Dutch/English Bible Reference Wrapper for Diatheke
===============================================================================

A comprehensive wrapper that allows using both Dutch and English Bible book names 
and abbreviations with the diatheke Bible study tool. This script combines and 
improves upon the functionality from bijbel-wrapper.py and nbible.py.

Usage:
    dutch-diatheke.py [OPTIONS] "REFERENCE"
    cat references.txt | dutch-diatheke.py [OPTIONS]

Examples:
    dutch-diatheke.py -b HSV "Johannes 3:16"    # Dutch name
    dutch-diatheke.py -b HSV "John 3:16"        # English name  
    dutch-diatheke.py -b DutSVV "1 Kor 13:4-7"  # Dutch abbreviation
    dutch-diatheke.py -b DutSVV "1Cor 13:4-7"   # English abbreviation
    dutch-diatheke.py --format HTML "Judges 6:12" # English name
    dutch-diatheke.py --format HTML "Richteren 6:12" # Dutch equivalent
    echo "Spreuken 3:5-6" | dutch-diatheke.py -b HSV

Options:
    -b, --module MODULE     SWORD/Diatheke Bible module (default: HSV)
    -f, --format FORMAT     Output format: plain, HTML, RTF, etc. (default: plain)
    -k, --key REFERENCE     Bible reference (alternative to positional argument)
    --echo                  Show the diatheke command that will be executed
    --dry-run              Show the command but don't execute it
    --apocrypha            Include Deuterocanonical/Apocryphal books
    -h, --help             Show this help message
    -v, --version          Show version information

Features:
- Recognizes both Dutch and English names and abbreviations for all Bible books
- Supports both canonical and deuterocanonical books  
- Handles various abbreviation styles and case variations (ri, richt, Judges, judg, etc.)
- Removes diacritical marks automatically
- Converts Roman numerals (I, II, III) to Arabic (1, 2, 3)
- Compatible with all diatheke options and output formats
"""

import sys
import re
import argparse
import subprocess
import unicodedata
from typing import Dict, List, Tuple, Optional

__version__ = "1.0.0"

# Dutch to English Bible book mapping with English names support
# Based on both bijbel-wrapper.py and nbible.py with improvements
CANONICAL_BOOKS = {
    # Old Testament
    "genesis": "Genesis", "gen": "Genesis", "ge": "Genesis", "gn": "Genesis",
    "exodus": "Exodus", "ex": "Exodus", "exo": "Exodus", "exod": "Exodus",
    "leviticus": "Leviticus", "lev": "Leviticus", "le": "Leviticus", "levit": "Leviticus", "lv": "Leviticus",
    "numeri": "Numbers", "numbers": "Numbers", "num": "Numbers", "nu": "Numbers", "numb": "Numbers", "nm": "Numbers", "nb": "Numbers",
    "deuteronomium": "Deuteronomy", "deuteronomy": "Deuteronomy", "deut": "Deuteronomy", "deu": "Deuteronomy", "dt": "Deuteronomy",
    "jozua": "Joshua", "joshua": "Joshua", "joz": "Joshua", "jos": "Joshua", "jo": "Joshua", "josh": "Joshua",
    "richteren": "Judges", "rechters": "Judges", "richt": "Judges", "rech": "Judges", "ri": "Judges",
    "judges": "Judges", "judg": "Judges", "jdg": "Judges", "jgs": "Judges",
    "ruth": "Ruth", "ru": "Ruth", "rt": "Ruth", "rut": "Ruth", "rth": "Ruth",
    "1 samuel": "1Samuel", "1 samuelconsole": "1Samuel", "1sam": "1Samuel", "1 sam": "1Samuel", "i samuel": "1Samuel", "i sam": "1Samuel", "1 sm": "1Samuel", "1sa": "1Samuel", "1s": "1Samuel",
    "2 samuel": "2Samuel", "2 samuelconsole": "2Samuel", "2sam": "2Samuel", "2 sam": "2Samuel", "ii samuel": "2Samuel", "ii sam": "2Samuel", "2 sm": "2Samuel", "2sa": "2Samuel", "2s": "2Samuel",
    "1 koningen": "1Kings", "1kings": "1Kings", "1 kings": "1Kings", "1kon": "1Kings", "1 kon": "1Kings", "i koningen": "1Kings", "i kon": "1Kings", "1kgs": "1Kings", "1 kgs": "1Kings", "1ki": "1Kings", "1k": "1Kings",
    "2 koningen": "2Kings", "2kings": "2Kings", "2 kings": "2Kings", "2kon": "2Kings", "2 kon": "2Kings", "ii koningen": "2Kings", "ii kon": "2Kings", "2kgs": "2Kings", "2 kgs": "2Kings", "2ki": "2Kings", "2k": "2Kings",
    "1 kronieken": "1Chronicles", "1chronicles": "1Chronicles", "1 chronicles": "1Chronicles", "1kron": "1Chronicles", "1 kron": "1Chronicles", "1 kr": "1Chronicles", "i kronieken": "1Chronicles", "i kron": "1Chronicles", "1chr": "1Chronicles", "1 chr": "1Chronicles", "1chron": "1Chronicles", "1 chron": "1Chronicles", "1ch": "1Chronicles",
    "2 kronieken": "2Chronicles", "2chronicles": "2Chronicles", "2 chronicles": "2Chronicles", "2kron": "2Chronicles", "2 kron": "2Chronicles", "2 kr": "2Chronicles", "ii kronieken": "2Chronicles", "ii kron": "2Chronicles", "2chr": "2Chronicles", "2 chr": "2Chronicles", "2chron": "2Chronicles", "2 chron": "2Chronicles", "2ch": "2Chronicles",
    "ezra": "Ezra", "ezr": "Ezra", "ez": "Ezra",
    "nehemia": "Nehemiah", "nehemiah": "Nehemiah", "neh": "Nehemiah", "ne": "Nehemiah",
    "ester": "Esther", "esther": "Esther", "est": "Esther", "es": "Esther",
    "job": "Job", "jb": "Job",
    "psalm": "Psalms", "psalms": "Psalms", "psalmen": "Psalms", "ps": "Psalms", "psa": "Psalms", "pss": "Psalms", "psm": "Psalms",
    "spreuken": "Proverbs", "proverbs": "Proverbs", "spr": "Proverbs", "sp": "Proverbs", "prov": "Proverbs", "pro": "Proverbs", "pr": "Proverbs", "prv": "Proverbs",
    "prediker": "Ecclesiastes", "ecclesiastes": "Ecclesiastes", "pred": "Ecclesiastes", "eccl": "Ecclesiastes", "ecc": "Ecclesiastes", "ec": "Ecclesiastes", "qoh": "Ecclesiastes",
    "hooglied": "Song of Solomon", "song of solomon": "Song of Solomon", "song of songs": "Song of Solomon", "hoogl": "Song of Solomon", "hl": "Song of Solomon", "lied der liederen": "Song of Solomon", "ldl": "Song of Solomon", "sos": "Song of Solomon", "ss": "Song of Solomon", "cant": "Song of Solomon", "song": "Song of Solomon",
    "jesaja": "Isaiah", "isaiah": "Isaiah", "jes": "Isaiah", "js": "Isaiah", "isa": "Isaiah", "is": "Isaiah",
    "jeremia": "Jeremiah", "jeremiah": "Jeremiah", "jer": "Jeremiah", "je": "Jeremiah",
    "klaagliederen": "Lam", "lamentations": "Lam", "klaagl": "Lam", "kla": "Lam", "lam": "Lam", "la": "Lam",
    "ezechiel": "Ezekiel", "ezekiel": "Ezekiel", "ezech": "Ezekiel", "eze": "Ezekiel", "ezk": "Ezekiel", "ek": "Ezekiel",
    "daniel": "Daniel", "dan": "Daniel", "dn": "Daniel", "da": "Daniel",
    "hosea": "Hosea", "hos": "Hosea", "ho": "Hosea",
    "joel": "Joel", "jl": "Joel", "joe": "Joel", "jol": "Joel",
    "amos": "Amos", "am": "Amos", "amo": "Amos",
    "obadja": "Obadiah", "obadiah": "Obadiah", "ob": "Obadiah", "obad": "Obadiah", "oba": "Obadiah",
    "jona": "Jonah", "jonah": "Jonah", "jon": "Jonah", "jnh": "Jonah",
    "micha": "Micah", "micah": "Micah", "mi": "Micah", "mic": "Micah",
    "nahum": "Nahum", "nah": "Nahum", "na": "Nahum", "nah": "Nahum",
    "habakuk": "Habakkuk", "habakkuk": "Habakkuk", "hab": "Habakkuk", "hb": "Habakkuk",
    "sefanja": "Zephaniah", "zefanja": "Zephaniah", "zephaniah": "Zephaniah", "sef": "Zephaniah", "zef": "Zephaniah", "zep": "Zephaniah", "zph": "Zephaniah",
    "haggai": "Haggai", "hag": "Haggai", "hg": "Haggai",
    "zacharia": "Zechariah", "zechariah": "Zechariah", "zach": "Zechariah", "zac": "Zechariah", "zec": "Zechariah", "zch": "Zechariah",
    "maleachi": "Malachi", "malachi": "Malachi", "mal": "Malachi",

    # New Testament
    "matteus": "Matthew", "mattheüs": "Matthew", "matthéüs": "Matthew", "matth": "Matthew", "matthew": "Matthew", "mat": "Matthew", "matt": "Matthew", "mt": "Matthew",
    "marcus": "Mark", "markus": "Mark", "mark": "Mark", "mar": "Mark", "marc": "Mark", "mr": "Mark", "mk": "Mark", "mrk": "Mark",
    "lucas": "Luke", "lukas": "Luke", "luke": "Luke", "luc": "Luke", "lc": "Luke", "lu": "Luke", "luk": "Luke", "lk": "Luke",
    "johannes": "John", "john": "John", "joh": "John", "jn": "John",
    "handelingen": "Acts", "acts": "Acts", "hand": "Acts", "hd": "Acts", "hnd": "Acts", "ac": "Acts", "act": "Acts",
    "romeinen": "Romans", "romans": "Romans", "rom": "Romans", "rm": "Romans", "ro": "Romans",
    "1 korinthe": "1Corinthians", "1 korintiers": "1Corinthians", "1corinthians": "1Corinthians", "1 corinthians": "1Corinthians", "1kor": "1Corinthians", "1 kor": "1Corinthians", "1 cor": "1Corinthians", "1cor": "1Corinthians", "i korinthe": "1Corinthians", "i kor": "1Corinthians", "1co": "1Corinthians",
    "2 korinthe": "2Corinthians", "2 korintiers": "2Corinthians", "2corinthians": "2Corinthians", "2 corinthians": "2Corinthians", "2kor": "2Corinthians", "2 kor": "2Corinthians", "2 cor": "2Corinthians", "2cor": "2Corinthians", "ii korinthe": "2Corinthians", "ii kor": "2Corinthians", "2co": "2Corinthians",
    "galaten": "Galatians", "galatians": "Galatians", "gal": "Galatians", "ga": "Galatians", "glt": "Galatians",
    "efeze": "Ephesians", "efeziers": "Ephesians", "ephesians": "Ephesians", "ef": "Ephesians", "eph": "Ephesians", "ep": "Ephesians",
    "filippenzen": "Philippians", "filipenzen": "Philippians", "philippians": "Philippians", "fil": "Philippians", "phil": "Philippians", "php": "Philippians", "pp": "Philippians",
    "kolossenzen": "Colossians", "colossenzen": "Colossians", "colossians": "Colossians", "kol": "Colossians", "col": "Colossians", "co": "Colossians",
    "1 thessalonicenzen": "1Thessalonians", "1 tessalonicenzen": "1Thessalonians", "1thessalonians": "1Thessalonians", "1 thessalonians": "1Thessalonians", "1thess": "1Thessalonians", "1 thess": "1Thessalonians", "1thes": "1Thessalonians", "1 thes": "1Thessalonians", "1 tes": "1Thessalonians", "1th": "1Thessalonians", "i thessalonicenzen": "1Thessalonians", "i thess": "1Thessalonians", "i tes": "1Thessalonians", "1ts": "1Thessalonians",
    "2 thessalonicenzen": "2Thessalonians", "2 tessalonicenzen": "2Thessalonians", "2thessalonians": "2Thessalonians", "2 thessalonians": "2Thessalonians", "2thess": "2Thessalonians", "2 thess": "2Thessalonians", "2thes": "2Thessalonians", "2 thes": "2Thessalonians", "2 tes": "2Thessalonians", "2th": "2Thessalonians", "ii thessalonicenzen": "2Thessalonians", "ii thess": "2Thessalonians", "ii tes": "2Thessalonians", "2ts": "2Thessalonians",
    "1 timoteus": "1Timothy", "1 timotheus": "1Timothy", "1timothy": "1Timothy", "1 timothy": "1Timothy", "1tim": "1Timothy", "1 tim": "1Timothy", "1ti": "1Timothy", "i timoteus": "1Timothy", "i tim": "1Timothy", "1tm": "1Timothy",
    "2 timoteus": "2Timothy", "2 timotheus": "2Timothy", "2timothy": "2Timothy", "2 timothy": "2Timothy", "2tim": "2Timothy", "2 tim": "2Timothy", "2ti": "2Timothy", "ii timoteus": "2Timothy", "ii tim": "2Timothy", "2tm": "2Timothy",
    "titus": "Titus", "tit": "Titus", "ti": "Titus", "tt": "Titus",
    "filemon": "Philemon", "philemon": "Philemon", "filem": "Philemon", "flm": "Philemon", "phm": "Philemon", "pm": "Philemon", "phlm": "Philemon",
    "hebreeen": "Hebrews", "hebrews": "Hebrews", "hebr": "Hebrews", "heb": "Hebrews", "he": "Hebrews",
    "jakobus": "James", "jacobus": "James", "james": "James", "jak": "James", "jac": "James", "jas": "James", "jms": "James", "jam": "James", "jm": "James",
    "1 petrus": "1Peter", "1peter": "1Peter", "1 peter": "1Peter", "1 petr": "1Peter", "1 pet": "1Peter", "1pe": "1Peter", "i petrus": "1Peter", "i petr": "1Peter", "i pet": "1Peter", "1pt": "1Peter", "1p": "1Peter",
    "2 petrus": "2Peter", "2peter": "2Peter", "2 peter": "2Peter", "2 petr": "2Peter", "2 pet": "2Peter", "2pe": "2Peter", "ii petrus": "2Peter", "ii petr": "2Peter", "ii pet": "2Peter", "2pt": "2Peter", "2p": "2Peter",
    "1 johannes": "1John", "1john": "1John", "1 john": "1John", "1joh": "1John", "1 joh": "1John", "1jn": "1John", "i johannes": "1John", "i joh": "1John", "1j": "1John",
    "2 johannes": "2John", "2john": "2John", "2 john": "2John", "2joh": "2John", "2 joh": "2John", "2jn": "2John", "ii johannes": "2John", "ii joh": "2John", "2j": "2John",
    "3 johannes": "3John", "3john": "3John", "3 john": "3John", "3joh": "3John", "3 joh": "3John", "3jn": "3John", "iii johannes": "3John", "iii joh": "3John", "3j": "3John",
    "judas": "Jude", "jude": "Jude", "jud": "Jude", "jd": "Jude",
    "openbaring": "Revelation", "revelation": "Revelation", "openb": "Revelation", "opb": "Revelation", "op": "Revelation", "apocalyps": "Revelation", "apokalyps": "Revelation", "rev": "Revelation", "re": "Revelation", "rv": "Revelation",
}

APOCRYPHAL_BOOKS = {
    "tobit": "Tobit", "tobias": "Tobit", "tob": "Tobit",
    "judit": "Judith", "judith": "Judith", "jdt": "Judith",
    "wijsheid": "Wisdom", "wijsheid van salomo": "Wisdom", "wijsh": "Wisdom", "wis": "Wisdom",
    "sirach": "Sirach", "jezus sirach": "Sirach", "jesus sirach": "Sirach", "sir": "Sirach", "ecclesiasticus": "Sirach", "eccli": "Sirach",
    "baruch": "Baruch", "bar": "Baruch",
    "brief van jeremia": "Letter of Jeremiah", "brief van jeremias": "Letter of Jeremiah", "brief jeremia": "Letter of Jeremiah", "letjer": "Letter of Jeremiah",
    "1 makkabeeen": "1Maccabees", "1 makkabeen": "1Maccabees", "1 makk": "1Maccabees", "1 mak": "1Maccabees", "1macc": "1Maccabees", "1 maccabeeen": "1Maccabees",
    "2 makkabeeen": "2Maccabees", "2 makkabeen": "2Maccabees", "2 makk": "2Maccabees", "2 mak": "2Maccabees", "2macc": "2Maccabees", "2 maccabeeen": "2Maccabees",
    "3 makkabeeen": "3Maccabees", "3 makkabeen": "3Maccabees", "3 makk": "3Maccabees", "3 mak": "3Maccabees", "3macc": "3Maccabees", "3 maccabeeen": "3Maccabees",
    "4 makkabeeen": "4Maccabees", "4 makkabeen": "4Maccabees", "4 makk": "4Maccabees", "4 mak": "4Maccabees", "4macc": "4Maccabees", "4 maccabeeen": "4Maccabees",
    "toevoegingen bij ester": "Additions to Esther", "toevoegingen bij esther": "Additions to Esther", "addesther": "Additions to Esther",
    "gebed van azarja": "Prayer of Azariah", "gebed azarja": "Prayer of Azariah", "azariah": "Prayer of Azariah", "song of the three": "Prayer of Azariah", "songofthree": "Prayer of Azariah",
    "susanna": "Susanna", "sus": "Susanna",
    "bel en de draak": "Bel and the Dragon", "bel en draak": "Bel and the Dragon", "belandthedragon": "Bel and the Dragon",
    "gebed van manasse": "Prayer of Manasseh", "manasse": "Prayer of Manasseh",
}

def normalize_text(text: str) -> str:
    """Normalize text for matching: remove diacritics, lowercase, clean punctuation."""
    # Remove diacritical marks
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c))
    # Convert to lowercase
    text = text.lower()
    # Replace various dash types
    text = text.replace('–', '-').replace('—', '-')
    # Remove punctuation except spaces, hyphens, and colons
    text = re.sub(r'[.,;!?()[]{}]', ' ', text)
    # Convert Roman numerals to Arabic at word boundaries
    roman_map = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5', 'vi': '6'}
    for roman, arabic in roman_map.items():
        text = re.sub(rf'\b{roman}\b', arabic, text)
    # Normalize spaces around numbers (e.g., "1kor" -> "1 kor", "psalm23" -> "psalm 23")  
    text = re.sub(r'(\d)([a-z])', r'\1 \2', text)
    text = re.sub(r'([a-z])(\d)', r'\1 \2', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def build_book_mapping(include_apocrypha: bool = False) -> Dict[str, str]:
    """Build the complete mapping dictionary."""
    mapping = CANONICAL_BOOKS.copy()
    if include_apocrypha:
        mapping.update(APOCRYPHAL_BOOKS)
    
    # Add normalized variations
    normalized_mapping = {}
    for dutch_key, english_value in mapping.items():
        # Add the original key
        normalized_mapping[dutch_key] = english_value
        # Add normalized version
        norm_key = normalize_text(dutch_key)
        normalized_mapping[norm_key] = english_value
        # Add version without spaces
        no_space_key = norm_key.replace(' ', '')
        normalized_mapping[no_space_key] = english_value
        
    return normalized_mapping

def expand_reference_shorthand(reference: str, include_apocrypha: bool = False) -> List[str]:
    """
    Expand shorthand Bible reference syntax into individual references.

    Syntax rules:
    - ',' separates verses within the same chapter OR different books
    - ';' separates chapters within the same book OR different books

    Examples:
        "Ex 9:9,25" -> ["Ex 9:9", "Ex 9:25"]
        "Ex 9:9;25" -> ["Ex 9:9", "Ex 25"]
        "Ex 9:9,25; 10:1" -> ["Ex 9:9", "Ex 9:25", "Ex 10:1"]
        "Ex 9:9, Gen 10:10" -> ["Ex 9:9", "Gen 10:10"]
        "Ex 9:9,25; 10:1; Genesis 10:10" -> ["Ex 9:9", "Ex 9:25", "Ex 10:1", "Genesis 10:10"]
    """
    if not reference.strip():
        return []

    result = []

    # First split by semicolon (chapter/book separators)
    semicolon_parts = [p.strip() for p in reference.split(';') if p.strip()]

    last_book = None
    last_chapter = None

    for semi_part in semicolon_parts:
        # Now split by comma (verse separators within the same chapter)
        comma_parts = [p.strip() for p in semi_part.split(',') if p.strip()]

        for comma_part in comma_parts:
            # Detect what kind of reference this is:
            # 1. Full reference with book name (e.g., "Ex 9:9", "Genesis 10:10")
            # 2. Chapter:verse without book (e.g., "10:5") - use last_book
            # 3. Just verse number (e.g., "25") - use last_book and last_chapter
            # 4. Just chapter (e.g., "10") after semicolon - use last_book

            tokens = comma_part.split()

            # Always check if this could be a book reference first
            # This handles: "Ex 9:9", "Exodus 9:9", "1 Kor 13:4", "1Ki 8:27", etc.
            mapping = build_book_mapping(include_apocrypha)
            norm_part = normalize_text(comma_part)

            found_book = False
            for i in range(len(tokens), 0, -1):
                potential_book = " ".join(normalize_text(t) for t in tokens[:i])
                if potential_book in mapping or potential_book.replace(" ", "") in mapping:
                    # This is a valid book name
                    result.append(comma_part)
                    last_book = " ".join(tokens[:i])
                    rest = " ".join(tokens[i:])
                    if rest and ':' in rest:
                        last_chapter = rest.split(':')[0].strip()
                    found_book = True
                    break

            if found_book:
                continue

            # Not a book reference, check other cases
            if ':' in comma_part:
                # This is "chapter:verse" without book name
                if last_book:
                    result.append(f"{last_book} {comma_part}")
                    last_chapter = comma_part.split(':')[0].strip()
                else:
                    raise ValueError(f"Reference '{comma_part}' has no book context")

            elif re.match(r'^\d+(-\d+)?$', comma_part):
                # This is a verse number or verse range (e.g., "38" or "38-39")
                # After comma: it's a verse in the same chapter
                # After semicolon: it could be a chapter or verse depending on context
                if last_book and last_chapter:
                    # Assume it's a verse in the same chapter (comma-separated)
                    result.append(f"{last_book} {last_chapter}:{comma_part}")
                elif last_book:
                    # After semicolon without chapter context, treat as chapter
                    result.append(f"{last_book} {comma_part}")
                    last_chapter = comma_part
                else:
                    raise ValueError(f"Reference '{comma_part}' has no book/chapter context")

            else:
                # Treat as full reference
                result.append(comma_part)

        # After processing a semicolon-separated part, clear the chapter context
        # but keep the book context
        last_chapter = None

    return result

def parse_reference(reference: str, include_apocrypha: bool = False) -> str:
    """Convert Dutch Bible reference to English format suitable for diatheke."""
    if not reference.strip():
        raise ValueError("Empty reference provided")

    mapping = build_book_mapping(include_apocrypha)
    norm_ref = normalize_text(reference)

    # Find the split point between book and chapter/verse
    # Look for the pattern: book name followed by chapter:verse or just chapter
    tokens = norm_ref.split()
    if not tokens:
        raise ValueError("Invalid reference format")

    # Try to find the longest matching book name
    book_part = ""
    rest_part = ""

    for i in range(len(tokens), 0, -1):
        potential_book = " ".join(tokens[:i])
        potential_rest = " ".join(tokens[i:])

        # Check if this is a valid book name
        if potential_book in mapping:
            book_part = potential_book
            rest_part = potential_rest
            break
        # Also check without spaces
        potential_book_no_space = potential_book.replace(" ", "")
        if potential_book_no_space in mapping:
            book_part = potential_book_no_space
            rest_part = potential_rest
            break

    if not book_part:
        raise ValueError(f"Unknown Bible book: '{tokens[0] if tokens else reference}'")

    english_book = mapping[book_part]

    if not rest_part:
        return english_book

    # Handle single chapter books (like Jude, Obadiah, etc.) that only have verses
    if ':' not in rest_part and rest_part.strip():
        # Check if this might be a single-chapter book
        single_chapter_books = {'Jude', 'Obadiah', 'Philemon', '2John', '3John'}
        if english_book in single_chapter_books:
            return f"{english_book} 1:{rest_part.strip()}"

    return f"{english_book} {rest_part.strip()}"

def run_diatheke(module: str, reference: str, format_type: str = "plain", options: str = None, echo: bool = False, dry_run: bool = False) -> int:
    """Execute diatheke with the given parameters."""
    cmd = ["diatheke", "-b", module]
    # Always include the format parameter
    cmd.extend(["-f", format_type])
    if options:
        cmd.extend(["-o", options])
    # The -k parameter must be last
    cmd.extend(["-k", reference])
    
    if echo or dry_run:
        print(f"[CMD] {' '.join(cmd)}")
    
    if dry_run:
        return 0
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
    except FileNotFoundError:
        print("ERROR: diatheke command not found. Please install SWORD tools.", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="Dutch Bible reference wrapper for diatheke",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s -b HSV "Johannes 3:16"
    %(prog)s -b DutSVV "1 Kor 13:4-7"  
    %(prog)s --format HTML "Psalm 23"
    echo "Spreuken 3:5-6" | %(prog)s -b HSV
        """
    )
    
    parser.add_argument("reference", nargs="*", 
                       help="Bible reference (e.g., 'Johannes 3:16')")
    parser.add_argument("-b", "--module", default="HSV",
                       help="SWORD Bible module (default: HSV)")
    parser.add_argument("-f", "--format", default="plain",
                       help="Output format: plain, HTML, RTF, etc. (default: plain)")
    parser.add_argument("-o", "--options", 
                       help="Module option filters (e.g., fv, fcv, fmslx)")
    parser.add_argument("-k", "--key", 
                       help="Bible reference (alternative to positional argument)")
    parser.add_argument("--echo", action="store_true",
                       help="Show the diatheke command being executed")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show command without executing it")
    parser.add_argument("--apocrypha", action="store_true",
                       help="Include Deuterocanonical/Apocryphal books")
    parser.add_argument("-v", "--version", action="version", 
                       version=f"%(prog)s {__version__}")
    
    args = parser.parse_args()
    
    # Collect references from arguments or stdin
    references = []
    if args.key:
        references.append(args.key)
    elif args.reference:
        references.append(" ".join(args.reference))
    elif not sys.stdin.isatty():
        # Read from stdin
        for line in sys.stdin:
            line = line.strip()
            if line:
                references.append(line)
    
    if not references:
        parser.print_help()
        return 1
    
    exit_code = 0
    for ref in references:
        try:
            # Expand shorthand syntax (comma and semicolon separators)
            expanded_refs = expand_reference_shorthand(ref, args.apocrypha)

            # Convert each expanded reference to English
            english_refs = []
            for expanded_ref in expanded_refs:
                english_ref = parse_reference(expanded_ref, args.apocrypha)
                english_refs.append(english_ref)

            # Join them with semicolons (diatheke's multi-reference separator)
            combined_english_ref = '; '.join(english_refs)
            result = run_diatheke(args.module, combined_english_ref, args.format, args.options, args.echo, args.dry_run)
            exit_code = max(exit_code, result)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            exit_code = 1
        except KeyboardInterrupt:
            print("\nInterrupted", file=sys.stderr)
            return 130
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
