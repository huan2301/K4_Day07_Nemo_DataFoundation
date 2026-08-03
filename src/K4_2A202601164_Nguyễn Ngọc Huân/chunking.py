from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Find sentences (keep punctuation). Matches up to a sentence-ending punctuation or the last fragment.
        sentences = re.findall(r'.*?[.!?](?:\s|$)|.+$', text, flags=re.S)
        # Clean sentences
        sentences = [s.strip() for s in sentences if s and s.strip()]
        chunks: list[str] = []
        cur: list[str] = []
        for s in sentences:
            cur.append(s)
            if len(cur) >= self.max_sentences_per_chunk:
                chunks.append(" ".join(cur).strip())
                cur = []
        if cur:
            chunks.append(" ".join(cur).strip())
        # filter out any empty strings
        return [c for c in chunks if c]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Use provided separators or defaults
        separators = list(self.separators)
        # If separators is empty, fallback to fixed-size split
        if not separators:
            # fixed-size slicing
            chunks: list[str] = []
            for i in range(0, len(text), self.chunk_size):
                chunks.append(text[i : i + self.chunk_size].strip())
            return [c for c in chunks if c]
        return [c for c in self._split(text, separators) if c and c.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        text = current_text
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text.strip()]

        if not remaining_separators:
            # No separators left: fixed-size split
            chunks: list[str] = []
            for i in range(0, len(text), self.chunk_size):
                chunks.append(text[i : i + self.chunk_size].strip())
            return chunks

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        # If separator is empty string, fallback to fixed-size split
        if sep == "":
            chunks: list[str] = []
            for i in range(0, len(text), self.chunk_size):
                chunks.append(text[i : i + self.chunk_size].strip())
            return chunks

        # If separator not present at all, try next separator
        if sep not in text:
            return self._split(text, next_seps)

        parts = text.split(sep)
        merged_chunks: list[str] = []
        buffer = ""
        for i, part in enumerate(parts):
            if buffer == "":
                candidate = part
            else:
                candidate = buffer + sep + part
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                # flush buffer
                if buffer:
                    merged_chunks.append(buffer.strip())
                # if the single part is too big, recursively split it with next separators
                if len(part) > self.chunk_size:
                    merged_chunks.extend(self._split(part, next_seps))
                    buffer = ""
                else:
                    buffer = part
        if buffer:
            merged_chunks.append(buffer.strip())

        # For any chunk still too large, recursively split using next separators
        final_chunks: list[str] = []
        for chunk in merged_chunks:
            if len(chunk) > self.chunk_size:
                final_chunks.extend(self._split(chunk, next_seps))
            else:
                final_chunks.append(chunk.strip())
        return final_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0
    dot_prod = _dot(vec_a, vec_b)
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_prod / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text)
        # heuristically choose sentences per chunk based on chunk_size
        max_sent = max(1, chunk_size // 50)
        by_sentences = SentenceChunker(max_sentences_per_chunk=max_sent).chunk(text)
        recursive = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0
            return {"count": count, "avg_length": avg_length, "chunks": chunks}

        return {"fixed_size": stats(fixed), "by_sentences": stats(by_sentences), "recursive": stats(recursive)}
