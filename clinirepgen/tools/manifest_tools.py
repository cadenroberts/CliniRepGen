"""
Manifest Tools - Unified interface for manifest search and access.

This class provides all the tools that agents use to interact with
the Trial Manifest during fact extraction.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from clinirepgen.manifest.models import Section, Table, TrialManifest

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A search result with relevance score."""
    id: str
    title: str
    score: float
    snippet: str
    source_type: str  # "section" or "table"
    metadata: Dict[str, Any]


class ManifestTools:
    """
    Provides search and access tools over a Trial Manifest.

    This is the main interface that agents use to find and retrieve
    information from trial documents.
    """

    def __init__(self, manifest: TrialManifest):
        """
        Initialize tools with a Trial Manifest.

        Args:
            manifest: The Trial Manifest to search/access
        """
        self.manifest = manifest

        # Build text index for search
        self._section_index: Dict[str, str] = {}  # section_id -> searchable text
        self._table_index: Dict[str, str] = {}    # table_id -> searchable text
        self._build_indices()

    def _build_indices(self) -> None:
        """Build search indices for sections and tables."""

        # Index sections
        for section_id, section in self.manifest.sections.items():
            searchable = f"{section.title} {section.content}".lower()
            self._section_index[section_id] = searchable

        # Index tables
        for table_id, table in self.manifest.tables.items():
            parts = [table.caption or ""]
            parts.extend(table.headers)
            if table.raw_data:
                for row in table.raw_data:
                    parts.extend([str(cell) for cell in row])
            self._table_index[table_id] = " ".join(parts).lower()

    def search_sections(
        self,
        query: str,
        doc_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> List[SearchResult]:
        """
        Search sections by query with optional filters.

        Args:
            query: Search query string
            doc_types: Optional list of document types to filter by
            tags: Optional list of tags to filter by
            max_results: Maximum number of results

        Returns:
            List of SearchResult objects sorted by relevance
        """
        query_lower = query.lower()
        query_terms = query_lower.split()

        results = []

        for section_id, searchable_text in self._section_index.items():
            section = self.manifest.sections[section_id]
            doc = self.manifest.documents.get(section.doc_id)

            # Apply filters
            if doc_types and doc and doc.doc_type not in doc_types:
                continue

            if tags and not any(tag in section.tags for tag in tags):
                continue

            # Calculate relevance score (simple term frequency)
            score = 0.0
            for term in query_terms:
                if term in searchable_text:
                    # Count occurrences
                    score += searchable_text.count(term)
                    # Bonus for title match
                    if term in section.title.lower():
                        score += 5.0

            if score > 0:
                # Generate snippet
                snippet = self._extract_snippet(section.content, query_terms, max_len=200)

                results.append(SearchResult(
                    id=section_id,
                    title=section.title,
                    score=score,
                    snippet=snippet,
                    source_type="section",
                    metadata={
                        "doc_id": section.doc_id,
                        "doc_name": doc.file_name if doc else "unknown",
                        "tags": section.tags,
                        "level": section.level,
                    }
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)

        return results[:max_results]

    def search_tables(
        self,
        query: str,
        doc_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> List[SearchResult]:
        """
        Search tables by query.

        Args:
            query: Search query string
            doc_types: Optional list of document types to filter by
            tags: Optional list of tags to filter by
            max_results: Maximum number of results

        Returns:
            List of SearchResult objects sorted by relevance
        """
        query_lower = query.lower()
        query_terms = query_lower.split()

        results = []

        for table_id, searchable_text in self._table_index.items():
            table = self.manifest.tables[table_id]
            doc = self.manifest.documents.get(table.doc_id)

            # Apply filters
            if doc_types and doc and doc.doc_type not in doc_types:
                continue

            if tags and not any(tag in table.tags for tag in tags):
                continue

            # Calculate relevance score
            score = 0.0
            for term in query_terms:
                if term in searchable_text:
                    score += searchable_text.count(term)
                    # Bonus for caption match
                    if table.caption and term in table.caption.lower():
                        score += 5.0
                    # Bonus for header match
                    if any(term in h.lower() for h in table.headers):
                        score += 3.0

            if score > 0:
                # Generate snippet from headers and first row
                snippet_parts = [table.caption or "Table"]
                snippet_parts.extend(table.headers[:5])
                snippet = " | ".join(snippet_parts)

                results.append(SearchResult(
                    id=table_id,
                    title=table.caption or f"Table ({table.num_rows}x{table.num_cols})",
                    score=score,
                    snippet=snippet[:200],
                    source_type="table",
                    metadata={
                        "doc_id": table.doc_id,
                        "doc_name": doc.file_name if doc else "unknown",
                        "tags": table.tags,
                        "num_rows": table.num_rows,
                        "num_cols": table.num_cols,
                        "headers": table.headers,
                    }
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)

        return results[:max_results]

    def open_section(self, section_id: str) -> Optional[Dict[str, Any]]:
        """
        Open and return full content of a section.

        Args:
            section_id: ID of the section to open

        Returns:
            Dict with section details and content, or None if not found
        """
        section = self.manifest.get_section(section_id)
        if not section:
            logger.warning(f"Section not found: {section_id}")
            return None

        doc = self.manifest.get_document(section.doc_id)

        return {
            "section_id": section.section_id,
            "title": section.title,
            "level": section.level,
            "section_number": section.section_number,
            "content": section.content,
            "word_count": section.word_count,
            "tags": section.tags,
            "page_start": section.page_start,
            "page_end": section.page_end,
            "doc_id": section.doc_id,
            "doc_name": doc.file_name if doc else "unknown",
            "doc_type": doc.doc_type if doc else "unknown",
            "has_tables": section.has_tables,
            "table_ids": section.table_ids,
        }

    def get_table(self, table_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full table data including all cells.

        Args:
            table_id: ID of the table to retrieve

        Returns:
            Dict with table details and data, or None if not found
        """
        table = self.manifest.get_table(table_id)
        if not table:
            logger.warning(f"Table not found: {table_id}")
            return None

        doc = self.manifest.get_document(table.doc_id)

        return {
            "table_id": table.table_id,
            "caption": table.caption,
            "table_number": table.table_number,
            "num_rows": table.num_rows,
            "num_cols": table.num_cols,
            "headers": table.headers,
            "raw_data": table.raw_data,
            "markdown": table.markdown or self._table_to_markdown(table),
            "tags": table.tags,
            "page_num": table.page_num,
            "doc_id": table.doc_id,
            "doc_name": doc.file_name if doc else "unknown",
            "section_id": table.section_id,
        }

    def get_table_cell(self, table_id: str, row: int, col: int) -> Optional[str]:
        """
        Get the value of a specific table cell.

        Args:
            table_id: ID of the table
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            Cell value as string, or None if not found
        """
        table = self.manifest.get_table(table_id)
        if not table:
            logger.warning(f"Table not found: {table_id}")
            return None

        return table.get_cell(row, col)

    def get_table_row(self, table_id: str, row: int) -> Optional[List[str]]:
        """
        Get all values in a table row.

        Args:
            table_id: ID of the table
            row: Row index (0-based)

        Returns:
            List of cell values, or None if table not found
        """
        table = self.manifest.get_table(table_id)
        if not table:
            return None

        return table.get_row(row)

    def get_table_column(self, table_id: str, col: int) -> Optional[List[str]]:
        """
        Get all values in a table column.

        Args:
            table_id: ID of the table
            col: Column index (0-based)

        Returns:
            List of cell values, or None if table not found
        """
        table = self.manifest.get_table(table_id)
        if not table:
            return None

        return table.get_column(col)

    def get_sections_by_tag(self, tag: str) -> List[Section]:
        """Get all sections with a specific tag."""
        return [
            section for section in self.manifest.sections.values()
            if tag in section.tags
        ]

    def get_tables_by_tag(self, tag: str) -> List[Table]:
        """Get all tables with a specific tag."""
        return [
            table for table in self.manifest.tables.values()
            if tag in table.tags
        ]

    def _extract_snippet(self, text: str, query_terms: List[str],
                         max_len: int = 200) -> str:
        """Extract a relevant snippet from text around query terms."""
        text_lower = text.lower()

        # Find first occurrence of any query term
        best_pos = len(text)
        for term in query_terms:
            pos = text_lower.find(term)
            if pos >= 0 and pos < best_pos:
                best_pos = pos

        if best_pos >= len(text):
            best_pos = 0

        # Extract snippet around that position
        start = max(0, best_pos - 50)
        end = min(len(text), start + max_len)

        snippet = text[start:end]

        # Clean up
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet.replace("\n", " ").strip()

    def _table_to_markdown(self, table: Table) -> str:
        """Convert a table to markdown format."""
        if not table.raw_data:
            return ""

        lines = []

        # Header row
        if table.headers:
            lines.append("| " + " | ".join(table.headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(table.headers)) + " |")

        # Data rows
        start_row = 1 if table.headers else 0
        for row in table.raw_data[start_row:]:
            lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

        return "\n".join(lines)

    # Tool descriptions for agents
    @staticmethod
    def get_tool_descriptions() -> List[Dict[str, Any]]:
        """Get tool descriptions in agent-friendly format."""
        return [
            {
                "name": "search_sections",
                "description": "Search document sections by query. Returns relevant sections with snippets.",
                "parameters": {
                    "query": "Search query string",
                    "doc_types": "Optional list of document types to filter (protocol, csr, etc.)",
                    "tags": "Optional list of tags to filter (methods, safety, etc.)",
                    "max_results": "Maximum number of results (default 10)",
                },
            },
            {
                "name": "search_tables",
                "description": "Search tables by query. Searches captions, headers, and cell content.",
                "parameters": {
                    "query": "Search query string",
                    "doc_types": "Optional list of document types to filter",
                    "tags": "Optional list of tags to filter",
                    "max_results": "Maximum number of results (default 10)",
                },
            },
            {
                "name": "open_section",
                "description": "Open a section and get its full content.",
                "parameters": {
                    "section_id": "ID of the section to open",
                },
            },
            {
                "name": "get_table",
                "description": "Get full table data including headers and all cells.",
                "parameters": {
                    "table_id": "ID of the table to retrieve",
                },
            },
            {
                "name": "get_table_cell",
                "description": "Get the value of a specific table cell.",
                "parameters": {
                    "table_id": "ID of the table",
                    "row": "Row index (0-based)",
                    "col": "Column index (0-based)",
                },
            },
        ]
