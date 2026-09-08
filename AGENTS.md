# AGENTS.md — Contributor & Autonomous Agent Guide

Welcome to the **Grand Theft Auto V Indonesian Localization Project**.

This document defines the strict engineering constraints, safety standards, and operational workflows for human contributors and autonomous AI agents working in this repository.

---

## 1. Absolute Immutable Rule — Highest Priority

> [!CAUTION]
> ### THE IMMUTABLE KEY RULE
> **THE PART BEFORE "=" MUST NEVER BE MODIFIED UNDER ANY CIRCUMSTANCES.**
> 
> ```
> <INDENTATION><KEY> = <TEXT>
> ```
> 
> **ONLY MODIFY THE CONTENT AFTER THE FIRST "=".**
> 
> - NEVER modify keys, hashes (e.g. `0x2DA16D65`), or named identifiers (e.g. `HUD_PAUSE`).
> - NEVER modify the indentation (tab `\t`) or spacing before the `=`.
> - NEVER add prefixes or suffixes to keys (e.g., changing `HUD_PAUSE` to `HUD_PAUSE_ID` is strictly prohibited).
> - NEVER alter key order.
> - NEVER delete, create, merge, or split keys.

### Example

```ini
# ORIGINAL SOURCE
	HUD_PAUSE = Resume Game

# CORRECT TRANSLATION
	HUD_PAUSE = Lanjutkan Permainan

# STRICTLY PROHIBITED (Modified Key)
	HUD_PAUSE_ID = Lanjutkan Permainan

# STRICTLY PROHIBITED (Altered Prefix / Delimiter)
HUD_PAUSE: Lanjutkan Permainan
```

---

## 2. File Format & Technical Specifications

GTA V uses the `.oxt` text format (utilized by OpenIV for archive import/export):

1. **Header**: Every `.oxt` file starts with a version line (typically `Version 2 30`).
2. **Block Enclosure**: Entries are enclosed within curly braces `{ ... }`.
3. **Entries**: Each entry follows the format `\t<KEY> = <TEXT>`.
4. **Encoding**: Files **MUST** be encoded in **UTF-8 with BOM (`utf-8-sig`)** (`0xEF, 0xBB, 0xBF`). Standard UTF-8 without BOM may cause game engine crashes.
5. **Line Endings**: Files **MUST** use Windows **CRLF (`\r\n`)** line endings.
6. **Multiple Equals Signs**: 443+ entries contain multiple `=` signs due to inline HTML tags (e.g., `<img src='...' width='252'/>`). Always parse entries by splitting **strictly on the first `=`** (`line.split("=", 1)`).

---

## 3. Token & Placeholder Safety Rules

1. **Rockstar Tokens (`~...~`)**:
   - Formatting tokens: `~s~` (default/white), `~r~` (red), `~g~` (green), `~b~` (blue), `~y~` (yellow), `~c~` (grey), `~n~` (newline), `~z~` (subtitle delay).
   - Input prompts: `~INPUT_CONTEXT~`, `~INPUT_ATTACK~`, `~INPUTGROUP_LOOK~`, etc.
   - Radar & HUD colors: `~HUD_COLOUR_RED~`, `~BLIP_OBJECTIVE~`, etc.
   - Values: `~a~` (string argument), `~1~` (integer argument).
   - **Rule**: Every token present in the source text must appear in the translation in exact casing and frequency.

2. **Standard Format Specifiers**:
   - `%s`, `%d`, `%f`, `%1`, `{0}`, `{player}`, `<name>`, `[NAME]`.
   - **Rule**: Never translate, alter, or renumber placeholders.

3. **Escape Sequences & Markup**:
   - `\n`, `\r`, `\t`, `\"`, `\'`.
   - Inline tags: `<img src='...' ... />`.
   - **Rule**: Retain all escape sequences and tags without modification.

4. **Proper Nouns**:
   - Fictional brands, vehicle models, characters, and districts must remain authentic:
     - Characters: *Michael, Trevor, Franklin, Lamar, Lester, Brad...*
     - Locations: *Los Santos, Blaine County, Vinewood, Del Perro...*
     - Factions: *FIB, IAA, Merryweather, Ammu-Nation, Lifeinvader...*
     - Vehicles: *Pegassi, Grotti, Bravado, Karin, Truffade...*
     - Brands: *Sprunk, eCola, Pisswasser, EgoChaser...*

---

## 4. Repository Structure

```
/
├── AGENTS.md                   # Contributor & autonomous agent guidance
├── PROGRESS.md                 # Real-time localization metrics and status
├── README.md                   # Project overview and user documentation
├── validate.py                 # Core integrity and structural validator
├── translate.py                # Safe, resumable translation pipeline
├── locales/
│   ├── original/               # Sacred, pristine original .oxt files (read-only)
│   │   └── *.oxt
│   ├── id/                     # Indonesian localized .oxt files
│   │   └── *.oxt
│   └── cache/                  # Resumable translation cache (translations.json)
├── tools/
│   ├── glossary.py             # Curated GTA V gaming glossary & directive patterns
│   └── token_shield.py         # Token extraction, masking, and restoration
└── reports/
    └── validation_report.json  # Automated validation audit reports
```

---

## 5. Development & Agent Workflow

Autonomous agents and human contributors must follow this exact sequence:

```
+----------------+      +-------------------+      +------------------+
| 1. Scan Source | ---> | 2. Mask & Shield  | ---> | 3. Translate Text|
| locales/orig/  |      | tools/token_shield|      | tools/glossary.py|
+----------------+      +-------------------+      +------------------+
                                                             |
                                                             v
+----------------+      +-------------------+      +------------------+
| 6. Git Commit  | <--- | 5. Run Validator  | <--- | 4. Write Target  |
| Clean Branch   |      | validate.py       |      | locales/id/      |
+----------------+      +-------------------+      +------------------+
```

### Step 1: Run Translation
To translate a batch of files:
```bash
python translate.py --files prolog.oxt abgail2.oxt snk_mnu.oxt --validate
```
To run a dry-run test without writing files:
```bash
python translate.py --files prolog.oxt --dry-run
```

### Step 2: Validate Translation Integrity
Always execute `validate.py` before committing changes:
```bash
python validate.py
```
To validate specific files:
```bash
python validate.py --files prolog.oxt abgail2.oxt
```

The validator checks:
- [x] Exact byte-level equality of left-hand side (indentation, key name, spacing before `=`)
- [x] Zero missing, added, or reordered keys
- [x] 100% token, placeholder, and escape sequence preservation
- [x] Correct UTF-8 BOM (`\xef\xbb\xbf`) header
- [x] Correct CRLF (`\r\n`) line endings

### Step 3: Git Operations
- All work is performed on descriptive branches (e.g. `localization/indonesian`).
- Make clean, atomic commits:
  - `feat: add Indonesian localization for prologue missions`
  - `fix: correct token preservation in menu files`
  - `docs: update translation progress metrics`
- Never commit broken validation audits.
