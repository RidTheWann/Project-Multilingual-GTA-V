#!/usr/bin/env python3
"""
GTA V Indonesian Localization Translation Pipeline.
Safely extracts text after '=', shields Rockstar tokens/placeholders, applies glossary/rules,
and writes UTF-8 BOM CRLF .oxt files to locales/id/ without modifying original files.
Includes:
- Modular glossary and directive resolver
- Proper noun contextual preservation
- Batch export and application engine
- Resumable translation memory cache
"""

import os
import sys
import glob
import json
import re
import argparse
from datetime import datetime, timezone
from typing import Dict, Tuple, List, Optional, Any

from tools.token_shield import TokenShield
from tools.glossary import (
    PROTECTED_PROPER_NOUNS,
    EXACT_PHRASES,
    COMMON_NOUNS_AND_LOCATIONS,
    MISSION_DIRECTIVE_PATTERNS,
)

class TranslationEngine:
    def __init__(self, cache_file: str = "locales/cache/translations.json"):
        self.shield = TokenShield()
        self.cache_file = cache_file
        self.cache: Dict[str, Any] = {}
        self.load_cache()

        # Compile mission directive regexes
        self.compiled_patterns = [
            (re.compile(pat, re.IGNORECASE), repl) for pat, repl in MISSION_DIRECTIVE_PATTERNS
        ]

    def load_cache(self):
        if os.path.isfile(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    # Normalize cache: support both direct string and rich record
                    for k, v in raw_data.items():
                        if isinstance(v, dict) and "target" in v:
                            self.cache[k] = v["target"]
                        elif isinstance(v, str):
                            self.cache[k] = v
            except Exception as e:
                print(f"Warning: Failed to load translation cache: {e}")
                self.cache = {}

    def save_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save translation cache: {e}")

    def _resolve_colored_noun(self, color_token: str, english_noun: str) -> str:
        """Translate the noun inside ~y~noun~s~ or ~b~noun~s~ cleanly."""
        clean = english_noun.strip().lower()
        if clean in COMMON_NOUNS_AND_LOCATIONS:
            return f"{color_token}{COMMON_NOUNS_AND_LOCATIONS[clean]}~s~"
        elif english_noun.strip() in PROTECTED_PROPER_NOUNS:
            return f"{color_token}{english_noun.strip()}~s~"
        return f"{color_token}{english_noun.strip()}~s~"

    def _resolve_dynamic_directive(self, text: str) -> Optional[str]:
        """Resolves common dynamic mission directives with color tokens."""
        # 1. "Go to the ~y~exit.~s~" / "Go to the ~y~server room.~s~"
        m = re.match(r"^Go to the (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Pergilah ke {colored}."

        # 2. "Go to ~y~exit~s~."
        m = re.match(r"^Go to (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Pergilah ke {colored}."

        # 3. "Follow ~b~Trevor.~s~" / "Follow ~b~Lamar.~s~"
        m = re.match(r"^Follow (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Ikuti {colored}."

        # 4. "Wait for ~b~Trevor~s~ to get to the car.~s~"
        m = re.match(r"^Wait for (~[byrg]~)([^~]+)(~s~) to get to the car\.?(~s~)?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Tunggu {colored} sampai di mobil."

        # 5. "Wait for the ~b~crew~s~ to get in the car.~s~"
        m = re.match(r"^Wait for (?:the )?(~[byrg]~)([^~]+)(~s~) to get in the car\.?(~s~)?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Tunggu {colored} masuk ke dalam mobil."

        # 6. "Wait for the ~b~crew.~s~"
        m = re.match(r"^Wait for (?:the )?(~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Tunggu {colored}."

        # 7. "Grab the ~b~woman.~s~"
        m = re.match(r"^Grab the (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Tangkap {colored}."

        # 8. "Shoot the ~r~monitors.~s~"
        m = re.match(r"^Shoot the (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Tembak {colored}."

        # 9. "Get back in the ~b~fire truck.~s~"
        m = re.match(r"^Get back in the (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Masuklah kembali ke dalam {colored}."

        # 10. "Collect the ~g~cash.~s~"
        m = re.match(r"^Collect the (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Ambil {colored}."

        # 11. "Take out the ~r~guard.~s~"
        m = re.match(r"^Take out the (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Lumpuhkan {colored}."

        # 12. "Open the ~g~shutter door.~s~"
        m = re.match(r"^Open the (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Buka {colored}."

        # 13. "Return to the ~b~crew.~s~"
        m = re.match(r"^Return to (?:the )?(~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Kembalilah ke {colored}."

        # 14. "Get to the ~b~car.~s~"
        m = re.match(r"^Get to the (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Capailah {colored}."

        # 15. "Get back in the ~b~car.~s~"
        m = re.match(r"^Get back in the (~[byrg]~)([^~]+)(~s~)\.?$", text, re.IGNORECASE)
        if m:
            colored = self._resolve_colored_noun(m.group(1), m.group(2))
            return f"Masuklah kembali ke dalam {colored}."

        return None

    def _match_and_translate_phrase(self, text: str) -> Optional[str]:
        """Attempt to translate text using glossary, patterns, and token masking."""
        stripped = text.strip()
        if not stripped:
            return None

        # 1. Exact phrase glossary
        if stripped in EXACT_PHRASES:
            return EXACT_PHRASES[stripped]

        # 2. Dynamic directive resolver (handles colored tokens cleanly)
        dyn = self._resolve_dynamic_directive(stripped)
        if dyn is not None:
            is_valid, _ = self.shield.verify_tokens(stripped, dyn)
            if is_valid:
                return dyn

        # 3. Compiled mission directive patterns
        for pat, repl in self.compiled_patterns:
            if pat.search(stripped):
                translated = pat.sub(repl, stripped)
                is_valid, _ = self.shield.verify_tokens(stripped, translated)
                if is_valid:
                    return translated

        # 4. Check with trailing punctuation removed (. ! ?)
        if stripped[-1] in (".", "!", "?") and len(stripped) > 2:
            punc = stripped[-1]
            base = stripped[:-1].strip()
            if base in EXACT_PHRASES:
                cand = EXACT_PHRASES[base] + punc
                is_valid, _ = self.shield.verify_tokens(stripped, cand)
                if is_valid:
                    return cand

        # 5. Token-masked exact phrase lookup
        masked, token_map = self.shield.mask(stripped)
        untokenized_clean = masked
        for marker in token_map.keys():
            untokenized_clean = untokenized_clean.replace(marker, "").strip()

        if untokenized_clean and untokenized_clean in EXACT_PHRASES:
            id_trans = EXACT_PHRASES[untokenized_clean]
            masked_trans = masked.replace(untokenized_clean, id_trans)
            candidate = self.shield.unmask(masked_trans, token_map)
            is_valid, _ = self.shield.verify_tokens(stripped, candidate)
            if is_valid:
                return candidate

        return None

    def translate_text(self, original_text: str) -> str:
        """
        Translates the extracted text after '='.
        Guarantees that tokens and proper nouns are preserved.
        """
        stripped = original_text.strip()
        if not stripped:
            return original_text

        # 1. If text is token-only (e.g. ~a~, ~z~, ~n~), keep as is
        if self.shield.is_token_only(stripped):
            return original_text

        # 2. Check if text is a standalone protected proper noun
        clean_text = re.sub(r"~[^~]+~", "", stripped).strip()
        if clean_text in PROTECTED_PROPER_NOUNS:
            return original_text

        # 3. Check translation cache
        if stripped in self.cache:
            cand = self.cache[stripped]
            is_valid, _ = self.shield.verify_tokens(stripped, cand)
            if is_valid:
                leading_ws = original_text[: len(original_text) - len(original_text.lstrip())]
                trailing_ws = original_text[len(original_text.rstrip()) :]
                return f"{leading_ws}{cand}{trailing_ws}"

        # 4. Attempt direct phrase translation
        candidate = self._match_and_translate_phrase(stripped)
        if candidate is not None:
            is_valid, _ = self.shield.verify_tokens(stripped, candidate)
            if is_valid:
                self.cache[stripped] = candidate
                leading_ws = original_text[: len(original_text) - len(original_text.lstrip())]
                trailing_ws = original_text[len(original_text.rstrip()) :]
                return f"{leading_ws}{candidate}{trailing_ws}"

        # 5. Check if wrapped in ~s~...~s~ (or with punctuation like ~s~. or ~s~!)
        if stripped.startswith("~s~"):
            for end_marker in ("~s~", "~s~.", "~s~!", "~s~?"):
                if stripped.endswith(end_marker):
                    inner = stripped[3 : -len(end_marker)]
                    trailing_punc = end_marker[3:]
                    inner_candidate = self._match_and_translate_phrase(inner)
                    if inner_candidate is not None:
                        reconstructed = f"~s~{inner_candidate}~s~{trailing_punc}"
                        is_valid, _ = self.shield.verify_tokens(stripped, reconstructed)
                        if is_valid:
                            self.cache[stripped] = reconstructed
                            leading_ws = original_text[: len(original_text) - len(original_text.lstrip())]
                            trailing_ws = original_text[len(original_text.rstrip()) :]
                            return f"{leading_ws}{reconstructed}{trailing_ws}"

        # 6. Check if preceded by subtitle delay token ~z~ (e.g. in *aud.oxt files)
        if stripped.startswith("~z~"):
            inner = stripped[3:].strip()
            inner_candidate = self._match_and_translate_phrase(inner)
            if inner_candidate is not None:
                reconstructed = f"~z~{inner_candidate}"
                is_valid, _ = self.shield.verify_tokens(stripped, reconstructed)
                if is_valid:
                    self.cache[stripped] = reconstructed
                    leading_ws = original_text[: len(original_text) - len(original_text.lstrip())]
                    trailing_ws = original_text[len(original_text.rstrip()) :]
                    return f"{leading_ws}{reconstructed}{trailing_ws}"

        # If not confidently translatable yet, safely return original text
        return original_text

class LocalizationProcessor:
    def __init__(self, original_dir: str = "locales/original", translated_dir: str = "locales/id"):
        self.original_dir = original_dir
        self.translated_dir = translated_dir
        self.engine = TranslationEngine()

    def process_file(self, filename: str, dry_run: bool = False) -> Dict[str, Any]:
        orig_path = os.path.join(self.original_dir, filename)
        trans_path = os.path.join(self.translated_dir, filename)

        stats = {
            "filename": filename,
            "total_entries": 0,
            "translated_entries": 0,
            "unchanged_entries": 0,
            "status": "PROCESSED",
        }

        if not os.path.isfile(orig_path):
            stats["status"] = f"ERROR: File not found: {orig_path}"
            return stats

        with open(orig_path, "rb") as bf:
            raw = bf.read()

        content = raw.decode("utf-8-sig")
        lines = content.splitlines(keepends=False)

        out_lines = []
        in_block = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                out_lines.append(line)
                continue

            if stripped.startswith("Version "):
                out_lines.append(line)
                continue

            if stripped == "{":
                in_block = True
                out_lines.append(line)
                continue

            if stripped == "}":
                in_block = False
                out_lines.append(line)
                continue

            if in_block and "=" in line:
                stats["total_entries"] += 1
                # Split STRICTLY on the first '='
                parts = line.split("=", 1)
                prefix = parts[0] + "="
                val = parts[1]

                trans_val = self.engine.translate_text(val)

                if trans_val.strip() != val.strip():
                    stats["translated_entries"] += 1
                else:
                    stats["unchanged_entries"] += 1

                # Reassemble: strictly preserve LHS prefix and '='
                out_lines.append(prefix + trans_val)
            else:
                out_lines.append(line)

        if not dry_run:
            os.makedirs(os.path.dirname(trans_path), exist_ok=True)
            output_text = "\r\n".join(out_lines) + "\r\n"
            with open(trans_path, "wb") as out_f:
                out_f.write(b"\xef\xbb\xbf")
                out_f.write(output_text.encode("utf-8"))

        return stats

    def process_all(
        self,
        files: Optional[List[str]] = None,
        pattern: Optional[str] = None,
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        all_orig_files = [os.path.basename(f) for f in glob.glob(os.path.join(self.original_dir, "*.oxt"))]

        if files:
            target_files = files
        elif pattern:
            import fnmatch
            target_files = [f for f in all_orig_files if fnmatch.fnmatch(f, pattern)]
        else:
            target_files = sorted(all_orig_files)

        results = []
        entries_done = 0

        for f in target_files:
            stat = self.process_file(f, dry_run=dry_run)
            results.append(stat)
            entries_done += stat["total_entries"]

            if limit and entries_done >= limit:
                print(f"Reached entry limit of {limit}. Stopping batch.")
                break

        if not dry_run:
            self.engine.save_cache()

        return results

    def export_batch(self, category: Optional[str] = None, files: Optional[List[str]] = None, max_entries: int = 500, output_path: str = "reports/batches/batch_input.json"):
        """Exports untranslated strings with context for native agent translation."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        all_orig_files = sorted([os.path.basename(f) for f in glob.glob(os.path.join(self.original_dir, "*.oxt"))])
        
        target_files = files if files else all_orig_files
        batch_items = []

        token_only_pat = re.compile(r"^(?:~[^~]+~|\s|%[0-9]*[a-zA-Z]|\{[0-9]+\}|<[^>]+>)+$")
        tech_pat = re.compile(r"^(?:[A-Z0-9_]{16,}|[a-z0-9_]+\.(?:dds|png|gfx|bik|awc)|0x[0-9a-fA-F]{8})$")

        for fname in target_files:
            fpath = os.path.join(self.original_dir, fname)
            tpath = os.path.join(self.translated_dir, fname)
            if not os.path.isfile(fpath) or not os.path.isfile(tpath):
                continue

            with open(fpath, "r", encoding="utf-8-sig") as of, open(tpath, "r", encoding="utf-8-sig") as tf:
                o_lines = [l.strip() for l in of if "=" in l and not l.strip().startswith("Version ")]
                t_lines = [l.strip() for l in tf if "=" in l and not l.strip().startswith("Version ")]

            for o_line, t_line in zip(o_lines, t_lines):
                k = o_line.split("=", 1)[0].strip()
                o_val = o_line.split("=", 1)[1].strip()
                t_val = t_line.split("=", 1)[1].strip()

                if o_val == t_val:
                    # Check if genuinely translatable
                    clean = re.sub(r"~[^~]+~", "", o_val).strip()
                    if not o_val or token_only_pat.match(o_val) or tech_pat.match(clean) or clean in PROTECTED_PROPER_NOUNS:
                        continue

                    batch_items.append({
                        "file": fname,
                        "key": k,
                        "source": o_val,
                        "clean_text": clean,
                    })

                    if len(batch_items) >= max_entries:
                        break
            if len(batch_items) >= max_entries:
                break

        with open(output_path, "w", encoding="utf-8") as bf:
            json.dump({
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "total_items": len(batch_items),
                "items": batch_items
            }, bf, indent=2, ensure_ascii=False)

        print(f"Exported {len(batch_items)} untranslated entries to {output_path}")

    def apply_batch(self, batch_file: str, dry_run: bool = False):
        """Applies translations from a translated batch JSON file, updates TM and target files."""
        if not os.path.isfile(batch_file):
            print(f"Error: Batch file not found: {batch_file}")
            return

        with open(batch_file, "r", encoding="utf-8") as bf:
            data = json.load(bf)

        items = data.get("items", [])
        print(f"Applying {len(items)} translations from {batch_file}...")

        applied_count = 0
        error_count = 0
        files_to_touch = set()

        for item in items:
            src = item.get("source", "").strip()
            target = item.get("target", "").strip()
            fname = item.get("file")

            if not src or not target or src == target:
                continue

            # Validate token parity
            is_valid, errs = self.engine.shield.verify_tokens(src, target)
            if not is_valid:
                print(f"Token error for '{src}': {errs}")
                error_count += 1
                continue

            # Store in Translation Memory
            self.engine.cache[src] = target
            applied_count += 1
            if fname:
                files_to_touch.add(fname)

        if not dry_run:
            self.engine.save_cache()
            # Reprocess affected files to write changes
            for fn in files_to_touch:
                self.process_file(fn, dry_run=False)

        print(f"Batch applied successfully: {applied_count} translations recorded, {error_count} rejected.")

def main():
    parser = argparse.ArgumentParser(description="GTA V Indonesian Translation Processor")
    parser.add_argument("--original-dir", default="locales/original", help="Source original .oxt directory")
    parser.add_argument("--translated-dir", default="locales/id", help="Target translated .oxt directory")
    parser.add_argument("--files", nargs="*", help="Specific files to process")
    parser.add_argument("--all", action="store_true", help="Process all files in locales/original")
    parser.add_argument("--pattern", help="Glob pattern for files to process (e.g. '*heist*')")
    parser.add_argument("--limit", type=int, help="Maximum number of entries to process")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without writing files")
    parser.add_argument("--validate", action="store_true", help="Run validate.py after translation")
    parser.add_argument("--report", default="reports/translation_batch.json", help="Path for JSON report")
    parser.add_argument("--export-batch", action="store_true", help="Export untranslated batch to JSON")
    parser.add_argument("--batch-size", type=int, default=500, help="Number of entries in exported batch")
    parser.add_argument("--batch-out", default="reports/batches/batch_input.json", help="Export batch output path")
    parser.add_argument("--apply-batch", help="Path to translated batch JSON file to apply")

    args = parser.parse_args()

    processor = LocalizationProcessor(args.original_dir, args.translated_dir)

    if args.export_batch:
        processor.export_batch(files=args.files, max_entries=args.batch_size, output_path=args.batch_out)
        sys.exit(0)

    if args.apply_batch:
        processor.apply_batch(args.apply_batch, dry_run=args.dry_run)
        if args.validate:
            from validate import LocalizationValidator
            val = LocalizationValidator(args.original_dir, args.translated_dir)
            audit = val.validate_all()
            if audit["summary"]["failed"] > 0:
                print(f"Validation FAILED: {audit['summary']['failed']} errors.")
                sys.exit(1)
            else:
                print("Validation PASSED for all files.")
        sys.exit(0)

    target_files = args.files
    if not target_files and not args.all and not args.pattern:
        print("Please specify --files, --pattern, --all, --export-batch, or --apply-batch.")
        sys.exit(1)

    print(f"Starting translation run (dry_run={args.dry_run})...")
    results = processor.process_all(
        files=target_files,
        pattern=args.pattern,
        limit=args.limit,
        dry_run=args.dry_run,
    )

    total_files = len(results)
    total_entries = sum(r["total_entries"] for r in results)
    total_translated = sum(r["translated_entries"] for r in results)
    total_unchanged = sum(r["unchanged_entries"] for r in results)

    print("=" * 60)
    print("GTA V TRANSLATION RUN SUMMARY")
    print("=" * 60)
    print(f"Files Processed:    {total_files}")
    print(f"Total Entries:      {total_entries}")
    print(f"Entries Translated: {total_translated}")
    print(f"Entries Unchanged:  {total_unchanged}")
    print("=" * 60)

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as rf:
        json.dump(
            {
                "summary": {
                    "files_processed": total_files,
                    "total_entries": total_entries,
                    "translated_entries": total_translated,
                    "unchanged_entries": total_unchanged,
                    "dry_run": args.dry_run,
                },
                "results": results,
            },
            rf,
            indent=2,
        )

    if args.validate and not args.dry_run:
        print("\nExecuting validation suite on generated files...")
        processed_file_names = [r["filename"] for r in results if r["status"] == "PROCESSED"]
        from validate import LocalizationValidator

        val = LocalizationValidator(args.original_dir, args.translated_dir)
        audit = val.validate_all(processed_file_names)
        val_summary = audit["summary"]
        if val_summary["failed"] > 0:
            print(f"Validation FAILED with {val_summary['failed']} errors.")
            sys.exit(1)
        else:
            print(f"Validation PASSED for all {val_summary['passed']} files.")

if __name__ == "__main__":
    main()
