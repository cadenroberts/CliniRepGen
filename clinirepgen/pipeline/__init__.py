"""
Pipeline module - Orchestration of the full CliniRepGen workflow.

Main pipeline stages:
1. Ingest: Build Trial Manifest from source documents
2. Extract: Run FactFinder to populate TrialFacts
3. Write: Generate reports from facts
4. Critique: Validate reports and identify issues
5. Iterate: Re-extract and rewrite until validation passes
"""

from clinirepgen.pipeline.extract import ExtractStage
from clinirepgen.pipeline.generate import GenerateStage
from clinirepgen.pipeline.ingest import IngestStage
from clinirepgen.pipeline.orchestrator import Pipeline, PipelineConfig

__all__ = [
    "Pipeline",
    "PipelineConfig",
    "IngestStage",
    "ExtractStage",
    "GenerateStage",
]
