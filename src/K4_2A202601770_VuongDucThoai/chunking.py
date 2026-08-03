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
        if not text or not text.strip():
            return []

        sentences = re.split(r"(?<=[.!?])\s+", text.strip())

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        chunks: list[str] = []

        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            sentence_group = sentences[
                start : start + self.max_sentences_per_chunk
            ]
            chunks.append(" ".join(sentence_group))

        return chunks


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
        if not text or not text.strip():
            return []

        chunks = self._split(text.strip(), self.separators)

        return [
            chunk.strip()
            for chunk in chunks
            if chunk and chunk.strip()
        ]

    def _split(
        self,
        current_text: str,
        remaining_separators: list[str],
        ) -> list[str]:
        # Base case 1: văn bản đã đủ ngắn
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case 2: không còn separator
        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Separator rỗng là mức cuối cùng: cắt theo kích thước cố định
        if separator == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        # Nếu separator không xuất hiện, thử separator tiếp theo
        if separator not in current_text:
            return self._split(current_text, next_separators)

        parts = current_text.split(separator)

        chunks: list[str] = []
        current_chunk = ""

        for part in parts:
            part = part.strip()

            if not part:
                continue

            if current_chunk:
                candidate = current_chunk + separator + part
            else:
                candidate = part

            # Nếu còn vừa kích thước thì tiếp tục gom
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
                continue

            # Candidate quá dài: lưu chunk đang có
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # Nếu riêng part vẫn quá dài, tiếp tục chia bằng separator sau
            if len(part) > self.chunk_size:
                chunks.extend(
                    self._split(part, next_separators)
                )
            else:
                current_chunk = part

        # Đưa chunk cuối cùng vào kết quả
        if current_chunk:
            chunks.append(current_chunk)

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(
                chunk_size=chunk_size,
                overlap=min(50, max(0, chunk_size // 10)),
            ),
            "by_sentences": SentenceChunker(
                max_sentences_per_chunk=3,
            ),
            "recursive": RecursiveChunker(
                chunk_size=chunk_size,
            ),
        }

        comparison: dict = {}

        for strategy_name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)

            if count > 0:
                avg_length = (
                    sum(len(chunk) for chunk in chunks) / count
                )
            else:
                avg_length = 0.0

            comparison[strategy_name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return comparison
