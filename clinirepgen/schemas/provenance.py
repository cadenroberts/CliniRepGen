"""
Provenance model - Tracks where each fact came from in source documents.

Every extracted fact must have provenance linking it to the original
source location (file, section, table cell, character offsets).
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import hashlib


class ProvenanceType(str, Enum):
    """Type of source location for provenance."""
    SECTION = "section"
    TABLE_CELL = "table_cell"
    PARAGRAPH = "paragraph"
    FIGURE = "figure"
    LIST_ITEM = "list_item"
    HEADER = "header"
    FOOTNOTE = "footnote"
    UNKNOWN = "unknown"


class Provenance(BaseModel):
    """
    Provenance information for a single extracted fact.
    
    Tracks the exact source location in the original document(s)
    to enable verification and citation.
    """
    
    # Source document identification
    file_id: str = Field(
        ...,
        description="Unique identifier for the source file"
    )
    file_name: str = Field(
        ...,
        description="Original filename"
    )
    
    # Location within document
    section_id: Optional[str] = Field(
        default=None,
        description="ID of the section containing this content"
    )
    section_title: Optional[str] = Field(
        default=None,
        description="Title/heading of the section"
    )
    
    # For table cells
    table_id: Optional[str] = Field(
        default=None,
        description="ID of the table (if from a table)"
    )
    row_index: Optional[int] = Field(
        default=None,
        description="Row index in table (0-based)"
    )
    col_index: Optional[int] = Field(
        default=None,
        description="Column index in table (0-based)"
    )
    
    # Character-level location
    page_num: Optional[int] = Field(
        default=None,
        description="Page number (1-based)"
    )
    char_start: Optional[int] = Field(
        default=None,
        description="Start character offset"
    )
    char_end: Optional[int] = Field(
        default=None,
        description="End character offset"
    )
    
    # Extracted text span
    text_span: Optional[str] = Field(
        default=None,
        description="The exact text span extracted"
    )
    
    # Type classification
    source_type: ProvenanceType = Field(
        default=ProvenanceType.UNKNOWN,
        description="Type of source element"
    )
    
    # Extraction metadata
    extraction_method: Optional[str] = Field(
        default=None,
        description="Method used to extract (e.g., 'regex', 'llm', 'table_parse')"
    )
    extraction_timestamp: Optional[str] = Field(
        default=None,
        description="ISO timestamp of extraction"
    )
    
    model_config = {"use_enum_values": True}
    
    @property
    def provenance_id(self) -> str:
        """Generate a deterministic ID for this provenance record."""
        key_parts = [
            self.file_id,
            str(self.section_id or ""),
            str(self.table_id or ""),
            str(self.row_index or ""),
            str(self.col_index or ""),
            str(self.char_start or ""),
            str(self.char_end or ""),
        ]
        key = "|".join(key_parts)
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def to_citation(self) -> str:
        """Generate a human-readable citation string."""
        parts = [self.file_name]
        
        if self.section_title:
            parts.append(f"§{self.section_title}")
        elif self.section_id:
            parts.append(f"§{self.section_id}")
            
        if self.table_id:
            parts.append(f"Table {self.table_id}")
            if self.row_index is not None and self.col_index is not None:
                parts.append(f"[{self.row_index},{self.col_index}]")
                
        if self.page_num:
            parts.append(f"p.{self.page_num}")
            
        return ", ".join(parts)


class ProvenanceList(BaseModel):
    """A list of provenance records with conflict tracking."""
    
    provenances: List[Provenance] = Field(
        default_factory=list,
        description="List of provenance records"
    )
    has_conflicts: bool = Field(
        default=False,
        description="Whether there are conflicting values from different sources"
    )
    conflict_notes: Optional[str] = Field(
        default=None,
        description="Notes about any conflicts between sources"
    )
    
    def add(self, provenance: Provenance) -> None:
        """Add a provenance record."""
        self.provenances.append(provenance)
        
    def to_citations(self) -> List[str]:
        """Generate citation strings for all provenances."""
        return [p.to_citation() for p in self.provenances]
    
    @property
    def primary(self) -> Optional[Provenance]:
        """Get the primary (first) provenance record."""
        return self.provenances[0] if self.provenances else None
