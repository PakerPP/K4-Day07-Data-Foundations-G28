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

    # Sentence-ending punctuation followed by whitespace marks a boundary;
    # captured so the punctuation stays attached to the sentence before it.
    _SENTENCE_SPLIT = re.compile(r"([.!?])(?:\s+|$)")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def _split_into_sentences(self, text: str) -> list[str]:
        tokens = self._SENTENCE_SPLIT.split(text.strip())
        sentences: list[str] = []
        buffer = ""
        for token in tokens:
            if token in (".", "!", "?"):
                buffer += token
                sentences.append(buffer.strip())
                buffer = ""
            else:
                buffer += token
        if buffer.strip():
            sentences.append(buffer.strip())
        return [s for s in sentences if s]

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        n = self.max_sentences_per_chunk
        return [" ".join(sentences[i : i + n]) for i in range(0, len(sentences), n)]


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
        raw_pieces = self._split(text.strip(), self.separators)
        return self._coalesce(raw_pieces)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text.strip() else []

        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator, remaining = remaining_separators[0], remaining_separators[1:]
        if separator == "":
            return self._split(current_text, [])

        parts = current_text.split(separator)
        if len(parts) == 1:
            return self._split(current_text, remaining)

        pieces: list[str] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            pieces.extend(self._split(part, remaining))
        return pieces

    def _coalesce(self, pieces: list[str]) -> list[str]:
        """Merge adjacent undersized pieces into chunks close to chunk_size."""
        merged: list[str] = []
        acc = ""
        for piece in pieces:
            candidate = f"{acc} {piece}".strip() if acc else piece
            if len(candidate) <= self.chunk_size:
                acc = candidate
            else:
                if acc:
                    merged.append(acc)
                acc = piece
        if acc:
            merged.append(acc)
        return merged


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=chunk_size // 10),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            lengths = [len(c) for c in chunks]
            comparison[name] = {
                "count": len(chunks),
                "avg_length": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
                "chunks": chunks,
            }
        return comparison
