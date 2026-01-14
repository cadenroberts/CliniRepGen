"""
Manifest models - Core data structures for the Trial Manifest.

The Trial Manifest indexes all trial documents by:
- Documents: source files (PDFs, protocols, CSRs, etc.)
- Sections: logical document sections with headers
- Tables: extracted tables with cell-level access
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import hashlib


class DocumentType(str, Enum):
    """Type of trial document."""
    PROTOCOL = "protocol"
    CSR = "csr"  # Clinical Study Report
    SAP = "sap"  # Statistical Analysis Plan
    ICF = "icf"  # Informed Consent Form
    IB = "ib"    # Investigator's Brochure
    JOURNAL = "journal"  # Published paper
    FDA_REVIEW = "fda_review"
    CTGOV_RECORD = "ctgov_record"
    OTHER = "other"


class DocumentMetadata(BaseModel):
    """Metadata for a source document in the manifest."""
    
    model_config = {"use_enum_values": True}
    
    doc_id: str = Field(
        ...,
        description="Unique deterministic ID for this document"
    )
    file_name: str = Field(
        ...,
        description="Original filename"
    )
    file_path: str = Field(
        ...,
        description="Path to the file"
    )
    doc_type: DocumentType = Field(
        default=DocumentType.OTHER,
        description="Type of document"
    )
    
    # Document properties
    title: Optional[str] = Field(default=None)
    num_pages: Optional[int] = Field(default=None)
    file_size_bytes: Optional[int] = Field(default=None)
    file_hash: Optional[str] = Field(default=None)
    
    # Processing metadata
    processed_at: Optional[str] = Field(default=None)
    parser_version: Optional[str] = Field(default=None)
    
    # Content statistics
    num_sections: int = Field(default=0)
    num_tables: int = Field(default=0)
    total_chars: int = Field(default=0)


class Section(BaseModel):
    """A logical section within a document."""
    
    section_id: str = Field(
        ...,
        description="Unique deterministic ID for this section"
    )
    doc_id: str = Field(
        ...,
        description="ID of the parent document"
    )
    
    # Section identification
    title: str = Field(
        ...,
        description="Section title/heading"
    )
    level: int = Field(
        default=1,
        description="Heading level (1 = top level)"
    )
    section_number: Optional[str] = Field(
        default=None,
        description="Section number if present (e.g., '3.2.1')"
    )
    
    # Content
    content: str = Field(
        default="",
        description="Full text content of the section"
    )
    
    # Location
    page_start: Optional[int] = Field(default=None)
    page_end: Optional[int] = Field(default=None)
    char_start: Optional[int] = Field(default=None)
    char_end: Optional[int] = Field(default=None)
    
    # Hierarchy
    parent_section_id: Optional[str] = Field(default=None)
    child_section_ids: List[str] = Field(default_factory=list)
    
    # Content metadata
    word_count: int = Field(default=0)
    has_tables: bool = Field(default=False)
    table_ids: List[str] = Field(default_factory=list)
    
    # Semantic tags for search
    tags: List[str] = Field(
        default_factory=list,
        description="Semantic tags (e.g., 'methods', 'randomization')"
    )
    
    @classmethod
    def generate_id(cls, doc_id: str, title: str, char_start: int) -> str:
        """Generate a deterministic section ID."""
        key = f"{doc_id}|{title}|{char_start}"
        return f"sec_{hashlib.sha256(key.encode()).hexdigest()[:12]}"


class TableCell(BaseModel):
    """A single cell in a table."""
    
    row: int = Field(..., description="Row index (0-based)")
    col: int = Field(..., description="Column index (0-based)")
    value: str = Field(default="", description="Cell content")
    is_header: bool = Field(default=False)
    row_span: int = Field(default=1)
    col_span: int = Field(default=1)


class Table(BaseModel):
    """An extracted table from a document."""
    
    table_id: str = Field(
        ...,
        description="Unique deterministic ID for this table"
    )
    doc_id: str = Field(
        ...,
        description="ID of the parent document"
    )
    section_id: Optional[str] = Field(
        default=None,
        description="ID of the containing section"
    )
    
    # Table identification
    caption: Optional[str] = Field(default=None)
    table_number: Optional[str] = Field(
        default=None,
        description="Table number (e.g., 'Table 1')"
    )
    
    # Structure
    num_rows: int = Field(default=0)
    num_cols: int = Field(default=0)
    headers: List[str] = Field(default_factory=list)
    
    # Cell data
    cells: List[TableCell] = Field(
        default_factory=list,
        description="All cells in the table"
    )
    
    # Raw formats
    markdown: Optional[str] = Field(
        default=None,
        description="Markdown representation"
    )
    raw_data: Optional[List[List[str]]] = Field(
        default=None,
        description="Raw 2D array of cell values"
    )
    
    # Location
    page_num: Optional[int] = Field(default=None)
    
    # Semantic tags
    tags: List[str] = Field(
        default_factory=list,
        description="Semantic tags (e.g., 'demographics', 'efficacy')"
    )
    
    @classmethod
    def generate_id(cls, doc_id: str, page_num: int, table_index: int) -> str:
        """Generate a deterministic table ID."""
        key = f"{doc_id}|{page_num}|{table_index}"
        return f"tbl_{hashlib.sha256(key.encode()).hexdigest()[:12]}"
    
    def get_cell(self, row: int, col: int) -> Optional[str]:
        """Get value of a specific cell."""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell.value
        return None
    
    def get_row(self, row: int) -> List[str]:
        """Get all values in a row."""
        return [c.value for c in sorted(
            [cell for cell in self.cells if cell.row == row],
            key=lambda x: x.col
        )]
    
    def get_column(self, col: int) -> List[str]:
        """Get all values in a column."""
        return [c.value for c in sorted(
            [cell for cell in self.cells if cell.col == col],
            key=lambda x: x.row
        )]
    
    def to_dict_rows(self) -> List[Dict[str, str]]:
        """Convert table to list of dicts using headers as keys."""
        if not self.headers or not self.raw_data:
            return []
        
        result = []
        for row_idx, row in enumerate(self.raw_data):
            if row_idx == 0 and self.headers:
                continue  # Skip header row
            row_dict = {}
            for col_idx, value in enumerate(row):
                if col_idx < len(self.headers):
                    row_dict[self.headers[col_idx]] = value
            result.append(row_dict)
        return result


class TrialManifest(BaseModel):
    """
    Complete Trial Manifest - indexes all documents, sections, and tables.
    
    This is the entry point for the extraction pipeline and provides
    search/access APIs over all trial artifacts.
    """
    
    # Manifest metadata
    manifest_id: str = Field(
        ...,
        description="Unique ID for this manifest"
    )
    trial_id: str = Field(
        ...,
        description="ID of the trial this manifest represents"
    )
    created_at: str = Field(
        ...,
        description="ISO timestamp of manifest creation"
    )
    
    # Indexed content
    documents: Dict[str, DocumentMetadata] = Field(
        default_factory=dict,
        description="Document ID -> DocumentMetadata"
    )
    sections: Dict[str, Section] = Field(
        default_factory=dict,
        description="Section ID -> Section"
    )
    tables: Dict[str, Table] = Field(
        default_factory=dict,
        description="Table ID -> Table"
    )
    
    # Indices for fast lookup
    doc_to_sections: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Document ID -> list of section IDs"
    )
    doc_to_tables: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Document ID -> list of table IDs"
    )
    section_to_tables: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Section ID -> list of table IDs"
    )
    
    def add_document(self, doc: DocumentMetadata) -> None:
        """Add a document to the manifest."""
        self.documents[doc.doc_id] = doc
        if doc.doc_id not in self.doc_to_sections:
            self.doc_to_sections[doc.doc_id] = []
        if doc.doc_id not in self.doc_to_tables:
            self.doc_to_tables[doc.doc_id] = []
    
    def add_section(self, section: Section) -> None:
        """Add a section to the manifest."""
        self.sections[section.section_id] = section
        if section.doc_id in self.doc_to_sections:
            self.doc_to_sections[section.doc_id].append(section.section_id)
        else:
            self.doc_to_sections[section.doc_id] = [section.section_id]
    
    def add_table(self, table: Table) -> None:
        """Add a table to the manifest."""
        self.tables[table.table_id] = table
        
        if table.doc_id in self.doc_to_tables:
            self.doc_to_tables[table.doc_id].append(table.table_id)
        else:
            self.doc_to_tables[table.doc_id] = [table.table_id]
        
        if table.section_id:
            if table.section_id in self.section_to_tables:
                self.section_to_tables[table.section_id].append(table.table_id)
            else:
                self.section_to_tables[table.section_id] = [table.table_id]
    
    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get a document by ID."""
        return self.documents.get(doc_id)
    
    def get_section(self, section_id: str) -> Optional[Section]:
        """Get a section by ID."""
        return self.sections.get(section_id)
    
    def get_table(self, table_id: str) -> Optional[Table]:
        """Get a table by ID."""
        return self.tables.get(table_id)
    
    def get_sections_for_doc(self, doc_id: str) -> List[Section]:
        """Get all sections for a document."""
        section_ids = self.doc_to_sections.get(doc_id, [])
        return [self.sections[sid] for sid in section_ids if sid in self.sections]
    
    def get_tables_for_doc(self, doc_id: str) -> List[Table]:
        """Get all tables for a document."""
        table_ids = self.doc_to_tables.get(doc_id, [])
        return [self.tables[tid] for tid in table_ids if tid in self.tables]
    
    def get_tables_for_section(self, section_id: str) -> List[Table]:
        """Get all tables within a section."""
        table_ids = self.section_to_tables.get(section_id, [])
        return [self.tables[tid] for tid in table_ids if tid in self.tables]
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get manifest statistics."""
        return {
            "num_documents": len(self.documents),
            "num_sections": len(self.sections),
            "num_tables": len(self.tables),
        }
