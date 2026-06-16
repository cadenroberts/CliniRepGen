"""
Search functions - Standalone search APIs for manifest content.

These are convenience functions that wrap ManifestTools methods.
"""

from typing import List, Optional

from clinirepgen.manifest.models import TrialManifest
from clinirepgen.tools.manifest_tools import ManifestTools, SearchResult


def search_sections(
    manifest: TrialManifest,
    query: str,
    doc_types: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    max_results: int = 10,
) -> List[SearchResult]:
    """
    Search sections in a manifest by query.

    Args:
        manifest: Trial Manifest to search
        query: Search query string
        doc_types: Optional list of document types to filter by
        tags: Optional list of tags to filter by
        max_results: Maximum number of results

    Returns:
        List of SearchResult objects sorted by relevance
    """
    tools = ManifestTools(manifest)
    return tools.search_sections(
        query=query,
        doc_types=doc_types,
        tags=tags,
        max_results=max_results,
    )


def search_tables(
    manifest: TrialManifest,
    query: str,
    doc_types: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    max_results: int = 10,
) -> List[SearchResult]:
    """
    Search tables in a manifest by query.

    Args:
        manifest: Trial Manifest to search
        query: Search query string
        doc_types: Optional list of document types to filter by
        tags: Optional list of tags to filter by
        max_results: Maximum number of results

    Returns:
        List of SearchResult objects sorted by relevance
    """
    tools = ManifestTools(manifest)
    return tools.search_tables(
        query=query,
        doc_types=doc_types,
        tags=tags,
        max_results=max_results,
    )


def search_all(
    manifest: TrialManifest,
    query: str,
    doc_types: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    max_results: int = 10,
) -> List[SearchResult]:
    """
    Search both sections and tables, returning combined results.

    Args:
        manifest: Trial Manifest to search
        query: Search query string
        doc_types: Optional list of document types to filter by
        tags: Optional list of tags to filter by
        max_results: Maximum total number of results

    Returns:
        Combined list of SearchResult objects sorted by relevance
    """
    tools = ManifestTools(manifest)

    section_results = tools.search_sections(
        query=query,
        doc_types=doc_types,
        tags=tags,
        max_results=max_results,
    )

    table_results = tools.search_tables(
        query=query,
        doc_types=doc_types,
        tags=tags,
        max_results=max_results,
    )

    # Combine and sort by score
    all_results = section_results + table_results
    all_results.sort(key=lambda r: r.score, reverse=True)

    return all_results[:max_results]
