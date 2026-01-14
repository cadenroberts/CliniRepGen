"""
Tests for tools module.
"""

import pytest
from datetime import datetime

from clinirepgen.manifest.models import (
    TrialManifest,
    DocumentMetadata,
    Section,
    Table,
    TableCell,
)
from clinirepgen.tools.manifest_tools import ManifestTools, SearchResult
from clinirepgen.tools.search import search_sections, search_tables, search_all
from clinirepgen.tools.access import open_section, get_table, get_table_cell


@pytest.fixture
def sample_manifest():
    """Create a sample manifest for testing."""
    manifest = TrialManifest(
        manifest_id="test_manifest",
        trial_id="NCT12345678",
        created_at=datetime.now().isoformat(),
    )
    
    # Add document
    doc = DocumentMetadata(
        doc_id="doc_001",
        file_name="protocol.pdf",
        file_path="/path/to/protocol.pdf",
    )
    manifest.add_document(doc)
    
    # Add sections
    sections_data = [
        ("sec_001", "Introduction", "This is the introduction to the clinical trial."),
        ("sec_002", "Methods", "The study used randomization and blinding methods."),
        ("sec_003", "Results", "The primary endpoint showed significant efficacy."),
        ("sec_004", "Safety", "Adverse events were mild and transient."),
    ]
    
    for sec_id, title, content in sections_data:
        section = Section(
            section_id=sec_id,
            doc_id="doc_001",
            title=title,
            content=content,
            word_count=len(content.split()),
            tags=[title.lower()],
        )
        manifest.add_section(section)
    
    # Add table
    cells = [
        TableCell(row=0, col=0, value="Parameter", is_header=True),
        TableCell(row=0, col=1, value="Treatment", is_header=True),
        TableCell(row=0, col=2, value="Placebo", is_header=True),
        TableCell(row=1, col=0, value="Age (years)"),
        TableCell(row=1, col=1, value="45.2"),
        TableCell(row=1, col=2, value="44.8"),
        TableCell(row=2, col=0, value="Male (%)"),
        TableCell(row=2, col=1, value="52"),
        TableCell(row=2, col=2, value="48"),
    ]
    
    table = Table(
        table_id="tbl_001",
        doc_id="doc_001",
        section_id="sec_003",
        caption="Baseline Demographics",
        num_rows=3,
        num_cols=3,
        headers=["Parameter", "Treatment", "Placebo"],
        cells=cells,
        raw_data=[
            ["Parameter", "Treatment", "Placebo"],
            ["Age (years)", "45.2", "44.8"],
            ["Male (%)", "52", "48"],
        ],
        tags=["demographics", "baseline"],
    )
    manifest.add_table(table)
    
    return manifest


class TestManifestTools:
    """Tests for ManifestTools class."""
    
    def test_initialization(self, sample_manifest):
        """Test tools initialization."""
        tools = ManifestTools(sample_manifest)
        assert tools.manifest == sample_manifest
    
    def test_search_sections(self, sample_manifest):
        """Test section search."""
        tools = ManifestTools(sample_manifest)
        
        results = tools.search_sections("randomization")
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        # Methods section should be top result
        assert any("Methods" in r.title for r in results[:3])
    
    def test_search_sections_with_tags(self, sample_manifest):
        """Test section search with tag filter."""
        tools = ManifestTools(sample_manifest)
        
        results = tools.search_sections("study", tags=["methods"])
        
        assert len(results) > 0
        assert all("methods" in r.metadata.get("tags", []) for r in results)
    
    def test_search_tables(self, sample_manifest):
        """Test table search."""
        tools = ManifestTools(sample_manifest)
        
        results = tools.search_tables("demographics")
        
        assert len(results) > 0
        assert results[0].source_type == "table"
    
    def test_open_section(self, sample_manifest):
        """Test opening a section."""
        tools = ManifestTools(sample_manifest)
        
        result = tools.open_section("sec_002")
        
        assert result is not None
        assert result["title"] == "Methods"
        assert "randomization" in result["content"]
    
    def test_open_section_not_found(self, sample_manifest):
        """Test opening nonexistent section."""
        tools = ManifestTools(sample_manifest)
        
        result = tools.open_section("sec_nonexistent")
        assert result is None
    
    def test_get_table(self, sample_manifest):
        """Test getting table data."""
        tools = ManifestTools(sample_manifest)
        
        result = tools.get_table("tbl_001")
        
        assert result is not None
        assert result["caption"] == "Baseline Demographics"
        assert result["num_rows"] == 3
        assert result["num_cols"] == 3
    
    def test_get_table_cell(self, sample_manifest):
        """Test getting specific cell."""
        tools = ManifestTools(sample_manifest)
        
        value = tools.get_table_cell("tbl_001", 1, 1)
        assert value == "45.2"
        
        value = tools.get_table_cell("tbl_001", 2, 0)
        assert value == "Male (%)"
    
    def test_get_table_row(self, sample_manifest):
        """Test getting table row."""
        tools = ManifestTools(sample_manifest)
        
        row = tools.get_table_row("tbl_001", 0)
        assert row == ["Parameter", "Treatment", "Placebo"]
    
    def test_get_table_column(self, sample_manifest):
        """Test getting table column."""
        tools = ManifestTools(sample_manifest)
        
        col = tools.get_table_column("tbl_001", 0)
        assert col == ["Parameter", "Age (years)", "Male (%)"]


class TestSearchFunctions:
    """Tests for standalone search functions."""
    
    def test_search_sections_function(self, sample_manifest):
        """Test search_sections function."""
        results = search_sections(sample_manifest, "efficacy")
        
        assert len(results) > 0
    
    def test_search_tables_function(self, sample_manifest):
        """Test search_tables function."""
        results = search_tables(sample_manifest, "baseline")
        
        assert len(results) > 0
    
    def test_search_all_function(self, sample_manifest):
        """Test search_all function."""
        results = search_all(sample_manifest, "study")
        
        assert len(results) > 0
        # Should include both sections and tables
        source_types = {r.source_type for r in results}
        assert "section" in source_types


class TestAccessFunctions:
    """Tests for standalone access functions."""
    
    def test_open_section_function(self, sample_manifest):
        """Test open_section function."""
        result = open_section(sample_manifest, "sec_001")
        
        assert result is not None
        assert result["title"] == "Introduction"
    
    def test_get_table_function(self, sample_manifest):
        """Test get_table function."""
        result = get_table(sample_manifest, "tbl_001")
        
        assert result is not None
        assert "raw_data" in result
    
    def test_get_table_cell_function(self, sample_manifest):
        """Test get_table_cell function."""
        value = get_table_cell(sample_manifest, "tbl_001", 1, 2)
        assert value == "44.8"
