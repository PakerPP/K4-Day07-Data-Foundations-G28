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

    _BOUNDARY = re.compile(r"[.!?]\s+|\.\n")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def _split_sentences(self, text: str) -> list[str]:
        sentences: list[str] = []
        cursor = 0
        for match in self._BOUNDARY.finditer(text):
            end = match.start() + 1  # keep the punctuation, drop the trailing whitespace
            piece = text[cursor:end].strip()
            if piece:
                sentences.append(piece)
            cursor = match.end()
        tail = text[cursor:].strip()
        if tail:
            sentences.append(tail)
        return sentences

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks: list[str] = []
        bucket: list[str] = []
        for sentence in sentences:
            bucket.append(sentence)
            if len(bucket) >= self.max_sentences_per_chunk:
                chunks.append(" ".join(bucket).strip())
                bucket = []
        if bucket:
            chunks.append(" ".join(bucket).strip())
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

        pieces = self._split(text.strip(), self.separators)
        return self._pack(pieces)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        """Break current_text into fragments no larger than chunk_size, trying
        each separator in turn; fragments may still be small (packing happens later)."""
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text else []

        if not remaining_separators:
            # Last resort: hard cut every chunk_size characters.
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator, rest = remaining_separators[0], remaining_separators[1:]
        if separator == "":
            return self._split(current_text, [])

        parts = [p for p in current_text.split(separator) if p.strip()]
        if len(parts) <= 1:
            return self._split(current_text, rest)

        fragments: list[str] = []
        for part in parts:
            fragments.extend(self._split(part.strip(), rest))
        return fragments

    def _pack(self, fragments: list[str]) -> list[str]:
        """Greedily accumulate consecutive small fragments into ~chunk_size chunks."""
        chunks: list[str] = []
        current = ""
        for fragment in fragments:
            joined = f"{current} {fragment}".strip() if current else fragment
            if len(joined) <= self.chunk_size:
                current = joined
            else:
                if current:
                    chunks.append(current)
                current = fragment
        if current:
            chunks.append(current)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        overlap = max(1, chunk_size // 10)
        chunkers = (
            ("fixed_size", FixedSizeChunker(chunk_size=chunk_size, overlap=overlap)),
            ("by_sentences", SentenceChunker(max_sentences_per_chunk=3)),
            ("recursive", RecursiveChunker(chunk_size=chunk_size)),
        )

        report: dict = {}
        for name, chunker in chunkers:
            pieces = chunker.chunk(text)
            lengths = [len(piece) for piece in pieces]
            avg_length = (sum(lengths) / len(lengths)) if lengths else 0.0
            report[name] = {
                "count": len(pieces),
                "avg_length": round(avg_length, 2),
                "chunks": pieces,
            }
        return report
