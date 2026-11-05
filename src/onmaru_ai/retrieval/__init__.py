"""Retrieval adapters that operate only on verified candidate data."""

from .lexical import LexicalRequest, LexicalSearchAdapter, PostgresLexicalChunkRepository

__all__ = ("LexicalRequest", "LexicalSearchAdapter", "PostgresLexicalChunkRepository")
