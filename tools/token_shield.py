"""
Token Shield Module for GTA V Localization.
Safely extracts, masks, and restores Rockstar tokens, placeholders, tags, and escape sequences.
"""

import re
from typing import Tuple, List, Dict

# Rockstar tokens: ~token~ (e.g. ~s~, ~INPUT_CONTEXT~, ~HUD_COLOUR_RED~)
ROCKSTAR_TOKEN_REGEX = re.compile(r"~[^~]+~")

# Standard format specifiers: %s, %d, %1, %2$s, {0}, {player}, etc.
PLACEHOLDER_REGEX = re.compile(
    r"(?:%[0-9]*[a-zA-Z]|%[0-9]+\$[a-zA-Z]|%[0-9]+|\{[0-9a-zA-Z_]+\}|<[a-zA-Z0-9_]+>|\[[a-zA-Z0-9_]+\])"
)

# HTML/XML markup tags: e.g. <img src='...' ... />
MARKUP_TAG_REGEX = re.compile(r"<img[^>]*/>|<[^>]+>")

# Escape sequences: \n, \r, \t, etc.
ESCAPE_REGEX = re.compile(r"\\[nrt\"\']")

class TokenShield:
    def __init__(self):
        # Combined pattern prioritizing full markup tags first, then rockstar tokens, then placeholders
        self.combined_regex = re.compile(
            r"(<img[^>]*/>|<[^>]+>|~[^~]+~|%[0-9]*[a-zA-Z]|%[0-9]+\$[a-zA-Z]|%[0-9]+|\{[0-9a-zA-Z_]+\}|<[a-zA-Z0-9_]+>|\[[a-zA-Z0-9_]+\])"
        )

    def extract_tokens(self, text: str) -> List[str]:
        """Extract all tokens in order of appearance."""
        return self.combined_regex.findall(text)

    def mask(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace all tokens with safe alphanumeric placeholders: __TK_0__, __TK_1__, etc.
        Returns the masked text and the mapping to restore them.
        """
        tokens = self.extract_tokens(text)
        token_map: Dict[str, str] = {}
        masked_text = text

        for idx, token in enumerate(tokens):
            marker = f"__TK_{idx}__"
            token_map[marker] = token

        # Replace using sub with a counter to ensure exact 1-to-1 order preservation
        counter = [0]
        def _replace(match):
            idx = counter[0]
            counter[0] += 1
            return f"__TK_{idx}__"

        masked_text = self.combined_regex.sub(_replace, text)
        return masked_text, token_map

    def unmask(self, masked_text: str, token_map: Dict[str, str]) -> str:
        """Restore masked tokens back to their original form."""
        restored = masked_text
        for marker, original_token in token_map.items():
            restored = restored.replace(marker, original_token)
        return restored

    def verify_tokens(self, original_text: str, candidate_text: str) -> Tuple[bool, List[str]]:
        """
        Verify that all tokens in original_text are preserved identically in candidate_text.
        Returns (is_valid, list_of_discrepancies).
        """
        orig_tokens = self.extract_tokens(original_text)
        cand_tokens = self.extract_tokens(candidate_text)

        errors = []
        if len(orig_tokens) != len(cand_tokens):
            errors.append(
                f"Token count mismatch: expected {len(orig_tokens)} tokens {orig_tokens}, got {len(cand_tokens)} {cand_tokens}"
            )
        else:
            for idx, (expected, actual) in enumerate(zip(orig_tokens, cand_tokens)):
                if expected != actual:
                    errors.append(f"Token mismatch at index {idx}: expected '{expected}', found '{actual}'")

        return (len(errors) == 0, errors)

    def is_token_only(self, text: str) -> bool:
        """Check if the text contains ONLY tokens, whitespace, or punctuation."""
        stripped = self.combined_regex.sub("", text).strip()
        # If nothing remains or only single punctuation remains, it's token-only
        return len(stripped) == 0
