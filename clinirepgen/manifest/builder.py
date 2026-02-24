"""
Manifest Builder - Builds Trial Manifest from source documents.

Orchestrates document parsing, section splitting, and table extraction
to create a complete Trial Manifest index.
"""

import os
import hashlib
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from clinirepgen.manifest.models import (
    DocumentMetadata,
    DocumentType,
    Section,
    Table,
    TableCell,
    TrialManifest,
)
from clinirepgen.manifest.section_splitter import SectionSplitter

logger = logging.getLogger(__name__)


def detect_doc_type(filename: str) -> DocumentType:
    """Detect document type from filename."""
    filename_lower = filename.lower()
    
    if "protocol" in filename_lower or "prot_" in filename_lower:
        return DocumentType.PROTOCOL
    elif "csr" in filename_lower or "clinical_study_report" in filename_lower:
        return DocumentType.CSR
    elif "sap" in filename_lower or "statistical" in filename_lower:
        return DocumentType.SAP
    elif "icf" in filename_lower or "consent" in filename_lower:
        return DocumentType.ICF
    elif "ib" in filename_lower or "brochure" in filename_lower:
        return DocumentType.IB
    elif any(ext in filename_lower for ext in [".pdf", ".docx"]):
        # Check for journal patterns
        if any(pat in filename_lower for pat in ["lancet", "nejm", "jama", "bmj"]):
            return DocumentType.JOURNAL
    
    return DocumentType.OTHER


class ManifestBuilder:
    """
    Builds a Trial Manifest from source documents.
    
    Usage:
        builder = ManifestBuilder(trial_id="NCT12345678")
        builder.add_document("/path/to/protocol.pdf")
        builder.add_document("/path/to/csr.pdf")
        manifest = builder.build()
    """
    
    def __init__(self, trial_id: str, output_dir: Optional[str] = None):
        """
        Initialize the manifest builder.
        
        Args:
            trial_id: Unique identifier for the trial
            output_dir: Directory for output files (optional)
        """
        self.trial_id = trial_id
        self.output_dir = output_dir or "."
        
        # Manifest ID will be computed deterministically in build()
        self.manifest_id: Optional[str] = None
        self.created_at: Optional[str] = None
        
        self.documents: Dict[str, DocumentMetadata] = {}
        self.sections: Dict[str, Section] = {}
        self.tables: Dict[str, Table] = {}
        
        self.section_splitter = SectionSplitter()
        
        # Track relationships
        self.doc_to_sections: Dict[str, List[str]] = {}
        self.doc_to_tables: Dict[str, List[str]] = {}
        self.section_to_tables: Dict[str, List[str]] = {}
    
    def add_document(self, file_path: str, doc_type: Optional[DocumentType] = None) -> str:
        """
        Add a document to the manifest.
        
        Args:
            file_path: Path to the document file
            doc_type: Optional explicit document type
            
        Returns:
            Document ID
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Generate deterministic doc ID
        file_hash = self._hash_file(file_path)
        doc_id = f"doc_{file_hash[:12]}"
        
        # Detect document type
        if doc_type is None:
            doc_type = detect_doc_type(path.name)
        
        # Create document metadata
        doc = DocumentMetadata(
            doc_id=doc_id,
            file_name=path.name,
            file_path=str(path.absolute()),
            doc_type=doc_type,
            file_size_bytes=path.stat().st_size,
            file_hash=file_hash,
            processed_at=datetime.now().isoformat(),
        )
        
        self.documents[doc_id] = doc
        self.doc_to_sections[doc_id] = []
        self.doc_to_tables[doc_id] = []
        
        logger.info(f"Added document: {path.name} (type={doc_type}, id={doc_id})")
        
        return doc_id
    
    def add_ctgov_data(self, ctgov_json: Dict[str, Any]) -> str:
        """
        Add ClinicalTrials.gov data to the manifest.
        
        Args:
            ctgov_json: Parsed ClinicalTrials.gov JSON data
            
        Returns:
            Document ID for the CT.gov record
        """
        nct_id = ctgov_json.get("study", {}).get("nct_id", self.trial_id)
        
        # Create a virtual document for CT.gov data
        doc_id = f"doc_ctgov_{nct_id}"
        
        doc = DocumentMetadata(
            doc_id=doc_id,
            file_name=f"{nct_id}_ctgov.json",
            file_path="",
            doc_type=DocumentType.CTGOV_RECORD,
            processed_at=datetime.now().isoformat(),
        )
        
        self.documents[doc_id] = doc
        self.doc_to_sections[doc_id] = []
        self.doc_to_tables[doc_id] = []
        
        # Extract structured data as sections
        self._process_ctgov_data(doc_id, ctgov_json)
        
        logger.info(f"Added ClinicalTrials.gov data: {nct_id}")
        
        return doc_id
    
    def _process_ctgov_data(self, doc_id: str, data: Dict[str, Any]) -> None:
        """Process ClinicalTrials.gov data into sections."""
        
        study = data.get("study", {})
        if study:
            # Create study metadata section
            section_id = Section.generate_id(doc_id, "Study Metadata", 0)
            section = Section(
                section_id=section_id,
                doc_id=doc_id,
                title="Study Metadata",
                level=1,
                content=json.dumps(study, indent=2),
            )
            self.sections[section_id] = section
            self.doc_to_sections[doc_id].append(section_id)
        
        # Process interventions
        interventions = data.get("interventions", [])
        if interventions:
            section_id = Section.generate_id(doc_id, "Interventions", 100)
            content = "\n".join([
                f"- {i.get('name', 'N/A')} ({i.get('intervention_type', 'N/A')}): {i.get('description', 'N/A')}"
                for i in interventions
            ])
            section = Section(
                section_id=section_id,
                doc_id=doc_id,
                title="Interventions",
                level=1,
                content=content,
                tags=["interventions"],
            )
            self.sections[section_id] = section
            self.doc_to_sections[doc_id].append(section_id)
        
        # Process outcomes
        outcomes = data.get("outcomes", [])
        if outcomes:
            section_id = Section.generate_id(doc_id, "Outcomes", 200)
            content = "\n".join([
                f"- [{o.get('outcome_type', 'N/A')}] {o.get('title', 'N/A')}: {o.get('description', 'N/A')} (timeframe: {o.get('time_frame', 'N/A')})"
                for o in outcomes
            ])
            section = Section(
                section_id=section_id,
                doc_id=doc_id,
                title="Outcomes",
                level=1,
                content=content,
                tags=["outcomes", "endpoints"],
            )
            self.sections[section_id] = section
            self.doc_to_sections[doc_id].append(section_id)
        
        # Process adverse events
        adverse_events = data.get("adverse_events", [])
        if adverse_events:
            section_id = Section.generate_id(doc_id, "Adverse Events", 300)
            
            # Also create a table for adverse events
            table_id = Table.generate_id(doc_id, 1, 0)
            
            headers = ["Event Type", "Organ System", "Term", "Subjects Affected", "Subjects at Risk"]
            raw_data = [headers]
            cells = []
            
            for col_idx, header in enumerate(headers):
                cells.append(TableCell(row=0, col=col_idx, value=header, is_header=True))
            
            for row_idx, ae in enumerate(adverse_events, start=1):
                row_values = [
                    str(ae.get("event_type", "")),
                    str(ae.get("organ_system", "")),
                    str(ae.get("adverse_event_term", "")),
                    str(ae.get("subjects_affected", "")),
                    str(ae.get("subjects_at_risk", "")),
                ]
                raw_data.append(row_values)
                for col_idx, value in enumerate(row_values):
                    cells.append(TableCell(row=row_idx, col=col_idx, value=value))
            
            table = Table(
                table_id=table_id,
                doc_id=doc_id,
                section_id=section_id,
                caption="Adverse Events",
                num_rows=len(raw_data),
                num_cols=len(headers),
                headers=headers,
                cells=cells,
                raw_data=raw_data,
                tags=["safety", "adverse_events"],
            )
            self.tables[table_id] = table
            self.doc_to_tables[doc_id].append(table_id)
            
            section = Section(
                section_id=section_id,
                doc_id=doc_id,
                title="Adverse Events",
                level=1,
                content=f"See Table {table_id} for adverse event summary.",
                has_tables=True,
                table_ids=[table_id],
                tags=["safety", "adverse_events"],
            )
            self.sections[section_id] = section
            self.doc_to_sections[doc_id].append(section_id)
            
            if section_id not in self.section_to_tables:
                self.section_to_tables[section_id] = []
            self.section_to_tables[section_id].append(table_id)
    
    def process_document_text(self, doc_id: str, text: str, 
                              page_map: Optional[Dict[int, int]] = None) -> None:
        """
        Process extracted document text into sections.
        
        Args:
            doc_id: Document ID
            text: Full document text
            page_map: Optional mapping of char positions to page numbers
        """
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not in manifest")
        
        # Split into sections
        section_dicts = self.section_splitter.split(text, doc_id)
        section_dicts = self.section_splitter.estimate_page_numbers(section_dicts)
        
        # Create Section objects
        for sd in section_dicts:
            section = Section(
                section_id=sd["section_id"],
                doc_id=doc_id,
                title=sd["title"],
                level=sd["level"],
                section_number=sd.get("section_number"),
                content=sd["content"],
                char_start=sd.get("char_start"),
                char_end=sd.get("char_end"),
                page_start=sd.get("page_start"),
                page_end=sd.get("page_end"),
                parent_section_id=sd.get("parent_section_id"),
                child_section_ids=sd.get("child_section_ids", []),
                word_count=len(sd["content"].split()),
            )
            
            # Auto-tag sections
            section.tags = self._auto_tag_section(section)
            
            self.sections[section.section_id] = section
            self.doc_to_sections[doc_id].append(section.section_id)
        
        # Update document stats
        doc = self.documents[doc_id]
        doc.num_sections = len(section_dicts)
        doc.total_chars = len(text)
        
        logger.info(f"Processed {len(section_dicts)} sections from {doc_id}")
    
    def add_table(self, doc_id: str, table_data: Dict[str, Any],
                  section_id: Optional[str] = None) -> str:
        """
        Add a table to the manifest.
        
        Args:
            doc_id: Parent document ID
            table_data: Table data dict with headers, rows, etc.
            section_id: Optional containing section ID
            
        Returns:
            Table ID
        """
        page_num = table_data.get("page_num", 1)
        table_index = len(self.doc_to_tables.get(doc_id, []))
        
        table_id = Table.generate_id(doc_id, page_num, table_index)
        
        # Extract cells from raw data
        cells = []
        raw_data = table_data.get("raw_data", [])
        headers = table_data.get("headers", [])
        
        if not headers and raw_data:
            headers = raw_data[0] if raw_data else []
        
        for row_idx, row in enumerate(raw_data):
            for col_idx, value in enumerate(row):
                cells.append(TableCell(
                    row=row_idx,
                    col=col_idx,
                    value=str(value),
                    is_header=(row_idx == 0),
                ))
        
        table = Table(
            table_id=table_id,
            doc_id=doc_id,
            section_id=section_id,
            caption=table_data.get("caption"),
            table_number=table_data.get("table_number"),
            num_rows=len(raw_data),
            num_cols=len(headers),
            headers=headers,
            cells=cells,
            raw_data=raw_data,
            markdown=table_data.get("markdown"),
            page_num=page_num,
            tags=table_data.get("tags", []),
        )
        
        self.tables[table_id] = table
        self.doc_to_tables[doc_id].append(table_id)
        
        if section_id:
            if section_id not in self.section_to_tables:
                self.section_to_tables[section_id] = []
            self.section_to_tables[section_id].append(table_id)
            
            # Update section
            if section_id in self.sections:
                self.sections[section_id].has_tables = True
                self.sections[section_id].table_ids.append(table_id)
        
        logger.info(f"Added table {table_id} to {doc_id}")
        
        return table_id
    
    def _auto_tag_section(self, section: Section) -> List[str]:
        """Auto-generate semantic tags for a section based on title/content."""
        tags = []
        title_lower = section.title.lower()
        
        tag_patterns = {
            "methods": ["method", "methodology", "study design", "design"],
            "eligibility": ["eligibility", "inclusion", "exclusion", "criteria"],
            "randomization": ["randomization", "randomisation", "random allocation"],
            "blinding": ["blind", "masking"],
            "outcomes": ["outcome", "endpoint", "primary", "secondary"],
            "results": ["result", "finding"],
            "efficacy": ["efficacy", "effectiveness"],
            "safety": ["safety", "adverse", "harm", "toxicity"],
            "statistics": ["statistic", "analysis", "sample size"],
            "demographics": ["demographic", "baseline", "characteristic"],
            "discussion": ["discussion", "interpretation"],
            "conclusions": ["conclusion", "summary"],
        }
        
        for tag, patterns in tag_patterns.items():
            if any(pat in title_lower for pat in patterns):
                tags.append(tag)
        
        return tags
    
    def _hash_file(self, file_path: str) -> str:
        """Generate SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def build(self) -> TrialManifest:
        """
        Build the final Trial Manifest.
        
        Returns:
            Complete TrialManifest object
        """
        # Compute a deterministic manifest_id based on trial_id and document hashes
        # Collect available file hashes (skip virtual CT.gov docs)
        hashes = [d.file_hash for d in self.documents.values() if getattr(d, 'file_hash', None)]
        if hashes:
            combined = "".join(sorted(hashes))
        else:
            combined = self.trial_id

        manifest_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()[:12]
        self.manifest_id = f"manifest_{self.trial_id}_{manifest_hash}"
        self.created_at = datetime.now().isoformat()

        manifest = TrialManifest(
            manifest_id=self.manifest_id,
            trial_id=self.trial_id,
            created_at=self.created_at,
            documents=self.documents,
            sections=self.sections,
            tables=self.tables,
            doc_to_sections=self.doc_to_sections,
            doc_to_tables=self.doc_to_tables,
            section_to_tables=self.section_to_tables,
        )
        
        logger.info(f"Built manifest: {manifest.stats}")
        
        return manifest
    
    def save(self, output_path: Optional[str] = None) -> str:
        """
        Save the manifest to JSON file.
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to saved file
        """
        manifest = self.build()
        
        if output_path is None:
            output_path = os.path.join(self.output_dir, f"{self.manifest_id}.json")
        
        with open(output_path, "w") as f:
            f.write(manifest.model_dump_json(indent=2))
        
        logger.info(f"Saved manifest to {output_path}")
        
        return output_path
