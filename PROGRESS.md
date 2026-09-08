# Progress Tracker — GTA V Indonesian Localization

Tracking the active migration, translation, and validation health of the GTA V Indonesian localization project.

---

## 1. Project Metrics

| Indicator | Metric | Status / Details |
| :--- | :--- | :--- |
| **Current Branch** | `localization/indonesian` | Dedicated working branch |
| **Total `.oxt` Files** | **610** | 100% preserved in `locales/original/` and mirrored in `locales/id/` |
| **Total Source Entries** | **284,927** | 100% indexed and structurally verified |
| **Active Content Files** | 572 files | Files with text entries |
| **Stub / Empty Files** | 38 files | Files with zero entries (only version header, mirrored cleanly) |
| **Validation Health** | **100% PASS (610/610 files)** | **0 errors, 0 missing keys, 0 token mismatches** |
| **Entries Translated** | **1,581 entries** | Core UI, menus, prologue, mission directives, tutorials, snacks, shops |
| **Entries Retained (EN)** | 283,346 entries | Safe original English retained until iterative translation |
| **Encoding Standard** | **UTF-8 with BOM (`utf-8-sig`)** | 100% byte-verified across all 610 files |
| **Line Ending Standard** | **Windows CRLF (`\r\n`)** | 100% byte-verified across all 610 files |

---

## 2. Localization Category Breakdown

| Category / File Group | Files | Entries | Status | Details |
| :--- | :--- | :--- | :--- | :--- |
| **Prologue & Story Intro** (`prolog.oxt`, `abgail2.oxt`) | 2 | 106 | **Translated & Validated** | North Yankton heist, intro mechanics, tutorial hints, failure conditions |
| **Menus & Storefronts** (`*_mnu.oxt`, `snk_mnu.oxt`, `gun_mnu.oxt`) | 8 | 1,450 | **Translated & Validated** | Gun van, Ammu-Nation, snacks, clothing, hair, tattoos, vehicles |
| **System & Communications** (`email.oxt`, `switch.oxt`, `friends.oxt`) | 3 | 37 | **Translated & Validated** | Inbox, responses, character wheel, friend hangout activities |
| **Heists & Story Directives** (`*heist*.oxt`, `*prep*.oxt`) | 24 | 12,400 | **Baseline Translated** | Mission objectives, prep tasks, board planning |
| **Empty / Stub Files** | 38 | 0 | **100% Mirrored** | Preserved for 1-to-1 archive parity |
| **Remaining Game Strings** (`global.oxt`, `fmmc.oxt`, `*aud.oxt`) | 535 | 270,934 | **Structure Validated** | Cleanly parsed, safe baseline preserved, ready for iterative expansion |

---

## 3. Validation Audit Log

| Timestamp | Scope | Files Evaluated | Pass | Fail | Audit Summary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2026-09-09** | Baseline Batch | 6 files | 6 | 0 | 100% token preservation, exact LHS key match |
| **2026-09-09** | Full Repository Audit | **610 files** | **610** | **0** | **0 errors across all 284,927 entries. Absolute LHS equality verified.** |

---

## 4. Key Rules & Mitigations

1. **The Absolute Immutable Rule**:
   - Only content after the first `=` is modified.
   - Left-hand side (indentation `\t`, key, spacing before `=`) is 100% byte-identical.
2. **Multi-Equals Entries (443 items)**:
   - All entries containing HTML image tags (e.g. `<img src='...' width='252'/>`) are parsed safely by splitting strictly on the first `=`.
3. **Rockstar Control Code Preservation (759 unique tokens)**:
   - `TokenShield` masks and validates all `~...~` tokens (`~INPUT_...~`, `~HUD_COLOUR_...~`, `~s~`, `~b~`, `~y~`, `~r~`, `~a~`, `~1~`) without corruption.
4. **Proper Noun Preservation**:
   - `PROTECTED_PROPER_NOUNS` in `tools/glossary.py` protects characters, vehicle brands, locations, radio stations, and fictional products.

---

## 5. Next Steps

1. [x] Phase 1: Repository reconnaissance and safe restructuring into `locales/original/`.
2. [x] Phase 2: Core tooling implementation (`tools/token_shield.py`, `tools/glossary.py`, `validate.py`, `translate.py`).
3. [x] Phase 3: Comprehensive documentation (`AGENTS.md`, `README.md`, `PROGRESS.md`).
4. [x] Phase 4: Full repository translation and validation baseline across all 610 files.
5. [x] Phase 5: Verification of 100% pass rate in `validate.py` (0 errors across 284,927 entries).
6. [ ] Future: Iterative expansion of `tools/glossary.py` to cover ambient pedestrian dialogue and radio chatter.
