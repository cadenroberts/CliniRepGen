"""
Pipeline Orchestrator - Runs the complete CliniRepGen workflow.

Stages:
1. Ingest documents into Trial Manifest
2. Extract facts using FactFinder
3. Generate reports using Writer
4. Critique reports using Critic
5. Iterate until validation passes or max iterations reached
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from clinirepgen.manifest.models import TrialManifest
from clinirepgen.manifest.builder import ManifestBuilder
from clinirepgen.schemas.trial_facts import TrialFacts
from clinirepgen.agents.base import AgentConfig
from clinirepgen.agents.fact_finder import FactFinderAgent
from clinirepgen.agents.writer import WriterAgent, GeneratedReport
from clinirepgen.agents.critic import CriticAgent, CritiqueResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the pipeline."""
    
    # Trial identification
    trial_id: str
    trial_name: Optional[str] = None
    
    # Input/output
    input_dir: str = "."
    output_dir: str = "output"
    
    # Report settings
    report_types: List[str] = field(default_factory=lambda: ["consort", "ich_e3"])
    
    # Iteration settings
    max_iterations: int = 3
    min_score_to_pass: float = 70.0
    strict_validation: bool = False
    
    # Agent config
    agent_config: Optional[AgentConfig] = None
    
    # Processing options
    skip_extraction: bool = False  # Use existing TrialFacts
    skip_critique: bool = False    # Skip critique loop


@dataclass
class PipelineResult:
    """Result of a pipeline run."""
    
    trial_id: str
    manifest: TrialManifest
    trial_facts: TrialFacts
    reports: Dict[str, GeneratedReport]
    critiques: Dict[str, CritiqueResult]
    iterations: int
    passed_validation: bool
    output_files: List[str]
    run_timestamp: str
    duration_seconds: float


class Pipeline:
    """
    Main orchestrator for the CliniRepGen pipeline.
    
    Runs the complete workflow:
    Ingest -> Extract -> Write -> Critique -> (Iterate) -> Output
    """
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize the pipeline.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        
        # Set up output directory
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize state
        self.manifest: Optional[TrialManifest] = None
        self.trial_facts: Optional[TrialFacts] = None
        self.reports: Dict[str, GeneratedReport] = {}
        self.critiques: Dict[str, CritiqueResult] = {}
        
        # Initialize agents
        agent_config = config.agent_config or AgentConfig()
        self.fact_finder: Optional[FactFinderAgent] = None
        self.writer = WriterAgent(config=agent_config)
        self.critic = CriticAgent(config=agent_config)
        
        self.logger = logging.getLogger(__name__)
    
    def run(
        self,
        documents: Optional[List[str]] = None,
        ctgov_data: Optional[Dict[str, Any]] = None,
        existing_manifest: Optional[TrialManifest] = None,
        existing_facts: Optional[TrialFacts] = None,
    ) -> PipelineResult:
        """
        Run the complete pipeline.
        
        Args:
            documents: List of document paths to ingest
            ctgov_data: Optional ClinicalTrials.gov JSON data
            existing_manifest: Optional pre-built manifest
            existing_facts: Optional pre-extracted facts
            
        Returns:
            PipelineResult with all outputs
        """
        start_time = datetime.now()
        output_files = []
        
        self.logger.info(f"Starting pipeline for trial: {self.config.trial_id}")
        
        # Stage 1: Ingest
        if existing_manifest:
            self.manifest = existing_manifest
            self.logger.info("Using provided manifest")
        else:
            self.manifest = self._ingest(documents or [], ctgov_data)
            
            # Save manifest
            manifest_path = self.output_dir / f"{self.config.trial_id}_manifest.json"
            with open(manifest_path, "w") as f:
                f.write(self.manifest.model_dump_json(indent=2))
            output_files.append(str(manifest_path))
            self.logger.info(f"Saved manifest to {manifest_path}")
        
        # Stage 2: Extract facts
        if existing_facts:
            self.trial_facts = existing_facts
            self.logger.info("Using provided facts")
        elif not self.config.skip_extraction:
            self.trial_facts = self._extract()
            
            # Save facts
            facts_path = self.output_dir / f"{self.config.trial_id}_facts.json"
            with open(facts_path, "w") as f:
                f.write(self.trial_facts.model_dump_json(indent=2))
            output_files.append(str(facts_path))
            self.logger.info(f"Saved facts to {facts_path}")
        else:
            # Create empty facts
            self.trial_facts = TrialFacts(
                trial_id=self.config.trial_id,
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
            )
        
        # Stage 3-5: Generate, Critique, Iterate
        iteration = 0
        passed = False
        
        while iteration < self.config.max_iterations:
            iteration += 1
            self.logger.info(f"=== Iteration {iteration}/{self.config.max_iterations} ===")
            
            # Generate reports
            for report_type in self.config.report_types:
                self.reports[report_type] = self._generate(report_type)
                
                # Save report
                report_path = self.output_dir / f"{self.config.trial_id}_{report_type}_iter{iteration}.md"
                with open(report_path, "w") as f:
                    f.write(self.writer.to_markdown(self.reports[report_type]))
                output_files.append(str(report_path))
            
            # Skip critique if requested
            if self.config.skip_critique:
                passed = True
                break
            
            # Critique reports
            all_passed = True
            for report_type, report in self.reports.items():
                critique = self._critique(report)
                self.critiques[report_type] = critique
                
                # Save critique
                critique_path = self.output_dir / f"{self.config.trial_id}_{report_type}_critique_iter{iteration}.md"
                with open(critique_path, "w") as f:
                    f.write(self.critic.to_markdown(critique))
                output_files.append(str(critique_path))
                
                if not critique.passes_validation:
                    all_passed = False
                    self.logger.info(f"{report_type} critique: Score {critique.overall_score:.1f}, {len(critique.issues)} issues")
            
            if all_passed:
                passed = True
                self.logger.info("All reports passed validation!")
                break
            
            # Re-extract missing facts if not last iteration
            if iteration < self.config.max_iterations:
                self._reextract_missing()
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Final summary
        self.logger.info(f"Pipeline completed in {duration:.1f}s")
        self.logger.info(f"Iterations: {iteration}, Passed: {passed}")
        self.logger.info(f"Output files: {len(output_files)}")
        
        return PipelineResult(
            trial_id=self.config.trial_id,
            manifest=self.manifest,
            trial_facts=self.trial_facts,
            reports=self.reports,
            critiques=self.critiques,
            iterations=iteration,
            passed_validation=passed,
            output_files=output_files,
            run_timestamp=start_time.isoformat(),
            duration_seconds=duration,
        )
    
    def _ingest(
        self,
        documents: List[str],
        ctgov_data: Optional[Dict[str, Any]],
    ) -> TrialManifest:
        """Ingest documents into a Trial Manifest."""
        self.logger.info(f"Ingesting {len(documents)} documents")
        
        builder = ManifestBuilder(
            trial_id=self.config.trial_id,
            output_dir=str(self.output_dir),
        )
        
        # Add CT.gov data if provided
        if ctgov_data:
            builder.add_ctgov_data(ctgov_data)
        
        # Add documents
        for doc_path in documents:
            try:
                doc_id = builder.add_document(doc_path)
                
                # Parse document text (basic implementation)
                # In production, would use proper PDF/doc parsing
                if doc_path.endswith(".txt"):
                    with open(doc_path, "r") as f:
                        text = f.read()
                    builder.process_document_text(doc_id, text)
                elif doc_path.endswith(".json"):
                    with open(doc_path, "r") as f:
                        data = json.load(f)
                    # Treat JSON as structured data
                    text = json.dumps(data, indent=2)
                    builder.process_document_text(doc_id, text)
                    
            except Exception as e:
                self.logger.error(f"Failed to ingest {doc_path}: {e}")
        
        return builder.build()
    
    def _extract(self) -> TrialFacts:
        """Extract facts from the manifest."""
        self.logger.info("Extracting facts from manifest")
        
        self.fact_finder = FactFinderAgent(
            manifest=self.manifest,
            config=self.config.agent_config,
        )
        
        return self.fact_finder.run(checklist="both")
    
    def _generate(self, report_type: str) -> GeneratedReport:
        """Generate a report of the specified type."""
        self.logger.info(f"Generating {report_type} report")
        
        return self.writer.run(
            trial_facts=self.trial_facts,
            report_type=report_type,
        )
    
    def _critique(self, report: GeneratedReport) -> CritiqueResult:
        """Critique a generated report."""
        self.logger.info(f"Critiquing {report.report_type} report")
        
        return self.critic.run(
            report=report,
            trial_facts=self.trial_facts,
            strict=self.config.strict_validation,
        )
    
    def _reextract_missing(self) -> None:
        """Re-extract facts for missing checklist items."""
        if not self.fact_finder:
            return
        
        # Collect missing items from all critiques
        missing_paths = set()
        for critique in self.critiques.values():
            for query in critique.suggested_queries:
                # Convert query to fact path (simplified)
                missing_paths.add(query)
        
        if missing_paths:
            self.logger.info(f"Re-extracting {len(missing_paths)} missing items")
            
            # Run targeted extraction
            # In production, would do more sophisticated re-extraction
            updated_facts = self.fact_finder.run(
                checklist="both",
                fact_paths=list(missing_paths)[:10],  # Limit re-extraction
            )
            
            # Merge new facts
            for path, fact in updated_facts.get_all_fact_values():
                if fact.value is not None:
                    existing = self.trial_facts.get_fact_by_path(path)
                    if existing and existing.is_null:
                        existing.value = fact.value
                        existing.confidence = fact.confidence
                        for prov in fact.provenance.provenances:
                            existing.add_provenance(prov)


def run_pipeline(
    trial_id: str,
    documents: List[str],
    output_dir: str = "output",
    ctgov_data: Optional[Dict[str, Any]] = None,
    report_types: Optional[List[str]] = None,
    max_iterations: int = 3,
) -> PipelineResult:
    """
    Convenience function to run the full pipeline.
    
    Args:
        trial_id: Unique trial identifier
        documents: List of document paths
        output_dir: Output directory
        ctgov_data: Optional CT.gov JSON data
        report_types: Report types to generate (default: consort, ich_e3)
        max_iterations: Maximum critique iterations
        
    Returns:
        PipelineResult with all outputs
    """
    config = PipelineConfig(
        trial_id=trial_id,
        output_dir=output_dir,
        report_types=report_types or ["consort", "ich_e3"],
        max_iterations=max_iterations,
    )
    
    pipeline = Pipeline(config)
    
    return pipeline.run(
        documents=documents,
        ctgov_data=ctgov_data,
    )
