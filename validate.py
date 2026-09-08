#!/usr/bin/env python3
"""
GTA V Localization Validation & Quality Assurance Suite.
Strictly verifies:
1. Absolute LHS key identity (indentation, key name, spacing before '=')
2. Key count, ordering, and 0 missing/added keys
3. Exact token, placeholder, markup, and escape sequence parity
4. File encoding (UTF-8 with BOM) and CRLF line endings
5. Quality Assurance heuristics (duplicate words, abnormal length ratios, untranslated English)
"""

import os
import sys
import glob
import json
import re
import argparse
from typing import List, Dict, Tuple, Any, Set

from tools.token_shield import TokenShield

shield = TokenShield()

# Regex to detect consecutive duplicated words (e.g. "dan dan", "ke ke", "di di")
DUPLICATE_WORDS_REGEX = re.compile(r"\b([a-zA-Z]{3,})\s+\1\b", re.IGNORECASE)

class LocalizationValidator:
    def __init__(self, original_dir: str = "locales/original", translated_dir: str = "locales/id"):
        self.original_dir = original_dir
        self.translated_dir = translated_dir

    def parse_oxt_file(self, filepath: str) -> Tuple[List[str], List[Tuple[str, str, str]], List[str]]:
        """
        Parses an .oxt file.
        Returns:
            headers: lines outside { ... } (e.g. Version 2 30)
            entries: list of (full_prefix_with_key_and_spacing, key_name, value_text)
            errors: structural parsing errors
        """
        errors = []
        headers = []
        entries = []
        seen_keys = set()

        if not os.path.isfile(filepath):
            errors.append(f"File does not exist: {filepath}")
            return headers, entries, errors

        with open(filepath, "rb") as bf:
            raw = bf.read()

        # 1. Byte-level checks: Encoding (BOM) & Line Endings
        if not raw.startswith(b"\xef\xbb\xbf"):
            errors.append("Encoding Error: Missing UTF-8 BOM (0xEF 0xBB 0xBF)")

        if b"\r\n" not in raw and len(raw) > 30:
            errors.append("Line Ending Error: File does not use CRLF line endings")

        # 2. Text decoding
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            errors.append(f"Decoding Error: Failed to decode utf-8-sig: {e}")
            return headers, entries, errors

        lines = content.splitlines(keepends=False)
        in_block = False

        for line_no, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("Version "):
                headers.append(stripped)
                continue

            if stripped == "{":
                if in_block:
                    errors.append(f"Line {line_no}: Unexpected nested opening brace '{{'")
                in_block = True
                continue

            if stripped == "}":
                if not in_block:
                    errors.append(f"Line {line_no}: Unexpected closing brace '}}' outside block")
                in_block = False
                continue

            if in_block:
                if "=" not in line:
                    errors.append(f"Line {line_no}: Missing '=' delimiter: {repr(line)}")
                    continue

                # Split STRICTLY on the first '='
                parts = line.split("=", 1)
                prefix = parts[0] + "="
                key_name = parts[0].strip()
                val_text = parts[1]

                if not key_name:
                    errors.append(f"Line {line_no}: Empty key before '='")
                    continue

                if key_name in seen_keys:
                    errors.append(f"Line {line_no}: Duplicate key '{key_name}' detected")
                seen_keys.add(key_name)

                entries.append((prefix, key_name, val_text))
            else:
                errors.append(f"Line {line_no}: Content outside braces: {repr(line)}")

        return headers, entries, errors

    def validate_pair(self, filename: str) -> Dict[str, Any]:
        orig_path = os.path.join(self.original_dir, filename)
        trans_path = os.path.join(self.translated_dir, filename)

        result: Dict[str, Any] = {
            "filename": filename,
            "status": "PASS",
            "errors": [],
            "warnings": [],
            "qa_warnings": [],
            "total_entries": 0,
            "translated_entries": 0,
            "identical_entries": 0,
        }

        if not os.path.isfile(trans_path):
            result["status"] = "FAIL"
            result["errors"].append(f"Translated file missing in {self.translated_dir}")
            return result

        orig_headers, orig_entries, orig_errs = self.parse_oxt_file(orig_path)
        trans_headers, trans_entries, trans_errs = self.parse_oxt_file(trans_path)

        if orig_errs:
            result["warnings"].extend([f"Original source issue: {e}" for e in orig_errs])
        if trans_errs:
            result["status"] = "FAIL"
            result["errors"].extend(trans_errs)

        # Header check
        if orig_headers != trans_headers:
            result["status"] = "FAIL"
            result["errors"].append(f"Header mismatch: Expected {orig_headers}, got {trans_headers}")

        result["total_entries"] = len(orig_entries)
        if len(orig_entries) != len(trans_entries):
            result["status"] = "FAIL"
            result["errors"].append(
                f"Entry count mismatch: Original has {len(orig_entries)} entries, translated has {len(trans_entries)} entries"
            )
            return result

        # Strict Key & LHS Matching + Token & QA Checks
        for idx, ((orig_prefix, orig_key, orig_val), (trans_prefix, trans_key, trans_val)) in enumerate(
            zip(orig_entries, trans_entries)
        ):
            # 1. Exact key equality
            if orig_key != trans_key:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Entry {idx + 1}: Key modified! Original '{orig_key}' != Translated '{trans_key}'"
                )
                continue

            # 2. Exact LHS prefix equality (indentation and spacing before '=')
            if orig_prefix != trans_prefix:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Entry {idx + 1} ({orig_key}): LHS prefix mismatch! "
                    f"Original {repr(orig_prefix)} != Translated {repr(trans_prefix)}"
                )

            # 3. Token & placeholder parity
            is_valid, token_errs = shield.verify_tokens(orig_val, trans_val)
            if not is_valid:
                result["status"] = "FAIL"
                for terr in token_errs:
                    result["errors"].append(f"Entry {idx + 1} ({orig_key}): {terr}")

            # 4. Translation status tracking
            orig_clean = orig_val.strip()
            trans_clean = trans_val.strip()

            if orig_clean == trans_clean:
                result["identical_entries"] += 1
            else:
                result["translated_entries"] += 1

                # QA Heuristic 1: Accidental duplicate words (e.g. "dan dan", "ke ke")
                dup_match = DUPLICATE_WORDS_REGEX.search(trans_clean)
                if dup_match:
                    result["qa_warnings"].append(
                        f"Entry {idx + 1} ({orig_key}): Possible duplicate word '{dup_match.group(0)}'"
                    )

                # QA Heuristic 2: Extreme length ratio anomaly (> 3.5x longer or < 0.25x shorter on long strings)
                if len(orig_clean) > 25:
                    ratio = len(trans_clean) / len(orig_clean)
                    if ratio > 3.5:
                        result["qa_warnings"].append(
                            f"Entry {idx + 1} ({orig_key}): Suspiciously long translation ({len(trans_clean)} vs {len(orig_clean)} chars)"
                        )
                    elif ratio < 0.25:
                        result["qa_warnings"].append(
                            f"Entry {idx + 1} ({orig_key}): Suspiciously short translation ({len(trans_clean)} vs {len(orig_clean)} chars)"
                        )

        if result["errors"]:
            result["status"] = "FAIL"

        return result

    def validate_all(self, target_files: List[str] = None) -> Dict[str, Any]:
        if not target_files:
            orig_files = set(os.path.basename(f) for f in glob.glob(os.path.join(self.original_dir, "*.oxt")))
            trans_files = set(os.path.basename(f) for f in glob.glob(os.path.join(self.translated_dir, "*.oxt")))

            missing_in_target = orig_files - trans_files
            unexpected_in_target = trans_files - orig_files

            files_to_check = sorted(list(trans_files))
        else:
            files_to_check = target_files
            missing_in_target = set()
            unexpected_in_target = set()

        results = []
        passed = 0
        failed = 0
        total_orig_entries = 0
        total_trans_entries = 0
        total_identical = 0
        total_qa_warnings = 0

        for f in files_to_check:
            res = self.validate_pair(f)
            results.append(res)
            if res["status"] == "PASS":
                passed += 1
            else:
                failed += 1
            total_orig_entries += res["total_entries"]
            total_trans_entries += res["translated_entries"]
            total_identical += res["identical_entries"]
            total_qa_warnings += len(res["qa_warnings"])

        summary = {
            "total_files": len(files_to_check),
            "passed": passed,
            "failed": failed,
            "missing_in_target": len(missing_in_target),
            "unexpected_in_target": len(unexpected_in_target),
            "total_entries": total_orig_entries,
            "translated_entries": total_trans_entries,
            "identical_entries": total_identical,
            "total_qa_warnings": total_qa_warnings,
        }

        return {"summary": summary, "results": results}

def main():
    parser = argparse.ArgumentParser(description="GTA V Localization Validator & QA Suite")
    parser.add_argument("--original-dir", default="locales/original", help="Path to original .oxt directory")
    parser.add_argument("--translated-dir", default="locales/id", help="Path to translated .oxt directory")
    parser.add_argument("--files", nargs="*", help="Specific files to validate")
    parser.add_argument("--report", default="reports/validation_report.json", help="Path to output JSON report")
    parser.add_argument("--qa", action="store_true", help="Print detailed QA warnings")
    args = parser.parse_args()

    validator = LocalizationValidator(args.original_dir, args.translated_dir)
    audit = validator.validate_all(args.files)

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as rf:
        json.dump(audit, rf, indent=2)

    summary = audit["summary"]
    print("=" * 60)
    print("GTA V LOCALIZATION VALIDATION & QA AUDIT")
    print("=" * 60)
    print(f"Files Evaluated:       {summary['total_files']}")
    print(f"Passed:                {summary['passed']}")
    print(f"Failed:                {summary['failed']}")
    print(f"Missing in target:     {summary['missing_in_target']}")
    print(f"Unexpected in target:  {summary['unexpected_in_target']}")
    print(f"Total Entries:         {summary['total_entries']}")
    print(f"Translated Entries:    {summary['translated_entries']}")
    print(f"Identical / Untrans:   {summary['identical_entries']}")
    print(f"QA Warnings:           {summary['total_qa_warnings']}")
    print(f"Audit Report:          {args.report}")
    print("=" * 60)

    if summary["failed"] > 0:
        print("\nFAILURES DETECTED:")
        for res in audit["results"]:
            if res["status"] == "FAIL":
                print(f"\n[FAIL] {res['filename']}:")
                for err in res["errors"][:10]:
                    print(f"  - {err}")
                if len(res["errors"]) > 10:
                    print(f"  ... and {len(res['errors']) - 10} more errors")
        sys.exit(1)
    else:
        print("\nAll validation checks PASSED. Absolute LHS key integrity verified.")
        if args.qa and summary["total_qa_warnings"] > 0:
            print("\nQA Warnings Summary:")
            for res in audit["results"]:
                for qw in res["qa_warnings"][:5]:
                    print(f"  [{res['filename']}] {qw}")
        sys.exit(0)

if __name__ == "__main__":
    main()
