"""
Access functions - Direct access APIs for manifest content.

These are convenience functions that wrap ManifestTools methods.
"""

from typing import Any, Dict, List, Optional

from clinirepgen.manifest.models import TrialManifest
from clinirepgen.tools.manifest_tools import ManifestTools


def open_section(manifest: TrialManifest, section_id: str) -> Optional[Dict[str, Any]]:
    """
    Open and return full content of a section.

    Args:
        manifest: Trial Manifest containing the section
        section_id: ID of the section to open

    Returns:
        Dict with section details and content, or None if not found
    """
    tools = ManifestTools(manifest)
    return tools.open_section(section_id)


def get_table(manifest: TrialManifest, table_id: str) -> Optional[Dict[str, Any]]:
    """
    Get full table data including all cells.

    Args:
        manifest: Trial Manifest containing the table
        table_id: ID of the table to retrieve

    Returns:
        Dict with table details and data, or None if not found
    """
    tools = ManifestTools(manifest)
    return tools.get_table(table_id)


def get_table_cell(manifest: TrialManifest, table_id: str, row: int, col: int) -> Optional[str]:
    """
    Get the value of a specific table cell.

    Args:
        manifest: Trial Manifest containing the table
        table_id: ID of the table
        row: Row index (0-based)
        col: Column index (0-based)

    Returns:
        Cell value as string, or None if not found
    """
    tools = ManifestTools(manifest)
    return tools.get_table_cell(table_id, row, col)


def get_table_row(manifest: TrialManifest, table_id: str, row: int) -> Optional[List[str]]:
    """
    Get all values in a table row.

    Args:
        manifest: Trial Manifest containing the table
        table_id: ID of the table
        row: Row index (0-based)

    Returns:
        List of cell values, or None if table not found
    """
    tools = ManifestTools(manifest)
    return tools.get_table_row(table_id, row)


def get_table_column(manifest: TrialManifest, table_id: str, col: int) -> Optional[List[str]]:
    """
    Get all values in a table column.

    Args:
        manifest: Trial Manifest containing the table
        table_id: ID of the table
        col: Column index (0-based)

    Returns:
        List of cell values, or None if table not found
    """
    tools = ManifestTools(manifest)
    return tools.get_table_column(table_id, col)


def get_document_sections(manifest: TrialManifest, doc_id: str) -> List[Dict[str, Any]]:
    """
    Get all sections for a specific document.

    Args:
        manifest: Trial Manifest
        doc_id: Document ID

    Returns:
        List of section dicts
    """
    ManifestTools(manifest)
    sections = manifest.get_sections_for_doc(doc_id)

    return [
        {
            "section_id": s.section_id,
            "title": s.title,
            "level": s.level,
            "word_count": s.word_count,
            "tags": s.tags,
        }
        for s in sections
    ]


def get_document_tables(manifest: TrialManifest, doc_id: str) -> List[Dict[str, Any]]:
    """
    Get all tables for a specific document.

    Args:
        manifest: Trial Manifest
        doc_id: Document ID

    Returns:
        List of table summary dicts
    """
    ManifestTools(manifest)
    tables = manifest.get_tables_for_doc(doc_id)

    return [
        {
            "table_id": t.table_id,
            "caption": t.caption,
            "num_rows": t.num_rows,
            "num_cols": t.num_cols,
            "headers": t.headers,
            "tags": t.tags,
        }
        for t in tables
    ]
