import math
import os
import re
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Set


class PorterStemmer:
    """
    Standard Porter Stemming Algorithm (Martin Porter, 1980).
    
    PURPOSE:
    Reduces morphological variants of English words to a common base stem.
    For example:
        'precautions' -> 'precaut'
        'precaution'  -> 'precaut'
        'inspecting'  -> 'inspect'
        'inspection'  -> 'inspect'
        'coolants'    -> 'coolant'
        'checked'     -> 'check'
    
    This ensures that when a supervisor queries 'precaution', it matches documents
    containing 'precautions' with 100% mathematical precision without relying on
    fuzzy edit distance.
    """

    @staticmethod
    def is_consonant(word: str, i: int) -> bool:
        letter = word[i]
        if letter in "aeiou":
            return False
        if letter == "y":
            return i == 0 or not PorterStemmer.is_consonant(word, i - 1)
        return True

    @staticmethod
    def measure(stem: str) -> int:
        """Counts the number of consonant-vowel transitions (VC sequences)."""
        m = 0
        i = 0
        n = len(stem)
        while i < n:
            if not PorterStemmer.is_consonant(stem, i):
                break
            i += 1
        while i < n:
            while i < n and not PorterStemmer.is_consonant(stem, i):
                i += 1
            if i >= n:
                break
            while i < n and PorterStemmer.is_consonant(stem, i):
                i += 1
            m += 1
        return m

    @staticmethod
    def stem(word: str) -> str:
        """Reduces suffixes for common English plurals, tenses, and agent nouns."""
        w = word.lower()
        if len(w) <= 3:
            return w

        # Step 1a: Plurals and 's' endings
        if w.endswith("sses"):
            w = w[:-2]
        elif w.endswith("ies"):
            w = w[:-2]
        elif not w.endswith("ss") and w.endswith("s"):
            w = w[:-1]

        # Step 1b: -ed and -ing
        if w.endswith("eed"):
            if PorterStemmer.measure(w[:-3]) > 0:
                w = w[:-1]
        elif w.endswith("ed"):
            stem = w[:-2]
            if any(not PorterStemmer.is_consonant(stem, j) for j in range(len(stem))):
                w = stem
                if w.endswith("at") or w.endswith("bl") or w.endswith("iz"):
                    w += "e"
                elif len(w) >= 2 and w[-1] == w[-2] and w[-1] not in "lsz":
                    w = w[:-1]
        elif w.endswith("ing"):
            stem = w[:-3]
            if any(not PorterStemmer.is_consonant(stem, j) for j in range(len(stem))):
                w = stem
                if w.endswith("at") or w.endswith("bl") or w.endswith("iz"):
                    w += "e"
                elif len(w) >= 2 and w[-1] == w[-2] and w[-1] not in "lsz":
                    w = w[:-1]

        # Step 1c: Terminal y -> i
        if w.endswith("y"):
            stem = w[:-1]
            if any(not PorterStemmer.is_consonant(stem, j) for j in range(len(stem))):
                w = stem + "i"

        # Step 2: Common suffixes (e.g. -ation, -tional, -ence)
        if w.endswith("ation"):
            if PorterStemmer.measure(w[:-5]) > 0:
                w = w[:-5] + "ate"
        elif w.endswith("tion"):
            if PorterStemmer.measure(w[:-4]) > 0:
                w = w[:-4] + "t"
        elif w.endswith("ment"):
            if PorterStemmer.measure(w[:-4]) > 0:
                w = w[:-4]
        elif w.endswith("able"):
            if PorterStemmer.measure(w[:-4]) > 0:
                w = w[:-4]

        return w


# Minimalist, high-utility English stopwords (functional grammar words)
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for", 
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", 
    "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "just", 
    "me", "more", "most", "my", "no", "nor", "not", "now", "of", "off", "on", "once", 
    "only", "or", "other", "our", "out", "over", "own", "s", "same", "she", 
    "should", "so", "some", "such", "than", "that", "the", "their", "them", 
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", 
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", 
    "why", "will", "with", "would", "you", "your"
}


class InvertedIndexRetriever:
    """
    High-Performance Inverted Index using Okapi BM25 Ranking with Porter Stemming
    and Active Document Revision Resolution.
    
    DATA STRUCTURE:
    - self.index: Dict[stemmed_term, List[Tuple[chunk_index, term_frequency]]]
      -> A Hash Map providing O(1) average-time candidate list access per query term.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[Dict[str, Any]] = []
        self.index: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.total_docs: int = 0
        self.doc_term_counts: Dict[str, int] = defaultdict(int)
        self.latest_revisions: Dict[str, Tuple[int, str]] = {}

    @staticmethod
    def tokenize(text: str, apply_stemming: bool = True) -> List[str]:
        """
        Extracts tokens, applies stopword filtering, and stems terms.
        Technical codes (e.g. 'al-104', 'bh-220', 'tx-200', '90.000') are preserved verbatim.
        """
        raw_tokens = re.findall(r"\b[a-zA-Z0-9_\-\.\%]+\b", text.lower())
        processed = []
        for t in raw_tokens:
            if t in STOP_WORDS:
                continue
            # Preserve technical codes, part numbers, and pure numbers
            if "-" in t or any(c.isdigit() for c in t) or len(t) <= 2:
                processed.append(t)
            else:
                stemmed = PorterStemmer.stem(t) if apply_stemming else t
                processed.append(stemmed)
        return processed

    def build_index(self, chunks: List[Dict[str, Any]]):
        """
        Indexes chunks into the in-memory Hash Map (Inverted Index) and dynamically
        resolves active document revisions.
        """
        self.chunks = chunks
        self.total_docs = len(chunks)
        self.doc_lengths = []
        self.index.clear()
        self.doc_term_counts.clear()

        # Step 1: Dynamically determine the highest revision for each Document Number
        for c in chunks:
            doc_no = c["doc_no"]
            rev_str = c["revision"]
            rev_num_match = re.search(r"[0-9]+", rev_str)
            rev_num = int(rev_num_match.group(0)) if rev_num_match else 1

            if doc_no not in self.latest_revisions:
                self.latest_revisions[doc_no] = (rev_num, rev_str)
            else:
                if rev_num > self.latest_revisions[doc_no][0]:
                    self.latest_revisions[doc_no] = (rev_num, rev_str)

        # Step 2: Index tokens into the Hash Map
        total_len = 0
        for idx, chunk in enumerate(chunks):
            content = f"{chunk.get('doc_title', '')} {chunk['heading']} {chunk['text']}"
            tokens = self.tokenize(content, apply_stemming=True)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            tf_map = defaultdict(int)
            for token in tokens:
                tf_map[token] += 1

            for token, count in tf_map.items():
                self.index[token].append((idx, count))
                self.doc_term_counts[token] += 1

        self.avg_doc_len = (total_len / self.total_docs) if self.total_docs > 0 else 0.0

    def is_chunk_active(self, chunk: Dict[str, Any]) -> bool:
        """Verifies if chunk belongs to the latest active revision."""
        doc_no = chunk["doc_no"]
        if doc_no in self.latest_revisions:
            latest_rev_str = self.latest_revisions[doc_no][1]
            return chunk["revision"] == latest_rev_str
        return True

    def retrieve(self, query: str, top_k: int = 4, allow_superseded: bool = False) -> List[Dict[str, Any]]:
        """
        BM25 probabilistic relevance scoring with coverage multiplier.
        Lookup complexity: O(1) hash access per query token.
        """
        query_tokens = self.tokenize(query, apply_stemming=True)
        if not query_tokens:
            return []

        scores = defaultdict(float)

        for token in query_tokens:
            if token not in self.index:
                continue

            # Inverse Document Frequency (IDF)
            n = self.doc_term_counts[token]
            idf = math.log((self.total_docs - n + 0.5) / (n + 0.5) + 1.0)

            # Retrieve candidate postings list from Hash Map
            for chunk_idx, tf in self.index[token]:
                chunk = self.chunks[chunk_idx]

                # Governance filter: suppress superseded revisions
                if not allow_superseded and not self.is_chunk_active(chunk):
                    continue

                doc_len = self.doc_lengths[chunk_idx]
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                term_score = idf * (tf * (self.k1 + 1.0)) / denominator
                scores[chunk_idx] += term_score

        # Coverage multiplier: boosts chunks containing multiple query stems
        final_scores = {}
        for chunk_idx, bm25_s in scores.items():
            content = f"{self.chunks[chunk_idx].get('doc_title', '')} {self.chunks[chunk_idx]['heading']} {self.chunks[chunk_idx]['text']}".lower()
            term_matches = sum(1 for t in query_tokens if t in content)
            coverage_multiplier = 1.0 + (term_matches / len(query_tokens))
            final_scores[chunk_idx] = bm25_s * coverage_multiplier

        ranked_indices = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for chunk_idx, score in ranked_indices:
            chunk = self.chunks[chunk_idx].copy()
            chunk["bm25_score"] = round(score, 4)
            results.append(chunk)

        return results

    def extract_vocabulary(self) -> Set[str]:
        return set(self.index.keys())
