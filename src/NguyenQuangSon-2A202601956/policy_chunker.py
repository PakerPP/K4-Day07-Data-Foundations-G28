"""Chunking strategy specialized for Markdown policy documents."""

from __future__ import annotations

import re

from .chunking import RecursiveChunker


class HeadingPolicyChunker:
    """Keep a Markdown heading with the policy clause it introduces.

    Policy questions usually name a rule rather than an isolated sentence.  By
    retaining the heading in every chunk derived from that section, retrieval
    keeps both the topic and its conditions together.
    """

    _heading_pattern = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)

    def __init__(self, chunk_size: int = 900) -> None:
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        matches = list(self._heading_pattern.finditer(text))
        if not matches:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(text.strip())

        chunks: list[str] = []
        prefix = text[: matches[0].start()].strip()
        if prefix:
            chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(prefix))

        for index, match in enumerate(matches):
            heading = match.group().strip()
            section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[match.end() : section_end].strip()
            section = f"{heading}\n\n{body}".strip()
            chunks.extend(self._chunk_section(heading, section, body))
        return chunks

    def _chunk_section(self, heading: str, section: str, body: str) -> list[str]:
        if len(section) <= self.chunk_size:
            return [section]

        available_body_size = self.chunk_size - len(heading) - 2
        if available_body_size <= 0:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(section)

        body_chunks = RecursiveChunker(chunk_size=available_body_size).chunk(body)
        return [f"{heading}\n\n{piece}".strip() for piece in body_chunks]
