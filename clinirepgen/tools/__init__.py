"""
Tools module - APIs for searching and accessing the Trial Manifest.

Provides the tool interface used by agents to:
- Search sections by query and filters
- Open and read specific sections
- Search tables by query
- Access individual table cells
"""

from clinirepgen.tools.access import get_table, get_table_cell, open_section
from clinirepgen.tools.manifest_tools import ManifestTools
from clinirepgen.tools.search import search_sections, search_tables

__all__ = [
    "ManifestTools",
    "search_sections",
    "search_tables",
    "open_section",
    "get_table_cell",
    "get_table",
]
