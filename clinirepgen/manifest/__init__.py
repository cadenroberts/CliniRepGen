"""
Manifest module - Trial Manifest index for documents, sections, and tables.

The Trial Manifest is the entry point for the extraction pipeline.
It indexes all trial artifacts and provides search/access APIs.
"""

from clinirepgen.manifest.builder import ManifestBuilder
from clinirepgen.manifest.models import (
    DocumentMetadata,
    Section,
    Table,
    TableCell,
    TrialManifest,
)
from clinirepgen.manifest.section_splitter import SectionSplitter

__all__ = [
    "DocumentMetadata",
    "Section",
    "Table",
    "TableCell",
    "TrialManifest",
    "ManifestBuilder",
    "SectionSplitter",
]
