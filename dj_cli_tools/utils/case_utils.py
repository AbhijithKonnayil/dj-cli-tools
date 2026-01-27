"""String case conversion utilities organized in a CaseUtils class.

Exports both the CaseUtils class and top-level convenience functions for
backwards compatibility.
"""
from __future__ import annotations

import re
from typing import List


class CaseUtils:
    """Utilities for converting strings between naming conventions.

    All methods are provided as @staticmethods so callers may use them without
    instantiating the class. The splitting algorithm is tolerant to common
    input shapes: snake_case, kebab-case, space separated, camelCase,
    PascalCase and ALLCAPS. Numbers are preserved as separate parts.
    """

    _WORD_RE = re.compile(r"""
        [A-Z]+(?=[A-Z][a-z]) |   # ALLCAPS acronym followed by TitleCase word
        [A-Z]?[a-z]+         |   # TitleCase / camelCase words
        \d+                  |   # numbers
        [A-Z]+                  # remaining ALLCAPS words
    """, re.VERBOSE)

    @staticmethod
    def _split_into_words(s: str) -> List[str]:
        if not s:
            return []
        s = re.sub(r"[_\-\s]+", " ", s).strip()
        if " " in s:
            tokens: List[str] = []
            for token in s.split():
                tokens.extend(CaseUtils._WORD_RE.findall(token) or [token])
            return tokens
        found = CaseUtils._WORD_RE.findall(s)
        return found or re.findall(r"\w+", s)

    @staticmethod
    def to_pascal_case(s: str) -> str:
        parts = CaseUtils._split_into_words(s)
        return "".join(p.capitalize() for p in parts)

    @staticmethod
    def to_camel_case(s: str) -> str:
        pascal = CaseUtils.to_pascal_case(s)
        if not pascal:
            return pascal
        return pascal[0].lower() + pascal[1:]

    @staticmethod
    def to_snake_case(s: str) -> str:
        parts = CaseUtils._split_into_words(s)
        return "_".join(p.lower() for p in parts)

    @staticmethod
    def to_kebab_case(s: str) -> str:
        parts = CaseUtils._split_into_words(s)
        return "-".join(p.lower() for p in parts)

    @staticmethod
    def to_title_case(s: str) -> str:
        parts = CaseUtils._split_into_words(s)
        return " ".join(p.capitalize() for p in parts)

    @staticmethod
    def to_constant_case(s: str) -> str:
        parts = CaseUtils._split_into_words(s)
        return "_".join(p.upper() for p in parts)

    @staticmethod
    def to_sentence_case(s: str) -> str:
        parts = CaseUtils._split_into_words(s)
        if not parts:
            return s
        sentence = " ".join(p.lower() for p in parts)
        return sentence[0].upper() + sentence[1:]


__all__ = [
    "CaseUtils",

]
