import re
from typing import List, Set, Tuple


class TextNormalizer:
    """
    Layer 1: Normalizer & Typo Fixer
    Cleans raw user input, removes extraneous whitespace/punctuation, and employs
    the Dynamic Programming Levenshtein Distance algorithm to correct common typos
    and phonetic variations against the dynamically built domain vocabulary.
    """

    def __init__(self, vocabulary: Set[str] = None):
        """
        Args:
            vocabulary: A set of domain terms extracted dynamically from the PDFs
                        (e.g., 'coolant', 'refractometer', 'hydraulic', 'caliper',
                        alarm codes, part numbers).
        """
        self.vocabulary = vocabulary or set()

    def update_vocabulary(self, words: Set[str]):
        """Dynamically add new terms discovered during document parsing."""
        self.vocabulary.update(words)

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Trims whitespace, normalizes multiple spaces, standardizes hyphens,
        and strips dangerous characters.
        """
        if not text:
            return ""
        # Standardize different dashes/hyphens
        normalized = re.sub(r"[—–−]", "-", text)
        # Normalize multiple whitespace characters to a single space
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """
        Calculates the minimum edit distance between two strings using
        Dynamic Programming.
        
        Time Complexity:  O(|s1| * |s2|)
        Space Complexity: O(|s1| * |s2|) (or O(min(|s1|, |s2|)) with row swapping)
        """
        m, n = len(s1), len(s2)
        # dp[i][j] stores the edit distance between s1[0..i-1] and s2[0..j-1]
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1].lower() == s2[j - 1].lower():
                    cost = 0
                else:
                    cost = 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,       # Deletion
                    dp[i][j - 1] + 1,       # Insertion
                    dp[i - 1][j - 1] + cost # Substitution
                )
        return dp[m][n]

    def find_closest_term(self, word: str, max_distance: int = 2) -> Tuple[str, int]:
        """
        Finds the closest known domain word in the vocabulary within max_distance edits.
        """
        clean_w = word.strip().lower()
        if len(clean_w) <= 3:
            # Avoid aggressive corrections for very short tokens
            return word, 0

        best_match = word
        min_dist = max_distance + 1

        for candidate in self.vocabulary:
            c_lower = candidate.lower()
            # Fast length filter: edit distance cannot be less than length difference
            if abs(len(c_lower) - len(clean_w)) > max_distance:
                continue

            dist = self.levenshtein_distance(clean_w, c_lower)
            if dist < min_dist:
                min_dist = dist
                best_match = candidate

        if min_dist <= max_distance:
            return best_match, min_dist
        return word, 0

    def normalize_query(self, query: str) -> str:
        """
        Full Layer 1 pipeline:
        1. Clean whitespace and characters.
        2. Fix common hyphen-omission in alarm codes (e.g. 'AL104' -> 'AL-104')
        3. Token-by-token typo correction using DP Levenshtein distance.
        """
        cleaned = self.clean_text(query)
        if not cleaned:
            return ""

        # Normalize pattern like AL104 or al104 to AL-104
        cleaned = re.sub(r"\b([Aa][Ll])\s*([0-9]{3})\b", r"\1-\2", cleaned)
        cleaned = re.sub(r"\b([Bb][Hh])\s*([0-9]{3})\b", r"\1-\2", cleaned)
        cleaned = re.sub(r"\b([Tt][Xx])\s*([0-9]{3})\b", r"\1-\2", cleaned)

        # Token-level typo correction
        tokens = cleaned.split(" ")
        corrected_tokens = []
        for token in tokens:
            # Strip punctuation for matching
            sub_w = re.sub(r"[^\w\-]", "", token)
            if sub_w and len(sub_w) > 4:
                closest, dist = self.find_closest_term(sub_w, max_distance=1)
                if dist > 0:
                    # Preserve original punctuation
                    token = token.replace(sub_w, closest)
            corrected_tokens.append(token)

        return " ".join(corrected_tokens)
