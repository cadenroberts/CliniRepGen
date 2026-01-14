"""
Tests for schemas module.
"""

import pytest
from datetime import datetime

from clinirepgen.schemas.provenance import Provenance, ProvenanceType, ProvenanceList
from clinirepgen.schemas.trial_facts import (
    TrialFacts,
    FactValue,
    ConfidenceLevel,
    ChecklistItem,
    ChecklistCategory,
)
from clinirepgen.schemas.consort import CONSORT_CHECKLIST, get_consort_item
from clinirepgen.schemas.ich_e3 import ICH_E3_CHECKLIST, get_ich_e3_item


class TestProvenance:
    """Tests for Provenance model."""
    
    def test_create_provenance(self):
        """Test creating a basic provenance."""
        prov = Provenance(
            file_id="doc_123",
            file_name="protocol.pdf",
            section_title="Methods",
            page_num=5,
            text_span="The study was randomized...",
        )
        
        assert prov.file_id == "doc_123"
        assert prov.file_name == "protocol.pdf"
        assert prov.section_title == "Methods"
        assert prov.page_num == 5
    
    def test_provenance_id_deterministic(self):
        """Test that provenance ID is deterministic."""
        prov1 = Provenance(
            file_id="doc_123",
            file_name="test.pdf",
            char_start=100,
            char_end=200,
        )
        prov2 = Provenance(
            file_id="doc_123",
            file_name="test.pdf",
            char_start=100,
            char_end=200,
        )
        
        assert prov1.provenance_id == prov2.provenance_id
    
    def test_to_citation(self):
        """Test citation string generation."""
        prov = Provenance(
            file_id="doc_123",
            file_name="protocol.pdf",
            section_title="Methods",
            page_num=5,
        )
        
        citation = prov.to_citation()
        assert "protocol.pdf" in citation
        assert "Methods" in citation
        assert "p.5" in citation
    
    def test_table_citation(self):
        """Test citation for table cell."""
        prov = Provenance(
            file_id="doc_123",
            file_name="results.pdf",
            table_id="tbl_001",
            row_index=2,
            col_index=3,
        )
        
        citation = prov.to_citation()
        assert "Table tbl_001" in citation
        assert "[2,3]" in citation


class TestFactValue:
    """Tests for FactValue model."""
    
    def test_create_fact_value(self):
        """Test creating a fact value."""
        fact = FactValue(
            value="Randomized controlled trial",
            confidence=ConfidenceLevel.HIGH,
        )
        
        assert fact.value == "Randomized controlled trial"
        assert fact.confidence == ConfidenceLevel.HIGH
        assert not fact.is_null
    
    def test_null_fact(self):
        """Test null fact detection."""
        fact = FactValue()
        assert fact.is_null
        assert fact.is_low_confidence
    
    def test_add_provenance(self):
        """Test adding provenance to fact."""
        fact = FactValue(value="Test value")
        prov = Provenance(file_id="doc_1", file_name="test.pdf")
        
        fact.add_provenance(prov)
        
        assert len(fact.provenance.provenances) == 1
        assert fact.provenance.primary.file_name == "test.pdf"


class TestTrialFacts:
    """Tests for TrialFacts model."""
    
    def test_create_trial_facts(self):
        """Test creating TrialFacts."""
        facts = TrialFacts(
            trial_id="NCT12345678",
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        
        assert facts.trial_id == "NCT12345678"
        assert facts.identification is not None
        assert facts.design is not None
    
    def test_get_fact_by_path(self):
        """Test getting fact by path."""
        facts = TrialFacts(
            trial_id="NCT12345678",
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        
        # Set a value
        facts.identification.trial_title.value = "Test Trial"
        
        # Get by path
        fact = facts.get_fact_by_path("identification.trial_title")
        assert fact is not None
        assert fact.value == "Test Trial"
    
    def test_get_null_facts(self):
        """Test getting null facts."""
        facts = TrialFacts(
            trial_id="NCT12345678",
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        
        null_facts = facts.get_null_facts()
        assert len(null_facts) > 0  # Most facts should be null initially


class TestChecklist:
    """Tests for checklist data."""
    
    def test_consort_checklist_loaded(self):
        """Test CONSORT checklist is loaded."""
        assert len(CONSORT_CHECKLIST) > 0
        assert len(CONSORT_CHECKLIST) >= 30  # Should have ~30+ items
    
    def test_ich_e3_checklist_loaded(self):
        """Test ICH E3 checklist is loaded."""
        assert len(ICH_E3_CHECKLIST) > 0
    
    def test_get_consort_item(self):
        """Test getting specific CONSORT item."""
        item = get_consort_item("1a")
        assert item is not None
        assert item.item_id == "1a"
        assert "randomized" in item.description.lower()
    
    def test_get_ich_e3_item(self):
        """Test getting specific ICH E3 item."""
        item = get_ich_e3_item("2.1")
        assert item is not None
        assert "summary" in item.description.lower()
