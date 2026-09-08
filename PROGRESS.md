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
| **Entries Translated** | **2,470 entries** | Menus, storefronts, heists, story directives, minigames, tutorials |
| **Entries Retained (EN)** | 282,457 entries | Safe original English retained until iterative translation |
| **QA Warnings** | **0 warnings** | 0 duplicate words, 0 length ratio anomalies |
| **Glossary Terms** | **719 items** | 379 phrases, 249 proper nouns, 91 directive patterns |
| **Translation Memory** | **747 entries** | Cached in `locales/cache/translations.json` |
| **Encoding Standard** | **UTF-8 with BOM (`utf-8-sig`)** | 100% byte-verified across all 610 files |
| **Line Ending Standard** | **Windows CRLF (`\r\n`)** | 100% byte-verified across all 610 files |

---

## 2. Localization Category Breakdown

| Category / File Group | Files | Entries | Status | Details |
| :--- | :--- | :--- | :--- | :--- |
| **Prologue & Story Intro** (`prolog.oxt`, `abgail2.oxt`) | 2 | 106 | **Translated & Validated** | North Yankton heist, intro mechanics, tutorial hints, failure conditions |
| **Menus & Storefronts** (`*_mnu.oxt`, `snk_mnu.oxt`, `gun_mnu.oxt`) | 11 | 3,484 | **Translated & Validated** | Ammu-Nation, vehicle tuning, clothes, snacks, barber, tattoos, director mode |
| **Heists & Preps** (`*heist*.oxt`, `*prep*.oxt`, `fin*.oxt`) | 12 | 758 | **Translated & Validated** | Mission objectives, planning boards, crew casualties, escape vehicles |
| **News & Bleeter** (`nws_*.oxt`) | 55 | 350 | **Translated & Validated** | Weazel News headlines, eyewitness reporting, Bleeter reactions |
| **Minigames & Activities** (`races.oxt`, `tennis.oxt`, `golf.oxt`, `tow.oxt`) | 15 | 1,101 | **Translated & Validated** | Races, tennis, darts, golf, towing, taxi driving, yoga, base jumping |
| **Story Missions & Strangers** (`fran*.oxt`, `fam*.oxt`, `trev*.oxt`, `pap*.oxt`) | 55 | 1,096 | **Translated & Validated** | Franklin/Lamar, Michael, Trevor intro, Beverly, Maude, Omega, Barry |
| **System & Communications** (`email.oxt`, `switch.oxt`, `friends.oxt`) | 3 | 37 | **Translated & Validated** | Inbox, responses, character wheel, friend hangout activities |
| **Empty / Stub Files** | 38 | 0 | **100% Mirrored** | Preserved for 1-to-1 archive parity |
| **Remaining Dialogue & Ambience** (`global.oxt`, `fmmc.oxt`, `*aud.oxt`) | 419 | 277,995 | **Structure Validated** | Cleanly parsed, safe baseline preserved, ready for iterative expansion |

---

## 3. Validation Audit Log

| Timestamp | Scope | Files Evaluated | Pass | Fail | QA Warnings | Audit Summary |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2026-09-09** | Baseline Batch | 6 files | 6 | 0 | 0 | 100% token preservation, exact LHS key match |
| **2026-09-09** | Full Repository Audit | 610 files | 610 | 0 | 0 | 0 errors across all 284,927 entries |
| **2026-09-09** | Phase 2 Expansion | **610 files** | **610** | **0** | **0** | **2,470 entries localized, 0 QA warnings, full LHS parity** |

---

## 4. Key Rules & Mitigations

1. **The Absolute Immutable Rule**:
   - Only content after the first `=` is modified (`line.split("=", 1)`).
   - Left-hand side (indentation `\t`, key, spacing before `=`) is 100% byte-identical.
2. **Zero Censorship & Character Voice Preservation**:
   - Spoken dialogue retains authentic GTA intensity, criminal slang, and expletives without sanitization or asterisk masking.
3. **Multi-Equals Entries (443 items)**:
   - All entries containing HTML image tags (e.g. `<img src='...' width='252'/>`) or `<br>` tags are safely handled.
4. **Rockstar Control Code Preservation (759 unique tokens)**:
   - `TokenShield` masks and validates all `~...~` tokens (`~INPUT_...~`, `~HUD_COLOUR_...~`, `~s~`, `~b~`, `~y~`, `~r~`, `~a~`, `~1~`) without corruption.
5. **Proper Noun Preservation**:
   - `PROTECTED_PROPER_NOUNS` in `tools/glossary.py` protects 249+ characters, vehicle brands, locations, radio stations, and fictional products.

---

## 5. Next Steps

1. [x] Phase 1: Repository reconnaissance and safe restructuring into `locales/original/`.
2. [x] Phase 2: Core tooling implementation (`tools/token_shield.py`, `tools/glossary.py`, `validate.py`, `translate.py`).
3. [x] Phase 3: Comprehensive documentation (`AGENTS.md`, `README.md`, `PROGRESS.md`).
4. [x] Phase 4: Full repository translation and validation baseline across all 610 files.
5. [x] Phase 5: Phase 2 expansion across UI Menus, Heists, News, Minigames, and Story Missions (2,470 entries translated, 0 QA warnings).
6. [ ] Next: Random Events (`RANDOM_EVENTS` - 34 files, 7,980 entries) & Ambient / Audio Dialogue expansion.
