#!/usr/bin/env python3
"""
GTA V Localization Validation Suite.
Compares original .oxt files in locales/original/ with translated files in locales/id/.
Guarantees absolute LHS key identity, structural integrity, and token preservation.
"""

import os
import sys
import glob
import json
import argparse
from typing import List, Dict, Tuple, Any

from tools.token_shield import TokenShield

shield = TokenShield()

class LocalizationValidator:
    def __init__(self, original_dir: str, translated_dir: str):
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

        # 1. Byte-level checks: Encoding (BOM) & Line Endings
        with open(filepath, "rb") as bf:
            raw = bf.read()

        if not raw.startswith(b"\xef\xbb\xbf"):
            errors.append("Encoding Error: Missing UTF-8 BOM (0xEF 0xBB 0xBF)")

        if b"\r\n" not in raw and len(raw) > 30:
            errors.append("Line Ending Error: File does not use CRLF line endings")

        # 2. Text parsing
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
                # Outside block and not Version header
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

        # Compare headers
        if orig_headers != trans_headers:
            result["status"] = "FAIL"
            result["errors"].append(f"Header mismatch: Expected {orig_headers}, got {trans_headers}")

        # Compare entry counts
        result["total_entries"] = len(orig_entries)
        if len(orig_entries) != len(trans_entries):
            result["status"] = "FAIL"
            result["errors"].append(
                f"Entry count mismatch: Original has {len(orig_entries)} entries, translated has {len(trans_entries)} entries"
            )
            return result

        # Strict Left-Hand-Side & Key Order Validation
        for idx, ((orig_prefix, orig_key, orig_val), (trans_prefix, trans_key, trans_val)) in enumerate(
            zip(orig_entries, trans_entries)
        ):
            # 1. Check EXACT key equality
            if orig_key != trans_key:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Entry {idx + 1}: Key modified! Original '{orig_key}' != Translated '{trans_key}'"
                )
                continue

            # 2. Check EXACT prefix (indentation and spacing before '=')
            if orig_prefix != trans_prefix:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Entry {idx + 1} ({orig_key}): LHS indentation or spacing mismatch! "
                    f"Original {repr(orig_prefix)} != Translated {repr(trans_prefix)}"
                )

            # 3. Check Token and Placeholder preservation
            is_valid, token_errs = shield.verify_tokens(orig_val, trans_val)
            if not is_valid:
                result["status"] = "FAIL"
                for terr in token_errs:
                    result["errors"].append(f"Entry {idx + 1} ({orig_key}): {terr}")

            # 4. Check Translation Status Metrics
            if orig_val.strip() == trans_val.strip():
                result["identical_entries"] += 1
            else:
                result["translated_entries"] += 1

        if result["errors"]:
            result["status"] = "FAIL"

        return result

    def validate_all(self, target_files: List[str] = None) -> Dict[str, Any]:
        if not target_files:
            # Check all translated files currently present in translated_dir
            trans_files = [os.path.basename(f) for f in glob.glob(os.path.join(self.translated_dir, "*.oxt"))]
            if not trans_files:
                print(f"No translated .oxt files found in {self.translated_dir} to validate.")
                return {"summary": {"total_files": 0, "passed": 0, "failed": 0}, "results": []}
            files_to_check = sorted(trans_files)
        else:
            files_to_check = target_files

        results = []
        passed = 0
        failed = 0
        total_orig_entries = 0
        total_trans_entries = 0
        total_identical = 0

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

        summary = {
            "total_files": len(files_to_check),
            "passed": passed,
            "failed": failed,
            "total_entries": total_orig_entries,
            "translated_entries": total_trans_entries,
            "identical_entries": total_identical,
        }

        return {"summary": summary, "results": results}

def main():
    parser = argparse.ArgumentParser(description="GTA V Localization Validator")
    parser.add_argument("--original-dir", default="locales/original", help="Path to original .oxt directory")
    parser.add_argument("--translated-dir", default="locales/id", help="Path to translated .oxt directory")
    parser.add_argument("--files", nargs="*", help="Specific files to validate (e.g. prolog.oxt abgail2.oxt)")
    parser.add_argument("--report", default="reports/validation_report.json", help="Path to output JSON report")
    parser.add_argument("--quiet", action="store_true", help="Minimal console output")
    args = parser.parse_args()

    validator = LocalizationValidator(args.original_dir, args.translated_dir)
    audit = validator.validate_all(args.files)

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as rf:
        json.dump(audit, rf, indent=2)

    summary = audit["summary"]
    print("=" * 60)
    print("GTA V LOCALIZATION VALIDATION AUDIT")
    print("=" * 60)
    print(f"Files Evaluated:    {summary['total_files']}")
    print(f"Passed:             {summary['passed']}")
    print(f"Failed:             {summary['failed']}")
    print(f"Total Entries:      {summary['total_entries']}")
    print(f"Translated:         {summary['translated_entries']}")
    print(f"Identical / Untrans:{summary['identical_entries']}")
    print(f"Report Generated:   {args.report}")
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
        sys.exit(0)

if __name__ == "__main__":
    main()
