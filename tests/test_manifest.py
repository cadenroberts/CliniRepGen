"""
Tests for manifest module.
"""

import pytest
import json
import tempfile
from pathlib import Path

from clinirepgen.manifest.models import (
    DocumentMetadata,
    DocumentType,
    Section,
    Table,
    TableCell,
    TrialManifest,
)
from clinirepgen.manifest.builder import ManifestBuilder
from clinirepgen.manifest.section_splitter import SectionSplitter


class TestDocumentMetadata:
    """Tests for DocumentMetadata model."""
    
    def test_create_document(self):
        """Test creating document metadata."""
        doc = DocumentMetadata(
            doc_id="doc_123",
            file_name="protocol.pdf",
            file_path="/path/to/protocol.pdf",
            doc_type=DocumentType.PROTOCOL,
        )
        
        assert doc.doc_id == "doc_123"
        assert doc.file_name == "protocol.pdf"
        assert doc.doc_type == DocumentType.PROTOCOL


class TestSection:
    """Tests for Section model."""
    
    def test_create_section(self):
        """Test creating a section."""
        section = Section(
            section_id="sec_001",
            doc_id="doc_123",
            title="Introduction",
            level=1,
            content="This is the introduction section.",
        )
        
        assert section.section_id == "sec_001"
        assert section.title == "Introduction"
        assert section.level == 1
    
    def test_generate_section_id(self):
        """Test deterministic section ID generation."""
        id1 = Section.generate_id("doc_123", "Methods", 100)
        id2 = Section.generate_id("doc_123", "Methods", 100)
        id3 = Section.generate_id("doc_123", "Methods", 200)
        
        assert id1 == id2  # Same inputs = same ID
        assert id1 != id3  # Different char_start = different ID
        assert id1.startswith("sec_")


class TestTable:
    """Tests for Table model."""
    
    def test_create_table(self):
        """Test creating a table."""
        table = Table(
            table_id="tbl_001",
            doc_id="doc_123",
            caption="Baseline Demographics",
            num_rows=5,
            num_cols=3,
            headers=["Parameter", "Treatment", "Placebo"],
        )
        
        assert table.table_id == "tbl_001"
        assert table.caption == "Baseline Demographics"
        assert table.num_cols == 3
    
    def test_table_cell_access(self):
        """Test accessing table cells."""
        cells = [
            TableCell(row=0, col=0, value="Age", is_header=True),
            TableCell(row=0, col=1, value="Treatment", is_header=True),
            TableCell(row=1, col=0, value="Mean (SD)"),
            TableCell(row=1, col=1, value="45.2 (10.1)"),
        ]
        
        table = Table(
            table_id="tbl_001",
            doc_id="doc_123",
            num_rows=2,
            num_cols=2,
            cells=cells,
        )
        
        assert table.get_cell(0, 0) == "Age"
        assert table.get_cell(1, 1) == "45.2 (10.1)"
        assert table.get_cell(99, 99) is None


class TestTrialManifest:
    """Tests for TrialManifest model."""
    
    def test_create_manifest(self):
        """Test creating a manifest."""
        manifest = TrialManifest(
            manifest_id="manifest_001",
            trial_id="NCT12345678",
            created_at="2024-01-01T00:00:00",
        )
        
        assert manifest.trial_id == "NCT12345678"
        assert len(manifest.documents) == 0
    
    def test_add_document(self):
        """Test adding a document to manifest."""
        manifest = TrialManifest(
            manifest_id="manifest_001",
            trial_id="NCT12345678",
            created_at="2024-01-01T00:00:00",
        )
        
        doc = DocumentMetadata(
            doc_id="doc_001",
            file_name="protocol.pdf",
            file_path="/path/to/protocol.pdf",
        )
        
        manifest.add_document(doc)
        
        assert "doc_001" in manifest.documents
        assert manifest.get_document("doc_001") == doc
    
    def test_add_section(self):
        """Test adding a section to manifest."""
        manifest = TrialManifest(
            manifest_id="manifest_001",
            trial_id="NCT12345678",
            created_at="2024-01-01T00:00:00",
        )
        
        # First add document
        doc = DocumentMetadata(
            doc_id="doc_001",
            file_name="protocol.pdf",
            file_path="/path/to/protocol.pdf",
        )
        manifest.add_document(doc)
        
        # Then add section
        section = Section(
            section_id="sec_001",
            doc_id="doc_001",
            title="Methods",
            content="Test content",
        )
        manifest.add_section(section)
        
        assert "sec_001" in manifest.sections
        assert "sec_001" in manifest.doc_to_sections["doc_001"]
    
    def test_manifest_stats(self):
        """Test manifest statistics."""
        manifest = TrialManifest(
            manifest_id="manifest_001",
            trial_id="NCT12345678",
            created_at="2024-01-01T00:00:00",
        )
        
        stats = manifest.stats
        assert stats["num_documents"] == 0
        assert stats["num_sections"] == 0
        assert stats["num_tables"] == 0


class TestSectionSplitter:
    """Tests for SectionSplitter."""
    
    def test_detect_numbered_headings(self):
        """Test detecting numbered headings."""
        splitter = SectionSplitter()
        
        text = """
1. INTRODUCTION

This is the introduction.

1.1 Background

This is background info.

2. METHODS

This is methods.
"""
        
        headings = splitter.detect_headings(text)
        
        assert len(headings) >= 2
        titles = [h.text for h in headings]
        assert "INTRODUCTION" in titles or any("Introduction" in t for t in titles)
    
    def test_split_document(self):
        """Test splitting document into sections."""
        splitter = SectionSplitter(min_section_length=10)
        
        text = """
1. INTRODUCTION

This is the introduction section with enough content to be considered valid.

2. METHODS

This is the methods section with enough content to be considered valid.

3. RESULTS

This is the results section with enough content to be considered valid.
"""
        
        sections = splitter.split(text, "doc_001")
        
        assert len(sections) >= 2
        assert all("section_id" in s for s in sections)
        assert all("title" in s for s in sections)


class TestManifestBuilder:
    """Tests for ManifestBuilder."""
    
    def test_builder_initialization(self):
        """Test builder initialization."""
        builder = ManifestBuilder(trial_id="NCT12345678")
        
        assert builder.trial_id == "NCT12345678"
        assert len(builder.documents) == 0
    
    def test_add_ctgov_data(self):
        """Test adding ClinicalTrials.gov data."""
        builder = ManifestBuilder(trial_id="NCT12345678")
        
        ctgov_data = {
            "study": {
                "nct_id": "NCT12345678",
                "brief_title": "Test Study",
                "phase": "Phase 3",
            },
            "interventions": [
                {"name": "Drug A", "intervention_type": "Drug", "description": "Test drug"}
            ],
            "outcomes": [
                {"outcome_type": "Primary", "title": "Test Outcome", "time_frame": "Week 12"}
            ],
        }
        
        doc_id = builder.add_ctgov_data(ctgov_data)
        manifest = builder.build()
        
        assert doc_id.startswith("doc_ctgov_")
        assert len(manifest.sections) > 0
    
    def test_build_manifest(self):
        """Test building complete manifest."""
        builder = ManifestBuilder(trial_id="NCT12345678")
        
        ctgov_data = {
            "study": {"nct_id": "NCT12345678", "brief_title": "Test"},
        }
        builder.add_ctgov_data(ctgov_data)
        
        manifest = builder.build()
        
        assert manifest.trial_id == "NCT12345678"
        assert len(manifest.documents) >= 1
    
    def test_save_manifest(self):
        """Test saving manifest to file."""
        builder = ManifestBuilder(trial_id="NCT12345678")
        
        ctgov_data = {"study": {"nct_id": "NCT12345678"}}
        builder.add_ctgov_data(ctgov_data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest.json"
            saved_path = builder.save(str(output_path))
            
            assert Path(saved_path).exists()
            
            # Verify JSON is valid
            with open(saved_path) as f:
                data = json.load(f)
            assert data["trial_id"] == "NCT12345678"
