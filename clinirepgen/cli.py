"""
CliniRepGen CLI - Command line interface for running the pipeline.

Usage:
    clinirepgen run --trial NCT12345678 --input ./trial_data --out ./output
    clinirepgen ingest --trial NCT12345678 --input ./documents
    clinirepgen extract --manifest manifest.json --out facts.json
    clinirepgen generate --facts facts.json --type consort --out report.md
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List

import click

from clinirepgen.pipeline.orchestrator import Pipeline, PipelineConfig, run_pipeline
from clinirepgen.pipeline.ingest import IngestStage
from clinirepgen.pipeline.extract import ExtractStage
from clinirepgen.pipeline.generate import GenerateStage
from clinirepgen.manifest.models import TrialManifest
from clinirepgen.schemas.trial_facts import TrialFacts
from clinirepgen.agents.base import AgentConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """CliniRepGen - Clinical Trial Report Generator
    
    Generate CONSORT and ICH E3 compliant reports from trial documents.
    """
    pass


@cli.command()
@click.option('--trial', '-t', required=True, help='Trial ID (e.g., NCT12345678)')
@click.option('--input', '-i', 'input_dir', default='.', help='Input directory with trial documents')
@click.option('--out', '-o', 'output_dir', default='output', help='Output directory')
@click.option('--ctgov', '-c', default=None, help='Path to ClinicalTrials.gov JSON export')
@click.option('--types', '-T', default='consort,ich_e3', help='Report types (comma-separated)')
@click.option('--iterations', '-n', default=3, help='Max critique iterations')
@click.option('--model', '-m', default=None, help='LLM model to use')
@click.option('--skip-extract', is_flag=True, help='Skip extraction (use existing facts)')
@click.option('--skip-critique', is_flag=True, help='Skip critique loop')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(trial, input_dir, output_dir, ctgov, types, iterations, model, 
        skip_extract, skip_critique, verbose):
    """Run the full CliniRepGen pipeline.
    
    Example:
        clinirepgen run --trial NCT12345678 --input ./data --out ./output
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    click.echo(f"Starting CliniRepGen pipeline for {trial}")
    click.echo(f"   Input: {input_dir}")
    click.echo(f"   Output: {output_dir}")
    
    # Find documents
    documents = []
    input_path = Path(input_dir)
    if input_path.exists():
        for ext in ['.pdf', '.txt', '.json', '.docx', '.md']:
            documents.extend(input_path.glob(f"*{ext}"))
    
    click.echo(f"   Found {len(documents)} documents")
    
    # Load CT.gov data if provided
    ctgov_data = None
    if ctgov and Path(ctgov).exists():
        with open(ctgov) as f:
            ctgov_data = json.load(f)
        click.echo(f"   Loaded CT.gov data from {ctgov}")
    
    # Set up agent config
    agent_config = AgentConfig()
    if model:
        agent_config.model = model
    
    # Set up pipeline config
    config = PipelineConfig(
        trial_id=trial,
        input_dir=input_dir,
        output_dir=output_dir,
        report_types=types.split(','),
        max_iterations=iterations,
        agent_config=agent_config,
        skip_extraction=skip_extract,
        skip_critique=skip_critique,
    )
    
    # Run pipeline
    try:
        pipeline = Pipeline(config)
        result = pipeline.run(
            documents=[str(d) for d in documents],
            ctgov_data=ctgov_data,
        )
        
        click.echo("")
        click.echo("Pipeline completed!")
        click.echo(f"   Iterations: {result.iterations}")
        click.echo(f"   Validation: {'PASSED' if result.passed_validation else 'FAILED'}")
        click.echo(f"   Duration: {result.duration_seconds:.1f}s")
        click.echo(f"   Output files: {len(result.output_files)}")
        
        for f in result.output_files[:5]:
            click.echo(f"   - {f}")
        if len(result.output_files) > 5:
            click.echo(f"   ... and {len(result.output_files) - 5} more")
            
    except Exception as e:
        click.echo(f"Pipeline failed: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--trial', '-t', required=True, help='Trial ID')
@click.option('--input', '-i', 'input_dir', required=True, help='Input directory')
@click.option('--out', '-o', 'output_path', default=None, help='Output manifest path')
@click.option('--ctgov', '-c', default=None, help='CT.gov JSON file')
def ingest(trial, input_dir, output_path, ctgov):
    """Ingest documents into a Trial Manifest.
    
    Example:
        clinirepgen ingest --trial NCT12345678 --input ./docs --out manifest.json
    """
    click.echo(f"Ingesting documents for {trial}")
    
    stage = IngestStage(trial_id=trial, output_dir=os.path.dirname(output_path or "."))
    
    # Ingest CT.gov data
    if ctgov and Path(ctgov).exists():
        with open(ctgov) as f:
            data = json.load(f)
        stage.ingest_ctgov(data)
        click.echo(f"   Added CT.gov data")
    
    # Ingest directory
    manifest = stage.ingest_directory(input_dir)
    
    # Save manifest
    if output_path is None:
        output_path = f"{trial}_manifest.json"
    
    with open(output_path, "w") as f:
        f.write(manifest.model_dump_json(indent=2))
    
    click.echo(f"Manifest created: {output_path}")
    click.echo(f"   Documents: {len(manifest.documents)}")
    click.echo(f"   Sections: {len(manifest.sections)}")
    click.echo(f"   Tables: {len(manifest.tables)}")


@cli.command()
@click.option('--manifest', '-m', required=True, help='Path to manifest JSON')
@click.option('--out', '-o', 'output_path', default=None, help='Output facts JSON path')
@click.option('--checklist', '-c', default='both', help='Checklist to use (consort, ich_e3, both)')
@click.option('--model', default=None, help='LLM model to use')
def extract(manifest, output_path, checklist, model):
    """Extract facts from a Trial Manifest.
    
    Example:
        clinirepgen extract --manifest manifest.json --out facts.json
    """
    click.echo(f"Extracting facts from {manifest}")
    
    # Load manifest
    with open(manifest) as f:
        manifest_data = json.load(f)
    manifest_obj = TrialManifest(**manifest_data)
    
    # Set up config
    agent_config = AgentConfig()
    if model:
        agent_config.model = model
    
    # Run extraction
    stage = ExtractStage(manifest=manifest_obj, config=agent_config)
    facts = stage.extract(checklist=checklist)
    
    # Save facts
    if output_path is None:
        output_path = f"{manifest_obj.trial_id}_facts.json"
    
    with open(output_path, "w") as f:
        f.write(facts.model_dump_json(indent=2))
    
    # Get coverage
    coverage = stage.get_coverage_summary(facts)
    
    click.echo(f"Facts extracted: {output_path}")
    click.echo(f"   Total facts: {coverage['total_facts']}")
    click.echo(f"   Populated: {coverage['populated']}")
    click.echo(f"   Coverage: {coverage['coverage_pct']:.1f}%")


@cli.command()
@click.option('--facts', '-f', required=True, help='Path to facts JSON')
@click.option('--type', '-t', 'report_type', default='consort', help='Report type (consort or ich_e3)')
@click.option('--out', '-o', 'output_path', default=None, help='Output file path')
@click.option('--critique/--no-critique', default=True, help='Run critique')
@click.option('--model', default=None, help='LLM model to use')
def generate(facts, report_type, output_path, critique, model):
    """Generate a report from extracted facts.
    
    Example:
        clinirepgen generate --facts facts.json --type consort --out report.md
    """
    click.echo(f"Generating {report_type} report from {facts}")
    
    # Load facts
    with open(facts) as f:
        facts_data = json.load(f)
    facts_obj = TrialFacts(**facts_data)
    
    # Set up config
    agent_config = AgentConfig()
    if model:
        agent_config.model = model
    
    # Generate
    stage = GenerateStage(config=agent_config)
    
    if critique:
        report, critique_result, iterations = stage.generate_with_critique(
            facts_obj, report_type
        )
        click.echo(f"   Iterations: {iterations}")
        click.echo(f"   Validation: {'PASSED' if critique_result.passes_validation else 'FAILED'}")
    else:
        report = stage.generate(facts_obj, report_type)
    
    # Save report
    if output_path is None:
        output_path = f"{facts_obj.trial_id}_{report_type}_report.md"
    
    saved_path = stage.save_report(report, output_path.replace('.md', ''))
    
    click.echo(f"Report generated: {saved_path}")
    click.echo(f"   Word count: {report.total_word_count}")


@cli.command()
def demo():
    """Run a demo with sample data.
    
    Creates sample trial data and runs the full pipeline.
    """
    click.echo("Running CliniRepGen demo")
    
    demo_dir = Path("demo_output")
    demo_dir.mkdir(exist_ok=True)
    
    # Create sample data
    sample_data = {
        "study": {
            "nct_id": "NCT00000001",
            "brief_title": "Demo Randomized Controlled Trial of Treatment A vs Placebo",
            "official_title": "A Phase 3, Randomized, Double-Blind, Placebo-Controlled Study of Treatment A in Patients with Condition X",
            "phase": "Phase 3",
            "study_type": "Interventional",
            "enrollment": 200,
            "start_date": "2023-01-15",
            "completion_date": "2024-06-30",
            "overall_status": "Completed"
        },
        "interventions": [
            {
                "intervention_type": "Drug",
                "name": "Treatment A",
                "description": "10mg oral tablet once daily for 12 weeks"
            },
            {
                "intervention_type": "Drug",
                "name": "Placebo",
                "description": "Matching placebo tablet once daily for 12 weeks"
            }
        ],
        "outcomes": [
            {
                "outcome_type": "Primary",
                "title": "Change in Disease Score from Baseline",
                "time_frame": "Week 12",
                "description": "Mean change in validated disease score"
            }
        ],
        "adverse_events": [
            {
                "event_type": "Other",
                "organ_system": "Gastrointestinal disorders",
                "adverse_event_term": "Nausea",
                "subjects_affected": 15,
                "subjects_at_risk": 100
            }
        ]
    }
    
    # Save sample data
    sample_path = demo_dir / "demo_ctgov.json"
    with open(sample_path, "w") as f:
        json.dump(sample_data, f, indent=2)
    
    click.echo(f"   Created sample data: {sample_path}")
    
    # Run ingestion only (skip LLM-dependent steps for demo)
    stage = IngestStage(trial_id="NCT00000001", output_dir=str(demo_dir))
    stage.ingest_ctgov(sample_data)
    manifest = stage.build()
    
    manifest_path = demo_dir / "demo_manifest.json"
    with open(manifest_path, "w") as f:
        f.write(manifest.model_dump_json(indent=2))
    
    click.echo(f"   Created manifest: {manifest_path}")
    click.echo(f"   Documents: {len(manifest.documents)}")
    click.echo(f"   Sections: {len(manifest.sections)}")
    click.echo(f"   Tables: {len(manifest.tables)}")
    
    click.echo("")
    click.echo("Demo complete!")
    click.echo("")
    click.echo("To run full pipeline with LLM extraction, set API_KEY and run:")
    click.echo(f"  clinirepgen run --trial NCT00000001 --ctgov {sample_path} --out {demo_dir}")


@cli.command()
@click.option('--manifest', '-m', help='Path to manifest to inspect')
@click.option('--facts', '-f', help='Path to facts to inspect')
def info(manifest, facts):
    """Display information about a manifest or facts file."""
    
    if manifest:
        click.echo(f"Manifest: {manifest}")
        with open(manifest) as f:
            data = json.load(f)
        manifest_obj = TrialManifest(**data)
        
        click.echo(f"   Trial ID: {manifest_obj.trial_id}")
        click.echo(f"   Created: {manifest_obj.created_at}")
        click.echo(f"   Documents: {len(manifest_obj.documents)}")
        click.echo(f"   Sections: {len(manifest_obj.sections)}")
        click.echo(f"   Tables: {len(manifest_obj.tables)}")
        
        click.echo("\n   Documents:")
        for doc in manifest_obj.documents.values():
            click.echo(f"   - {doc.file_name} ({doc.doc_type})")
    
    if facts:
        click.echo(f"Facts: {facts}")
        with open(facts) as f:
            data = json.load(f)
        facts_obj = TrialFacts(**data)
        
        all_facts = facts_obj.get_all_fact_values()
        populated = sum(1 for _, f in all_facts if f.value is not None)
        
        click.echo(f"   Trial ID: {facts_obj.trial_id}")
        click.echo(f"   Last Updated: {facts_obj.last_updated}")
        click.echo(f"   Total Facts: {len(all_facts)}")
        click.echo(f"   Populated: {populated} ({populated/len(all_facts)*100:.1f}%)")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
