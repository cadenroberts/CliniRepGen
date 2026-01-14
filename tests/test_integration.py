"""
Integration tests - End-to-end pipeline tests.

These tests verify the complete pipeline works correctly
using sample data.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from clinirepgen.manifest.builder import ManifestBuilder
from clinirepgen.schemas.trial_facts import TrialFacts, ConfidenceLevel
from clinirepgen.schemas.provenance import Provenance, ProvenanceType
from clinirepgen.pipeline.ingest import IngestStage
from clinirepgen.reports.renderer import MarkdownRenderer, render_consort
from clinirepgen.reports.templates import CONSORTTemplate, ICHE3Template


# Sample CT.gov data for testing
SAMPLE_CTGOV_DATA = {
    "study": {
        "nct_id": "NCT00000001",
        "brief_title": "Test Clinical Trial",
        "official_title": "A Randomized Controlled Trial for Testing",
        "phase": "Phase 3",
        "study_type": "Interventional",
        "enrollment": 200,
        "start_date": "2023-01-01",
        "completion_date": "2024-06-30",
        "overall_status": "Completed"
    },
    "interventions": [
        {
            "intervention_type": "Drug",
            "name": "Test Drug",
            "description": "10mg once daily"
        },
        {
            "intervention_type": "Drug",
            "name": "Placebo",
            "description": "Matching placebo"
        }
    ],
    "outcomes": [
        {
            "outcome_type": "Primary",
            "title": "Change in Primary Endpoint",
            "time_frame": "Week 12",
            "description": "Mean change from baseline"
        }
    ],
    "adverse_events": [
        {
            "event_type": "Other",
            "organ_system": "Gastrointestinal",
            "adverse_event_term": "Nausea",
            "subjects_affected": 10,
            "subjects_at_risk": 100
        }
    ]
}


class TestManifestBuilding:
    """Test manifest building from various sources."""
    
    def test_build_from_ctgov(self):
        """Test building manifest from CT.gov data."""
        builder = ManifestBuilder(trial_id="NCT00000001")
        builder.add_ctgov_data(SAMPLE_CTGOV_DATA)
        
        manifest = builder.build()
        
        assert manifest.trial_id == "NCT00000001"
        assert len(manifest.documents) >= 1
        assert len(manifest.sections) >= 1
    
    def test_build_from_text_file(self):
        """Test building manifest from text file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample text file with enough content per section
            text_file = Path(tmpdir) / "protocol.txt"
            text_file.write_text("""
1. INTRODUCTION

This is the introduction section of the clinical trial protocol. It describes the background and rationale for conducting this randomized controlled study. The introduction provides important context about the disease area and unmet medical need.

2. METHODS

This is the methods section describing the trial design in detail. It covers the randomization procedure, blinding methods, eligibility criteria, treatment administration, and outcome assessments. The methods section is critical for reproducibility.

3. RESULTS

This is the results section presenting the primary and secondary outcomes. It includes efficacy data, safety findings, and statistical analyses. The results section summarizes the key findings of the clinical trial.
""")
            
            builder = ManifestBuilder(trial_id="TEST001", output_dir=tmpdir)
            doc_id = builder.add_document(str(text_file))
            
            with open(text_file) as f:
                text = f.read()
            builder.process_document_text(doc_id, text)
            
            manifest = builder.build()
            
            assert len(manifest.documents) == 1
            assert len(manifest.sections) >= 1


class TestTrialFactsPopulation:
    """Test populating TrialFacts from various sources."""
    
    def test_create_populated_facts(self):
        """Test creating and populating TrialFacts."""
        facts = TrialFacts(
            trial_id="NCT00000001",
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        
        # Populate from CT.gov data
        facts.identification.nct_id.value = SAMPLE_CTGOV_DATA["study"]["nct_id"]
        facts.identification.nct_id.confidence = ConfidenceLevel.HIGH
        facts.identification.nct_id.add_provenance(Provenance(
            file_id="ctgov",
            file_name="clinicaltrials.gov",
            source_type=ProvenanceType.SECTION,
        ))
        
        facts.identification.trial_title.value = SAMPLE_CTGOV_DATA["study"]["brief_title"]
        facts.identification.trial_title.confidence = ConfidenceLevel.HIGH
        
        facts.identification.phase.value = SAMPLE_CTGOV_DATA["study"]["phase"]
        facts.population.target_enrollment.value = SAMPLE_CTGOV_DATA["study"]["enrollment"]
        
        # Verify population
        assert facts.identification.nct_id.value == "NCT00000001"
        assert not facts.identification.nct_id.is_null
        assert facts.identification.nct_id.confidence == ConfidenceLevel.HIGH
    
    def test_facts_coverage_tracking(self):
        """Test tracking fact coverage."""
        facts = TrialFacts(
            trial_id="NCT00000001",
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        
        # Initially all should be null
        null_facts = facts.get_null_facts()
        assert len(null_facts) > 10
        
        # Populate some facts
        facts.identification.trial_title.value = "Test Trial"
        facts.design.design_type.value = "Randomized"
        
        # Check coverage improved
        new_null_facts = facts.get_null_facts()
        assert len(new_null_facts) < len(null_facts)


class TestReportGeneration:
    """Test report generation from TrialFacts."""
    
    def test_render_consort_report(self):
        """Test rendering CONSORT report."""
        facts = TrialFacts(
            trial_id="NCT00000001",
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        
        # Populate minimal facts
        facts.identification.trial_title.value = "Test Randomized Trial"
        facts.design.design_type.value = "Parallel, randomized, double-blind"
        facts.outcomes.primary_outcome.value = "Change in disease score"
        
        # Render report
        markdown = render_consort(facts)
        
        assert "Test Randomized Trial" in markdown
        assert "CONSORT" in markdown
        assert len(markdown) > 100
    
    def test_templates_have_sections(self):
        """Test that templates define sections."""
        consort = CONSORTTemplate()
        ich_e3 = ICHE3Template()
        
        assert len(consort.get_sections()) >= 5
        assert len(ich_e3.get_sections()) >= 8
        
        # Check section structure
        methods = consort.get_section("methods")
        assert methods is not None
        assert len(methods.subsections) > 0


class TestIngestStage:
    """Test ingestion stage."""
    
    def test_ingest_ctgov_json(self):
        """Test ingesting CT.gov JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save sample data to file
            json_file = Path(tmpdir) / "ctgov.json"
            json_file.write_text(json.dumps(SAMPLE_CTGOV_DATA))
            
            stage = IngestStage(trial_id="NCT00000001", output_dir=tmpdir)
            doc_id = stage.ingest_ctgov_file(str(json_file))
            
            manifest = stage.build()
            
            assert doc_id.startswith("doc_ctgov")
            assert len(manifest.sections) >= 1
    
    def test_ingest_directory(self):
        """Test ingesting directory of files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample files
            (Path(tmpdir) / "protocol.txt").write_text("1. METHODS\n\nTest methods content.")
            (Path(tmpdir) / "results.txt").write_text("1. RESULTS\n\nTest results content.")
            
            stage = IngestStage(trial_id="TEST001", output_dir=tmpdir)
            manifest = stage.ingest_directory(tmpdir)
            
            assert len(manifest.documents) >= 2


class TestMarkdownRenderer:
    """Test markdown rendering."""
    
    def test_render_facts_summary(self):
        """Test rendering facts summary."""
        facts = TrialFacts(
            trial_id="NCT00000001",
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        facts.identification.trial_title.value = "Test Trial"
        facts.identification.phase.value = "Phase 3"
        
        renderer = MarkdownRenderer()
        markdown = renderer.render_facts_summary(facts)
        
        assert "Trial Facts Summary" in markdown
        assert "NCT00000001" in markdown
        assert "Test Trial" in markdown


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_ctgov_to_manifest_to_report(self):
        """Test full flow from CT.gov data to report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Build manifest from CT.gov data
            builder = ManifestBuilder(trial_id="NCT00000001", output_dir=tmpdir)
            builder.add_ctgov_data(SAMPLE_CTGOV_DATA)
            manifest = builder.build()
            
            assert manifest.trial_id == "NCT00000001"
            
            # Step 2: Create TrialFacts (simulating extraction)
            facts = TrialFacts(
                trial_id="NCT00000001",
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
            )
            
            # Populate facts from manifest sections
            facts.identification.nct_id.value = "NCT00000001"
            facts.identification.trial_title.value = SAMPLE_CTGOV_DATA["study"]["brief_title"]
            facts.identification.phase.value = SAMPLE_CTGOV_DATA["study"]["phase"]
            facts.intervention.intervention_name.value = "Test Drug"
            facts.outcomes.primary_outcome.value = "Change in Primary Endpoint"
            
            # Step 3: Generate report
            markdown = render_consort(facts)
            
            assert "NCT00000001" in markdown or "Test Clinical Trial" in markdown
            assert len(markdown) > 200
            
            # Step 4: Save outputs
            manifest_path = Path(tmpdir) / "manifest.json"
            facts_path = Path(tmpdir) / "facts.json"
            report_path = Path(tmpdir) / "report.md"
            
            manifest_path.write_text(manifest.model_dump_json(indent=2))
            facts_path.write_text(facts.model_dump_json(indent=2))
            report_path.write_text(markdown)
            
            # Verify files created
            assert manifest_path.exists()
            assert facts_path.exists()
            assert report_path.exists()
