# CliniRepGen

**Clinical Report Generator** — A production-ready pipeline for generating regulatory-compliant clinical trial reports from structured and unstructured trial artifacts.

CliniRepGen ingests trial data (ClinicalTrials.gov exports, protocols, CSRs), extracts provenance-tracked facts aligned to **CONSORT 2025** and **ICH E3** guidelines, and generates narrative reports with full source traceability.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Configuration](#configuration)
- [Pipeline Stages](#pipeline-stages)
- [Data Schemas](#data-schemas)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

### Core Capabilities

- **Trial Manifest Index**: Pre-segments documents into sections and tables with deterministic IDs and semantic metadata
- **Provenance-Aware Fact Extraction**: Every extracted fact links back to exact source location (file, section, table cell, character offsets)
- **Checklist-Driven Extraction**: Treats each CONSORT/ICH E3 item as a separate extraction question
- **Dual Report Generation**: Produces both CONSORT narrative and ICH E3 CSR synopsis formats
- **Critic-Driven Validation**: Automated checking for missing items, unused facts, and unsupported claims
- **Iterative Refinement**: Critique loop drives targeted re-extraction until validation passes

### Technical Highlights

- **No Hallucination**: Facts only extracted from source documents; missing data logged as null
- **Deterministic IDs**: SHA-256 based IDs for reproducible manifest references
- **Typed Models**: Full Pydantic v2 schemas with validation
- **Extensible Architecture**: Modular agents, tools, and templates
- **Production CLI**: Full command-line interface with logging and error handling

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CliniRepGen Pipeline                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   INGEST     │───▶│   EXTRACT    │───▶│   GENERATE   │───▶│  CRITIQUE │ │
│  │              │    │              │    │              │    │           │ │
│  │ • CT.gov     │    │ • FactFinder │    │ • Writer     │    │ • Critic  │ │
│  │ • Protocols  │    │ • Tools      │    │ • Templates  │    │ • Loop    │ │
│  │ • CSRs       │    │ • LLM        │    │ • Renderer   │    │           │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘ │
│         │                   │                   │                   │       │
│         ▼                   ▼                   ▼                   ▼       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │ TrialManifest│    │  TrialFacts  │    │   Reports    │    │ Findings  │ │
│  │              │    │              │    │              │    │           │ │
│  │ • Documents  │    │ • Values     │    │ • CONSORT    │    │ • Missing │ │
│  │ • Sections   │    │ • Provenance │    │ • ICH E3     │    │ • Unused  │ │
│  │ • Tables     │    │ • Confidence │    │ • Markdown   │    │ • Claims  │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Package Structure

```
clinirepgen/
├── __init__.py              # Package exports
├── cli.py                   # Command-line interface (Typer)
├── config.py                # Configuration management
│
├── schemas/                 # Pydantic data models
│   ├── provenance.py        # Source tracking (file, section, offsets)
│   ├── trial_facts.py       # FactValue, TrialFacts, ChecklistItem
│   ├── consort.py           # CONSORT 2025 checklist (30+ items)
│   └── ich_e3.py            # ICH E3 checklist (50+ items)
│
├── manifest/                # Trial Manifest system
│   ├── models.py            # Document, Section, Table, TrialManifest
│   ├── builder.py           # ManifestBuilder for ingestion
│   └── section_splitter.py  # Document segmentation
│
├── tools/                   # Agent tools for manifest access
│   ├── manifest_tools.py    # ManifestTools class
│   ├── search.py            # search_sections(), search_tables()
│   └── access.py            # open_section(), get_table_cell()
│
├── agents/                  # LLM-powered agents
│   ├── base.py              # BaseAgent with OpenAI client
│   ├── fact_finder.py       # Extracts facts from manifest
│   ├── writer.py            # Generates narrative reports
│   └── critic.py            # Validates reports against facts
│
├── pipeline/                # Orchestration
│   ├── orchestrator.py      # Full pipeline with critique loop
│   ├── ingest.py            # IngestStage
│   ├── extract.py           # ExtractStage
│   └── generate.py          # GenerateStage
│
└── reports/                 # Report generation
    ├── templates.py         # CONSORT and ICH E3 templates
    └── renderer.py          # Markdown rendering
```

---

## Installation

### Prerequisites

- Python 3.10+
- pip or uv package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/CliniRepGen.git
cd CliniRepGen

# Create virtual environment and install
make setup

# Or manually:
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Run tests
make test

# Check CLI
clinirepgen --help
```

---

## Quick Start

### 1. Run the Demo (No API Key Required)

```bash
clinirepgen demo
```

This creates a sample manifest from demo CT.gov data, demonstrating the ingestion pipeline without LLM calls.

**Output:**
```
🎯 Running CliniRepGen demo
   Created sample data: demo_output/demo_ctgov.json
   Created manifest: demo_output/demo_manifest.json
   Documents: 1
   Sections: 4
   Tables: 1
✅ Demo complete!
```

### 2. Ingest Your Own Trial Data

```bash
# Ingest CT.gov JSON + documents into a manifest
clinirepgen ingest \
  --trial NCT12345678 \
  --ctgov path/to/ctgov_export.json \
  --input path/to/documents/ \
  --out output/manifest.json
```

### 3. Run Full Pipeline (Requires API Key)

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Or use OpenRouter
export API_KEY="sk-or-..."
export API_BASE="https://openrouter.ai/api/v1"
export MODEL_NAME="anthropic/claude-sonnet-4"

# Run the full extraction → generation → critique pipeline
clinirepgen run \
  --trial NCT12345678 \
  --ctgov data/trial.json \
  --input data/documents/ \
  --out output/
```

---

## CLI Reference

### Global Options

```bash
clinirepgen [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version |

### Commands

#### `demo`

Run a demonstration of the pipeline without requiring an API key.

```bash
clinirepgen demo
```

Creates sample data in `demo_output/` directory.

---

#### `ingest`

Build a Trial Manifest from source documents.

```bash
clinirepgen ingest [OPTIONS]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--trial, -t` | Yes | Trial identifier (e.g., NCT number) |
| `--input, -i` | No | Directory containing trial documents |
| `--ctgov, -c` | No | Path to ClinicalTrials.gov JSON export |
| `--out, -o` | Yes | Output path for manifest JSON |

**Example:**
```bash
clinirepgen ingest \
  --trial NCT00000001 \
  --ctgov data/ctgov.json \
  --input data/protocols/ \
  --out output/manifest.json
```

**Supported Document Types:**
- `.txt` - Plain text (protocols, reports)
- `.json` - Structured data (CT.gov exports)
- `.md` - Markdown documents

---

#### `extract`

Extract facts from a manifest into a TrialFacts JSON.

```bash
clinirepgen extract [OPTIONS]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--trial, -t` | Yes | Trial identifier |
| `--manifest, -m` | Yes | Path to manifest JSON |
| `--out, -o` | Yes | Output path for facts JSON |
| `--checklist` | No | Checklist to use: `consort`, `ich_e3`, or `all` (default: `all`) |

**Example:**
```bash
clinirepgen extract \
  --trial NCT00000001 \
  --manifest output/manifest.json \
  --out output/facts.json \
  --checklist consort
```

---

#### `generate`

Generate reports from extracted facts.

```bash
clinirepgen generate [OPTIONS]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--trial, -t` | Yes | Trial identifier |
| `--facts, -f` | Yes | Path to facts JSON |
| `--out, -o` | Yes | Output directory for reports |
| `--format` | No | Report format: `consort`, `ich_e3`, or `all` (default: `all`) |

**Example:**
```bash
clinirepgen generate \
  --trial NCT00000001 \
  --facts output/facts.json \
  --out output/reports/ \
  --format all
```

---

#### `run`

Execute the full pipeline: ingest → extract → generate → critique.

```bash
clinirepgen run [OPTIONS]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--trial, -t` | Yes | Trial identifier |
| `--input, -i` | No | Directory containing trial documents (default: `.`) |
| `--ctgov, -c` | No | Path to ClinicalTrials.gov JSON export |
| `--out, -o` | Yes | Output directory for all artifacts |
| `--max-iterations` | No | Max critique loop iterations (default: 3) |

**Example:**
```bash
clinirepgen run \
  --trial NCT00000001 \
  --ctgov data/trial.json \
  --input data/ \
  --out output/ \
  --max-iterations 5
```

**Output Structure:**
```
output/
├── manifest.json          # Trial Manifest
├── facts.json             # Extracted TrialFacts
├── consort_report.md      # CONSORT narrative
├── ich_e3_synopsis.md     # ICH E3 synopsis
└── critique.json          # Final critique findings
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (or compatible) |
| `API_KEY` | - | Alternative API key variable |
| `API_BASE` | `https://api.openai.com/v1` | API base URL |
| `MODEL_NAME` | `gpt-4o` | Model to use for extraction/generation |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_TOKENS` | `4096` | Max tokens per LLM response |
| `TEMPERATURE` | `0.1` | LLM temperature (lower = more deterministic) |

### Configuration File

Create `clinirepgen.yaml` in your working directory:

```yaml
# clinirepgen.yaml
api:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o"
  max_tokens: 4096
  temperature: 0.1

pipeline:
  max_iterations: 3
  checklist: "all"  # consort, ich_e3, or all

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## Pipeline Stages

### Stage 1: Ingest

**Purpose:** Build a searchable Trial Manifest from raw documents.

**Process:**
1. Parse ClinicalTrials.gov JSON export (study metadata, interventions, outcomes, adverse events)
2. Scan input directory for documents (.txt, .json, .md)
3. Split documents into sections using heading detection
4. Extract tables from structured content
5. Generate deterministic IDs for all entities
6. Build cross-reference indices (doc→sections, section→tables)

**Output:** `TrialManifest` with:
- `documents`: Dict of `DocumentMetadata`
- `sections`: Dict of `Section` with content and tags
- `tables`: Dict of `Table` with cell data

---

### Stage 2: Extract

**Purpose:** Populate TrialFacts by querying the manifest for each checklist item.

**Process:**
1. Load CONSORT and/or ICH E3 checklists
2. For each checklist item:
   - Generate search query from item description
   - Search sections and tables for relevant content
   - Use LLM to extract specific fact value
   - Record provenance (source location)
   - Assign confidence level (high/medium/low/null)
3. Handle conflicts by noting in `FactValue.notes`

**Tools Available to FactFinder:**
- `search_sections(query, filters)` - Semantic search over sections
- `search_tables(query, filters)` - Search table captions and content
- `open_section(section_id)` - Retrieve full section content
- `get_table_cell(table_id, row, col)` - Access specific cell

---

### Stage 3: Generate

**Purpose:** Create narrative reports from extracted facts.

**Process:**
1. Load report template (CONSORT or ICH E3)
2. For each template section:
   - Gather relevant facts from TrialFacts
   - Use LLM to generate narrative prose
   - Inject inline citations to provenance
3. Render final markdown document

**Templates:**
- **CONSORT Narrative**: Title/Abstract, Introduction, Methods, Results, Discussion
- **ICH E3 Synopsis**: Comprehensive summary per ICH E3 Section 2

---

### Stage 4: Critique

**Purpose:** Validate generated reports and identify gaps.

**Checks Performed:**
1. **Missing Checklist Items**: Facts with null confidence
2. **Low Confidence Facts**: Facts needing verification
3. **Unused Facts**: Extracted but not mentioned in narrative
4. **Unsupported Claims**: Narrative statements without provenance

**Output:** Critique findings with suggestions for targeted re-extraction.

---

### Critique Loop

The orchestrator iterates through extract→generate→critique until:
- All critical checks pass, OR
- Max iterations reached

Each iteration focuses on resolving the highest-priority issues from the previous critique.

---

## Data Schemas

### Provenance

Tracks the exact source of any extracted information.

```python
class Provenance(BaseModel):
    file_id: str              # Document ID
    file_name: str            # Original filename
    section_id: Optional[str] # Section within document
    section_title: Optional[str]
    table_id: Optional[str]   # Table if from tabular data
    row_index: Optional[int]  # Table row
    col_index: Optional[int]  # Table column
    char_start: Optional[int] # Character offset start
    char_end: Optional[int]   # Character offset end
    page_num: Optional[int]   # Page number if available
    
    @property
    def provenance_id(self) -> str:
        """Deterministic SHA-256 based ID"""
```

### FactValue

A single extracted fact with full metadata.

```python
class FactValue(BaseModel):
    value: Optional[Any]           # The extracted value
    provenance: List[Provenance]   # Source locations
    confidence: FactConfidence     # high/medium/low/null
    notes: Optional[str]           # Conflict notes
    extracted_at: datetime
```

### TrialFacts

Complete collection of facts for a trial.

```python
class TrialFacts(BaseModel):
    trial_id: str
    facts: Dict[str, FactValue]  # Keyed by checklist item ID
    
    def get_fact(self, item_id: str) -> Optional[FactValue]
    def set_fact(self, item_id: str, value: FactValue)
    def get_null_facts() -> List[str]
    def get_coverage_stats() -> Dict[str, int]
```

### ChecklistItem

A single item from CONSORT or ICH E3.

```python
class ChecklistItem(BaseModel):
    item_id: str        # e.g., "1a", "12.3.2"
    description: str    # Full requirement text
    category: str       # Category/section
    source: str         # "CONSORT" or "ICH_E3"
    required: bool      # Whether mandatory
```

### TrialManifest

Central index of all trial artifacts.

```python
class TrialManifest(BaseModel):
    manifest_id: str
    trial_id: str
    created_at: datetime
    documents: Dict[str, DocumentMetadata]
    sections: Dict[str, Section]
    tables: Dict[str, Table]
    
    def get_stats() -> Dict[str, int]
    def search_sections(query: str) -> List[SearchResult]
    def search_tables(query: str) -> List[SearchResult]
```

---

## API Reference

### Python API

```python
from clinirepgen import (
    # Manifest
    ManifestBuilder,
    TrialManifest,
    Section,
    Table,
    
    # Schemas
    TrialFacts,
    FactValue,
    Provenance,
    CONSORT_CHECKLIST,
    ICH_E3_CHECKLIST,
    
    # Tools
    ManifestTools,
    search_sections,
    search_tables,
    open_section,
    get_table_cell,
    
    # Agents
    FactFinder,
    Writer,
    Critic,
    
    # Pipeline
    Orchestrator,
    IngestStage,
    ExtractStage,
    GenerateStage,
    
    # Reports
    ReportTemplate,
    MarkdownRenderer,
)
```

### Building a Manifest Programmatically

```python
from clinirepgen import ManifestBuilder

# Initialize builder
builder = ManifestBuilder(trial_id="NCT00000001")

# Add ClinicalTrials.gov data
builder.add_ctgov_data("path/to/ctgov.json")

# Add documents
builder.add_document("path/to/protocol.txt", doc_type="protocol")
builder.add_document("path/to/csr.txt", doc_type="csr")

# Build and save
manifest = builder.build()
builder.save_manifest("output/manifest.json")

print(f"Created manifest with {len(manifest.sections)} sections")
```

### Searching the Manifest

```python
from clinirepgen import ManifestTools, TrialManifest

# Load manifest
manifest = TrialManifest.model_validate_json(open("manifest.json").read())

# Initialize tools
tools = ManifestTools(manifest)

# Search for content
results = tools.search_sections("primary endpoint", limit=5)
for result in results:
    print(f"Found in {result.section_id}: {result.content_preview[:100]}...")

# Access specific section
section = tools.open_section(results[0].section_id)
print(section.content)

# Search tables
table_results = tools.search_tables("adverse events")
for result in table_results:
    table = tools.get_table(result.table_id)
    print(f"Table: {table.caption}, {table.num_rows} rows")
```

### Running the Full Pipeline

```python
from clinirepgen import Orchestrator
import os

# Configure API
os.environ["OPENAI_API_KEY"] = "sk-..."

# Initialize orchestrator
orchestrator = Orchestrator(
    trial_id="NCT00000001",
    model_name="gpt-4o"
)

# Run pipeline
result = orchestrator.run(
    ctgov_path="data/ctgov.json",
    document_paths=["data/protocol.txt", "data/csr.txt"],
    output_dir="output/",
    max_iterations=3
)

# Check results
print(f"Status: {result['status']}")
print(f"Facts extracted: {result['fact_stats']['populated']}/{result['fact_stats']['total']}")
print(f"Missing items: {len(result['critique']['missing_items'])}")
```

---

## Testing

### Run All Tests

```bash
make test
```

### Run with Coverage

```bash
make test-cov
```

### Run Specific Test File

```bash
pytest tests/test_manifest.py -v
```

### Test Structure

```
tests/
├── test_schemas.py       # Provenance, FactValue, TrialFacts, Checklists
├── test_manifest.py      # Document, Section, Table, ManifestBuilder
├── test_tools.py         # ManifestTools, search, access functions
└── test_integration.py   # End-to-end pipeline tests
```

---

## Examples

### Example 1: Process a ClinicalTrials.gov Export

```bash
# Download trial data (example using AACT)
# Or export from ClinicalTrials.gov directly

# Create manifest
clinirepgen ingest \
  --trial NCT02793856 \
  --ctgov NCT02793856_ctgov.json \
  --out manifest.json

# Extract facts
clinirepgen extract \
  --trial NCT02793856 \
  --manifest manifest.json \
  --out facts.json

# Generate reports
clinirepgen generate \
  --trial NCT02793856 \
  --facts facts.json \
  --out reports/
```

### Example 2: Custom Checklist Subset

```python
from clinirepgen import (
    ManifestBuilder, 
    TrialFacts, 
    FactFinder,
    ChecklistItem,
    ChecklistCategory
)

# Define custom checklist
custom_items = [
    ChecklistItem(
        item_id="custom_1",
        description="Primary efficacy endpoint definition",
        category=ChecklistCategory.OUTCOMES,
        source="CUSTOM",
        required=True
    ),
    ChecklistItem(
        item_id="custom_2", 
        description="Sample size calculation assumptions",
        category=ChecklistCategory.SAMPLE_SIZE,
        source="CUSTOM",
        required=True
    ),
]

# Build manifest
builder = ManifestBuilder("NCT00000001")
builder.add_document("protocol.txt", doc_type="protocol")
manifest = builder.build()

# Extract with custom checklist
facts = TrialFacts(trial_id="NCT00000001", checklist_items=custom_items)
finder = FactFinder(manifest=manifest, llm_client=client)
facts = finder.run(facts, custom_items)

# Check coverage
for item_id, fact in facts.facts.items():
    status = "✓" if fact.value else "✗"
    print(f"{status} {item_id}: {fact.value or 'NOT FOUND'}")
```

### Example 3: Inspect Provenance

```python
from clinirepgen import TrialFacts

# Load facts
facts = TrialFacts.model_validate_json(open("facts.json").read())

# Find a specific fact
fact = facts.get_fact("14")  # CONSORT item 14: Outcomes

if fact and fact.value:
    print(f"Value: {fact.value}")
    print(f"Confidence: {fact.confidence.level}")
    
    for prov in fact.provenance:
        print(f"\nSource: {prov.to_citation()}")
        print(f"  File: {prov.file_name}")
        print(f"  Section: {prov.section_title}")
        if prov.char_start and prov.char_end:
            print(f"  Chars: {prov.char_start}-{prov.char_end}")
```

---

## Troubleshooting

### Common Issues

#### "API key not set"

```
❌ Pipeline failed: The api_key client option must be set
```

**Solution:** Set your API key:
```bash
export OPENAI_API_KEY="sk-..."
# Or
export API_KEY="sk-..."
```

#### "No sections found in document"

The section splitter may not detect headings in your document format.

**Solution:** Check that your document has recognizable headings:
- Numbered headings: `1. Introduction`, `1.1 Background`
- Uppercase headings: `METHODS`, `RESULTS`

#### "Low coverage on extraction"

Many facts showing as null/low confidence.

**Solutions:**
1. Ensure source documents contain the required information
2. Add more documents to the manifest
3. Increase `max_iterations` for more extraction attempts
4. Check that document content is being parsed correctly

#### Import Errors

```
ModuleNotFoundError: No module named 'clinirepgen'
```

**Solution:** Install in development mode:
```bash
pip install -e .
```

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
clinirepgen run --trial NCT00000001 ...
```

### Getting Help

1. Check the [Issues](https://github.com/your-org/CliniRepGen/issues) page
2. Run `clinirepgen --help` for CLI documentation
3. Review test files for usage examples

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Citation

If you use CliniRepGen in your research, please cite:

```bibtex
@software{clinirepgen2026,
  title = {CliniRepGen: Clinical Report Generator},
  year = {2026},
  url = {https://github.com/your-org/CliniRepGen}
}
```

---

## Acknowledgments

- CONSORT 2025 guidelines for randomized trial reporting
- ICH E3 guidelines for clinical study report structure
- OpenAI for language model APIs
