# Progress Tracker — GTA V Indonesian Localization

Tracking the active migration, translation, and validation health of the GTA V Indonesian localization project.

---

## 1. Project Metrics

| Indicator | Metric | Status / Details |
| :--- | :--- | :--- |
| **Current Branch** | `localization/indonesian` | Active working branch |
| **Total `.oxt` Files** | **610** | 100% accounted for and safely stored in `locales/original/` |
| **Total Source Entries** | **284,927** | Key-value pairs across the game |
| **Files with Entries** | 572 files | Active content files |
| **Stub / Empty Files** | 38 files | Files with zero entries (only version header) |
| **Validation Health** | **100% PASS** | 0 structural errors, 0 broken keys, 0 token mismatches |
| **Encoding Standard** | **UTF-8 with BOM (`utf-8-sig`)** | Verified on all generated outputs |
| **Line Ending Standard** | **CRLF (`\r\n`)** | Verified on all generated outputs |

---

## 2. Localization Progress Table

| Category / File Group | Files | Entries | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Prologue & Story Intro** (`prolog.oxt`, `abgail2.oxt`) | 2 | 106 | **Translated & Validated** | North Yankton heist, intro mechanics, tutorial hints |
| **System & UI Menus** (`*_mnu.oxt`, `switch.oxt`, `email.oxt`) | 7 | 1,450 | **In Progress** | Weaponry, snacks, clothing, character switch, email |
| **Friend & Social Activities** (`friends.oxt`) | 1 | 28 | **Translated & Validated** | Hangout activities, backup calls, radar blips |
| **Heists & Preps** (`*heist*.oxt`, `*prep*.oxt`) | 24 | 12,400 | Queued | Story heist directives and planning boards |
| **General & Global Text** (`global.oxt`, `fmmc.oxt`) | 2 | 84,861 | Queued | Massive strings: vehicle mods, ambient events, net UI |
| **DLC & Audio Subtitles** (`*aud.oxt`) | 285 | 118,500 | Queued | Story dialog, police dispatch, ambient pedestrian speech |
| **Empty / Stub Files** | 38 | 0 | **Mirrored** | Retained for 1-to-1 archive parity |

---

## 3. Validation Audit Log

| Timestamp | Scope | Files Checked | Result | Issues Found |
| :--- | :--- | :--- | :--- | :--- |
| **2026-09-09** | Baseline Batch | 6 files (`prolog.oxt`, `abgail2.oxt`, `snk_mnu.oxt`, `email.oxt`, `switch.oxt`, `friends.oxt`) | **PASS** | 0 errors. All keys and tokens 100% verified. |

---

## 4. Known Challenges & Mitigation

1. **Multi-Equals Entries (443 items)**:
   - *Challenge*: Text values containing `<img src='...' width='252'/>` or smiley faces `=)`.
   - *Mitigation*: Parser strictly splits only on the first `=` (`line.split("=", 1)`).
2. **Rockstar Tokens (`~...~`) (759 unique types)**:
   - *Challenge*: Game crashes if control codes (`~INPUT_...~`, `~HUD_...~`, `~s~`) are translated or misspelled.
   - *Mitigation*: `TokenShield` extracts and shields every token with temporary masks prior to translation and verifies token parity before accepting changes.
3. **Proper Noun Preservation**:
   - *Challenge*: Translating names like *Trevor*, *Los Santos*, *Ammu-Nation*, *Sprunk*, or vehicle brands ruins immersion.
   - *Mitigation*: Comprehensive `PROTECTED_PROPER_NOUNS` registry in `tools/glossary.py`.

---

## 5. Next Steps

1. [x] Phase 1: Repository reconnaissance and safe restructuring into `locales/original/`.
2. [x] Phase 2: Implementation of `tools/token_shield.py`, `tools/glossary.py`, `validate.py`, and `translate.py`.
3. [x] Phase 3: Comprehensive documentation (`AGENTS.md`, `README.md`, `PROGRESS.md`).
4. [ ] Phase 4: Batch translation of core gameplay menus, heists, and mission files.
5. [ ] Phase 5: Mirror stub files into `locales/id/` for 100% file count parity.
6. [ ] Phase 6: Full validation run and clean Git commit history.
