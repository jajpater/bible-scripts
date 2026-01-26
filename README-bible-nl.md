# Bible Scripts

Dit document beschrijft het uniforme systeem voor bijbeltekst-opzoek en de
format-converter `bible-to-format_v2.py`.

## Overzicht

Er is één centraal `bible` script dat via symlinks wordt aangeroepen. De
scriptnaam bepaalt welke module en welk outputformaat wordt gebruikt.

```
bible/
├── bible                 # Master script
├── bible-symlinks         # Interactieve symlink manager
├── bible-to-format_v2.py  # Format converter (tex, md, typ) met poëtische regeleinden
├── bible-format-wrapper.py
├── dutch-diatheke.py
├── hsv -> bible
├── hsvhtml -> bible
├── hsvtex -> bible
├── hsvtyp -> bible
├── ...
```

## Hoe het werkt

### Naamconventie

De scriptnaam wordt geparsed in drie delen: base, format en (optioneel) opties.

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

Opties worden na een `-` gezet. Het format zit altijd direct aan de base vast
(bijv. `gbsorg-fr`).

### Ondersteunde formaten

| Suffix | Formaat     | Beschrijving                          |
|--------|-------------|---------------------------------------|
| (geen) | plain       | Opgemaakte tekst met versreferenties  |
| `html` | HTML        | HTML output via diatheke              |
| `tex`  | LaTeX       | LaTeX met poëtische structuur         |
| `typ`  | Typst       | Typst met tabel-layout                |
| `typs` | Typst       | Typst simple style                    |
| `md`   | Markdown    | Markdown met inspringing              |
| `org`  | Org-mode    | Org-mode met #+BEGIN_VERSE blokken    |

### Formatter routing

- `plain` gebruikt `bible-format-wrapper.py`.
- `tex`, `typ`, `md`, `org` gebruiken `bible-to-format_v2.py`.
- Als opties `f` (footnotes) of `r` (refs) gezet zijn, gebruikt het script
  OSIS-output voor notes.

### Module mapping

Het `bible` script bevat een mapping van korte namen naar SWORD-modules:

```bash
[hsv]="HSV"
[svv]="DutSVV"
[nbv]="NBV21"
[esv]="ESV"
[lxx]="LXX"
# etc.
```

Als een naam niet in de mapping staat, probeert het script de naam direct als
SWORD-module te gebruiken.

## Gebruik

### Via symlinks (aanbevolen)

```bash
hsv Johannes 3:16
svv Psalm 23:1-6
hsvtex "1 Kor 13:4-7"
esv John 1:1
gbsorg-fr Psalm 3:9
kjva-fnl Matt 1:1
```

### Direct via bible script

```bash
bible -m HSV Johannes 3:16
bible -m LXX -f html Genesis 1:1
bible -m KJVA -o fnl Matt 1:1
bible -m GBS2 -f org -o fr Psalm 3:9
bible --list-modules
```

### Opties

```
-h, --help      Toon help
-v, --version   Toon versie
-m, --module    Specificeer SWORD-module
-f, --format    Specificeer outputformaat (plain, html, tex, typ, md, org)
-o, --options   Specificeer option filters (bijv. fr, fnl)
-i, --inline-notes  Render notes inline (anders onder het vers)
--ref-pos       Referentiepositie (start, end, none) voor geformatteerde output
--ref-type      Referentietype (inline, footnote, combined)
--verse-nums    Versnummering (dots, colons, none)
--book-style    Boekstijl (full, abbr)
--version-abbrev  Versie-afkorting (auto, none)
--style         Formatter-stijl (table, simple)
--raw           Ruwe output zonder formatting
--list-modules  Toon beschikbare modules
```

### Opties (suffix / -o)

Veelgebruikte option filters:

- `f` footnotes
- `r` refs (cross references; mapping naar diatheke `s`)
- `n` Strong's numbers
- `l` lemmas
- `m` morphology
- `h` headings
- `c` cantillation
- `v` Hebrew vowels
- `a` Greek accents

### Inline voetnoten (org/md/tex/typ)

Met `-i/--inline-notes` komen notes inline te staan met een spatie erna:

```text
Org: Dit is tekst[fn:: 53. Dit is de voetnoot] 
MD:  Dit is tekst^[53. Dit is de voetnoot] 
TeX: Dit is tekst\footnote{53. Dit is de voetnoot.} 
Typ: Dit is tekst #footnote[53. Dit is de voetnoot] 
```

## bible-to-format_v2.py

Converter voor diatheke HTML/OSIS output met uitgebreide format-opties.

### Gebruik

```bash
# HTML input
dutch-diatheke.py -b HSV -f HTML "Psalm 3:9" | ./bible-to-format_v2.py --format org

# OSIS input (aanbevolen voor footnotes/refs)
diatheke -b GBS2 -f OSIS -o fs -k "Ps 3:9" | ./bible-to-format_v2.py --format org --options fr
```

### Formats

```
--format {typ,tex,md,org,plain}
```

Notes:
- `plain` outputs basic text met versnummering en optionele notes.
- `typ`/`tex`/`md`/`org` behouden poëtische regeleinden.

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
- `tex`/`typ` gebruiken superscript labels als versnummers aan staan.
- `md`/`org` gebruiken de gekozen prefix.

### Notes en cross references

```
--options <filters>
--inline-notes
```

Default note behavior:
- Notes staan onder elk vers met format-specifieke markers.
- `--inline-notes` zet notes inline.

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

#### Marker voorbeeld (originele n-waarden)

Als een module note-markers levert (bijv. `n="53"`), gebruikt v2 die markers:

```text
53. En God zag al wat Hij gemaakt had, en zie, het was zeer goed.[fn:53] 
   [fn:53] note: Of: zeer goed.
```

## Nieuwe module toevoegen

### Methode 1: Interactieve manager

```bash
./bible-symlinks
```

Dit opent een interactief menu waar je:
1. Modules kunt selecteren uit alle geïnstalleerde SWORD-modules
2. Format-varianten kunt toevoegen (html, tex, typ, typs, md, org)
3. Option-varianten kunt toevoegen (bijv. `gbsorg-fr`)
4. Option-filters kunt forceren zonder naamsuffix
5. Symlinks kunt verwijderen
6. Huidige symlinks kunt bekijken

### Methode 2: Handmatig

```bash
# Stap 1: Maak symlink
ln -s bible lxx

# Stap 2 (optioneel): Voeg mapping toe als naam != module
# Edit bible script en voeg toe aan MODULE_MAP:
[lxx]="LXX"

# Stap 3 (optioneel): Maak format-varianten
ln -s bible lxxhtml
ln -s bible lxxtex
```

### Methode 3: Quick add via CLI

```bash
./bible-symlinks -a lxx LXX
./bible-symlinks -a septuagint LXX
```

## Beschikbare modules

Bekijk alle geïnstalleerde SWORD-modules:

```bash
bible --list-modules
# of
diatheke -b system -k modulelist
```

## Output formaten

### Poëtische structuur

**LaTeX** (`hsvtex Psalm 3:9`):
```latex
\begin{verse}
\textsuperscript{9} Het heil is van de  \textsc{HEERE} ;\\
\vin Uw zegen is over Uw volk.\\
\vin Sela
\end{verse}
```

**Markdown** (`hsvmd Psalm 3:9`):
```markdown
9. Het heil is van de  **HEERE** ;
    Uw zegen is over Uw volk.
    Sela
```

**Typst** (`hsvtyp Psalm 3:9`):
```typst
#table(columns: (auto, auto), stroke: none,
    [#text(size:11pt)[9.]], [Het heil is van de  #smallcaps[HEERE] ;],
    [], [Uw zegen is over Uw volk.],
    [], [Sela],
)
```

**Org-mode** (`hsvorg Psalm 3:9`):
```org
#+BEGIN_VERSE
9. Het heil is van de  *HEERE* ;
   Uw zegen is over Uw volk.
   Sela
#+END_VERSE
```

### Proza

Voor proza-teksten (zoals Johannes) wordt geen verse-omgeving gebruikt:

```bash
hsvtex Johannes 3:16
# Output: \textsuperscript{16} Want zo lief heeft God de wereld gehad...
```

## Technische details

### Dependencies

- `diatheke` - SWORD Bible lookup engine
- `fzf` - Voor interactieve module selectie (bible-symlinks)
- `pandoc` - Voor tex/md output conversie

**Let op:** `diatheke-tui` wordt bewust **niet** meegeleverd in de flake-package.
- Python 3 - Voor helper scripts
