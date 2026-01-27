# Bible Scripts

This document describes the unified Bible lookup system and the
`bible-to-format_v2.py` format converter.

## Overview

There is one central `bible` script that is invoked via symlinks. The
script name determines which module and which output format is used.

## Dependencies (SWORD/Diatheke)

This repo assumes you have a **patched SWORD** installation locally, with
`diatheke` (and optionally `xiphos`) built against that patch set. For that
reason, `diatheke` is **not** declared as a runtime dependency in the Nix
derivation. Ensure `diatheke` is in your `PATH`.

```
bible/
├── bible                 # Master script
├── bible-symlinks         # Interactive symlink manager
├── bible-to-format_v2.py  # Format converter (tex, md, typ) with poetic line breaks
├── bible-format-wrapper.py
├── dutch-diatheke.py
├── hsv -> bible
├── hsvhtml -> bible
├── hsvtex -> bible
├── hsvtyp -> bible
├── ...
```

## How it works

### Naming convention

The script name is parsed into three parts: base, format and (optional) options.

| Symlink     | Base  | Format | Module  |
|-------------|-------|--------|---------|
| `hsv`       | hsv   | plain  | HSV     |
| `hsvhtml`   | hsv   | html   | HSV     |
| `hsvtex`    | hsv   | tex    | HSV     |
| `hsvorg`    | hsv   | org    | HSV     |
| `svvmd`     | svv   | md     | DutSVV  |
| `lxx`       | lxx   | plain  | LXX     |
| `gbsorg-fr` | gbs   | org    | GBS2    |
| `kjva-fnl`  | kjva  | plain  | KJVA    |

Options are appended after a `-`. The format always sits directly after the
base (e.g. `gbsorg-fr`).

### Supported formats

| Suffix | Format     | Description                           |
|--------|------------|---------------------------------------|
| (none) | plain      | Formatted text with verse references  |
| `html` | HTML       | HTML output via diatheke              |
| `tex`  | LaTeX      | LaTeX with poetic structure           |
| `typ`  | Typst      | Typst with table layout               |
| `typs` | Typst      | Typst simple style                    |
| `md`   | Markdown   | Markdown with indentation             |
| `org`  | Org-mode   | Org-mode with #+BEGIN_VERSE blocks    |

### Formatter routing

- `plain` uses `bible-format-wrapper.py`.
- `tex`, `typ`, `md`, `org` use `bible-to-format_v2.py`.
- If options `f` (footnotes) or `r` (refs) are set, the script uses
  OSIS output for notes.

### Module mapping

The `bible` script contains a mapping from short names to SWORD modules:

```bash
[hsv]="HSV"
[svv]="DutSVV"
[nbv]="NBV21"
[esv]="ESV"
[lxx]="LXX"
# etc.
```

If a name is not in the mapping, the script tries to use the name directly
as a SWORD module.

## Usage

### Via symlinks (recommended)

```bash
hsv John 3:16
svv Psalm 23:1-6
hsvtex "1 Cor 13:4-7"
esv John 1:1
gbsorg-fr Psalm 3:9
kjva-fnl Matt 1:1
```

### Direct via the bible script

```bash
bible -m HSV John 3:16
bible -m LXX -f html Genesis 1:1
bible -m KJVA -o fnl Matt 1:1
bible -m GBS2 -f org -o fr Psalm 3:9
bible --list-modules
```

### Options

```
-h, --help      Show help
-v, --version   Show version
-m, --module    Specify SWORD module
-f, --format    Specify output format (plain, html, tex, typ, md, org)
-o, --options   Specify option filters (e.g. fr, fnl)
-i, --inline-notes  Render notes inline (otherwise below the verse)
--ref-pos       Reference position (start, end, none) for formatted output
--ref-type      Reference type (inline, footnote, combined)
--verse-nums    Verse numbering (dots, colons, none)
--book-style    Book style (full, abbr)
--version-abbrev  Version abbreviation (auto, none)
--style         Formatter style (table, simple)
--raw           Raw output without formatting
--list-modules  Show available modules
```

### Options (suffix / -o)

Common option filters:

- `f` footnotes
- `r` refs (cross references; maps to diatheke `s`)
- `n` Strong's numbers
- `l` lemmas
- `m` morphology
- `h` headings
- `c` cantillation
- `v` Hebrew vowels
- `a` Greek accents

### Inline footnotes (org/md/tex/typ)

With `-i/--inline-notes` notes appear inline with a trailing space:

```text
Org: This is text[fn:: 53. This is the footnote] 
MD:  This is text^[53. This is the footnote] 
TeX: This is text\footnote{53. This is the footnote.} 
Typ: This is text #footnote[53. This is the footnote] 
```

## bible-to-format_v2.py

Converter for diatheke HTML/OSIS output with extended format options.

### Usage

```bash
# HTML input
dutch-diatheke.py -b HSV -f HTML "Psalm 3:9" | ./bible-to-format_v2.py --format org

# OSIS input (recommended for footnotes/refs)
diatheke -b GBS2 -f OSIS -o fs -k "Ps 3:9" | ./bible-to-format_v2.py --format org --options fr
```

### Formats

```
--format {typ,tex,md,org,plain}
```

Notes:
- `plain` outputs basic text with verse numbering and optional notes.
- `typ`/`tex`/`md`/`org` preserve poetic line breaks.

### Reference controls

```
--ref-pos {start,end,none}
--ref-type {inline,footnote,combined}
--book-style {full,abbr}
--version-abbrev {auto,none}
```

### Verse numbering

```
--verse-nums {dots,colons,none}
```

Notes:
- `tex`/`typ` use superscript labels when verse numbers are enabled.
- `md`/`org` use the chosen prefix.

### Notes and cross references

```
--options <filters>
--inline-notes
```

Default note behavior:
- Notes appear below each verse with format-specific markers.
- `--inline-notes` renders notes inline.

Format-specific note markers (non-inline):
- org: `[fn:1]`
- markdown: `[^1]`
- latex: `\textsuperscript{1}`
- typst: `#super[1]`

Inline note syntax:
- org: `[fn:: 1. ...] `
- markdown: `^[1. ...] `
- latex: `\footnote{1. ...} `
- typst: `#footnote[1. ...] `

#### Marker example (original n-values)

If a module provides note markers (e.g. `n="53"`), v2 uses those markers:

```text
53. And God saw all that He had made, and behold, it was very good.[fn:53] 
   [fn:53] note: Or: very good.
```

## Add a new module

### Method 1: Interactive manager

```bash
./bible-symlinks
```

This opens an interactive menu where you can:
1. Select modules from all installed SWORD modules
2. Add format variants (html, tex, typ, typs, md, org)
3. Add option variants (e.g. `gbsorg-fr`)
4. Force option filters without name suffix
5. Remove symlinks
6. View current symlinks

### Method 2: Manual

```bash
# Step 1: Create symlink
ln -s bible lxx

# Step 2 (optional): Add mapping if name != module
# Edit bible script and add to MODULE_MAP:
[lxx]="LXX"

# Step 3 (optional): Create format variants
ln -s bible lxxhtml
ln -s bible lxxtex
```

### Method 3: Quick add via CLI

```bash
./bible-symlinks -a lxx LXX
./bible-symlinks -a septuagint LXX
```

## Available modules

List all installed SWORD modules:

```bash
bible --list-modules
# or
diatheke -b system -k modulelist
```

## Output formats

### Poetic structure

**LaTeX** (`hsvtex Psalm 3:9`):
```latex
\begin{verse}
\textsuperscript{9} Salvation belongs to the  \textsc{LORD} ;\\
\vin Your blessing is on Your people.\\
\vin Selah
\end{verse}
```

**Markdown** (`hsvmd Psalm 3:9`):
```markdown
9. Salvation belongs to the  **LORD** ;
    Your blessing is on Your people.
    Selah
```

**Typst** (`hsvtyp Psalm 3:9`):
```typst
#table(columns: (auto, auto), stroke: none,
    [#text(size:11pt)[9.]], [Salvation belongs to the  #smallcaps[LORD] ;],
    [], [Your blessing is on Your people.],
    [], [Selah],
)
```

**Org-mode** (`hsvorg Psalm 3:9`):
```org
#+BEGIN_VERSE
9. Salvation belongs to the  *LORD* ;
   Your blessing is on Your people.
   Selah
#+END_VERSE
```

### Prose

For prose texts (such as John), no verse environment is used:

```bash
hsvtex John 3:16
# Output: \textsuperscript{16} For God so loved the world...
```

## Technical details

### Dependencies

- `diatheke` - SWORD Bible lookup engine (must be installed separately)
- `fzf` - Interactive module selection (bible-symlinks)
- `pandoc` - Tex/md output conversion
- Python 3 - Helper scripts

**Note:** `diatheke-tui` is intentionally **not** shipped in the flake package.

### Nix Flake

This repo contains a `flake.nix` for installation via Nix.

#### SWORD not included

**Important:** The flake intentionally does not include SWORD as a dependency. This is because:

1. Dutch Bible modules (GBS2, HSV, NBV21) require a patched SWORD with DutSVV versification
2. We want to avoid having two SWORD versions (patched + unpatched) on the system
3. The patched SWORD should be available system-wide (also for Xiphos)

You must install SWORD (or sword-patched) separately before bible-scripts will work.

#### Preserving symlink names

The flake uses `wrapProgram` with `--inherit-argv0` to preserve symlink names. This ensures `hsv John 3:16` works correctly - the script sees `hsv` as the invocation name, not `bible`.

#### Installation

```bash
# Standalone (requires diatheke in PATH)
nix run github:jajpater/bible-scripts -- -m HSV "John 3:16"

# Development shell
nix develop github:jajpater/bible-scripts
```

#### DutSVV Versification Patch

The repo contains `dutsvv-versification.patch` as documentation/backup. This patch adds support for the DutSVV versification system to SWORD. The patch is not used by the flake - you must patch SWORD yourself or use a pre-patched version.

To build patched SWORD:

```nix
sword-patched = pkgs.sword.overrideAttrs (old: {
  postPatch = (old.postPatch or "") + ''
    patch -p0 < ${./dutsvv-versification.patch}
  '';
});
```

The patch has been submitted to the SWORD project. Once accepted upstream, the patch will no longer be needed.
