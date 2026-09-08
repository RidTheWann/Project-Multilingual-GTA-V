#!/usr/bin/env python3
"""
GTA V Indonesian Localization Translation Pipeline.
Safely extracts text after '=', shields Rockstar tokens/placeholders, applies glossary/rules,
and writes UTF-8 BOM CRLF .oxt files to locales/id/ without modifying original files.
"""

import os
import sys
import glob
import json
import re
import argparse
from typing import Dict, Tuple, List, Optional, Any

from tools.token_shield import TokenShield
from tools.glossary import (
    PROTECTED_PROPER_NOUNS,
    EXACT_PHRASE_GLOSSARY,
    MISSION_DIRECTIVE_PATTERNS,
)

class TranslationEngine:
    def __init__(self, cache_file: str = "locales/cache/translations.json"):
        self.shield = TokenShield()
        self.cache_file = cache_file
        self.cache: Dict[str, str] = {}
        self.load_cache()

        # Compile mission directive regexes
        self.compiled_patterns = [
            (re.compile(pat, re.IGNORECASE), repl) for pat, repl in MISSION_DIRECTIVE_PATTERNS
        ]

    def load_cache(self):
        if os.path.isfile(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
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

    def _match_and_translate_phrase(self, text: str) -> Optional[str]:
        """Attempt to translate text using glossary, patterns, and token masking."""
        stripped = text.strip()
        if not stripped:
            return None

        # 1. Check exact phrase glossary
        if stripped in EXACT_PHRASE_GLOSSARY:
            return EXACT_PHRASE_GLOSSARY[stripped]

        # 2. Check compiled mission directive patterns
        for pat, repl in self.compiled_patterns:
            if pat.search(stripped):
                translated = pat.sub(repl, stripped)
                is_valid, _ = self.shield.verify_tokens(stripped, translated)
                if is_valid:
                    return translated

        # 3. Check token-masked exact phrase lookup
        masked, token_map = self.shield.mask(stripped)
        untokenized_clean = masked
        for marker in token_map.keys():
            untokenized_clean = untokenized_clean.replace(marker, "").strip()

        if untokenized_clean and untokenized_clean in EXACT_PHRASE_GLOSSARY:
            id_trans = EXACT_PHRASE_GLOSSARY[untokenized_clean]
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

        # 2. Check if text is a protected proper noun (e.g. character, car, radio, location)
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

        # 5. Check if wrapped in ~s~...~s~
        if stripped.startswith("~s~") and (stripped.endswith("~s~") or stripped.endswith("~s~.")):
            has_trailing_period = stripped.endswith("~s~.")
            inner = stripped[3:-3] if not has_trailing_period else stripped[3:-4]
            inner_candidate = self._match_and_translate_phrase(inner)
            if inner_candidate is not None:
                reconstructed = (
                    f"~s~{inner_candidate}~s~." if has_trailing_period else f"~s~{inner_candidate}~s~"
                )
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

def main():
    parser = argparse.ArgumentParser(description="GTA V Indonesian Translation Processor")
    parser.add_argument("--original-dir", default="locales/original", help="Source original .oxt directory")
    parser.add_argument("--translated-dir", default="locales/id", help="Target translated .oxt directory")
    parser.add_argument("--files", nargs="*", help="Specific files to process (e.g. prolog.oxt abgail2.oxt)")
    parser.add_argument("--all", action="store_true", help="Process all files in locales/original")
    parser.add_argument("--pattern", help="Glob pattern for files to process (e.g. '*heist*')")
    parser.add_argument("--limit", type=int, help="Maximum number of entries to process")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without writing files")
    parser.add_argument("--validate", action="store_true", help="Run validate.py after translation")
    parser.add_argument("--report", default="reports/translation_batch.json", help="Path for JSON report")

    args = parser.parse_args()

    processor = LocalizationProcessor(args.original_dir, args.translated_dir)

    target_files = args.files
    if not target_files and not args.all and not args.pattern:
        print("Please specify --files, --pattern, or --all.")
        print("Example: python translate.py --files prolog.oxt abgail2.oxt")
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
    print(f"Translation run report saved to {args.report}")

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
