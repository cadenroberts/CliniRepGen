# CliniRepGen

Automated generation of regulatory-compliant clinical trial reports from source documents with deterministic provenance tracking.

## Summary

CliniRepGen transforms heterogeneous clinical trial source materials (ClinicalTrials.gov JSON, protocols, CSRs, PDF documents) into CONSORT 2025 and ICH E3 compliant reports. The system builds a deterministic manifest with SHA-256 stable IDs, extracts checklist-driven facts with full provenance, generates narrative reports via LLM agents, and iteratively validates completeness through automated critique.

## What it does

- Ingests trial documents and constructs a deterministic Trial Manifest with SHA-256-stable section and table IDs
- Extracts structured facts for each CONSORT and ICH E3 checklist item with full provenance (file, section, table cell, character offsets)
- Generates narrative reports using LLM agents constrained by templates and extracted facts
- Validates reports via critique agent that flags missing items, unused facts, and unsupported claims
- Iterates extraction and generation until validation passes or iteration budget exhausted
- Exports Markdown reports with inline provenance citations

## Architecture

### Component Diagram

```
Input Documents → ManifestBuilder → TrialManifest (SHA-256 IDs)
                                          ↓
                                   FactFinderAgent (LLM + search tools)
                                          ↓
                                    TrialFacts (provenance-backed)
                                          ↓
                                    WriterAgent (LLM + templates)
                                          ↓
                                   GeneratedReport (CONSORT/ICH E3)
                                          ↓
                                    CriticAgent (validation)
                                          ↓
                            [Pass: Save] or [Fail: Re-extract → iterate]
```

### Execution Flow

1. **Ingest Stage** (`manifest/builder.py`)
   - Reads documents (PDF, TXT, JSON, DOCX)
   - Splits into sections using heuristic section headers
   - Extracts tables using pdfplumber/python-docx
   - Assigns SHA-256 IDs to all entities (documents, sections, tables, cells)
   - Outputs `TrialManifest` JSON

2. **Extract Stage** (`agents/fact_finder.py`)
   - For each checklist item (CONSORT/ICH E3), formulates a targeted query
   - Uses semantic search over manifest sections/tables
   - Calls LLM with search results to extract fact value
   - Records provenance: file name, section ID, table coordinates, text span
   - Populates `TrialFacts` with `FactValue` objects (value, confidence, provenance)

3. **Generate Stage** (`agents/writer.py`)
   - Groups facts by checklist category (e.g., Methods, Results)
   - For each category, generates narrative text via LLM with template guidance
   - Inserts inline citations linking back to fact provenance
   - Assembles sections into complete `GeneratedReport`

4. **Critique Stage** (`agents/critic.py`)
   - Validates checklist coverage (% of required items populated)
   - Checks for unused facts (extracted but not cited in report)
   - Flags unsupported claims (report statements without provenance)
   - Returns `CritiqueResult` with pass/fail and suggested re-extraction queries

5. **Iteration Loop** (`pipeline/orchestrator.py`)
   - If critique fails and iterations remain, re-extract missing facts
   - Regenerate report with updated facts
   - Re-critique until pass or max iterations reached

### Contracts Between Components

- **ManifestBuilder → FactFinderAgent**: Stable SHA-256 IDs ensure reproducible references
- **FactFinderAgent → WriterAgent**: Every `FactValue` includes provenance; Writer must cite it
- **WriterAgent → CriticAgent**: Report sections reference checklist items; Critic validates coverage
- **CriticAgent → Orchestrator**: Critique result includes re-extraction suggestions; Orchestrator decides iteration

### Failure Modes

- **Ingest failure**: Missing files, unsupported formats, malformed CT.gov JSON → explicit error, pipeline halts
- **Extraction failure**: LLM timeout, API error → retries 3x with exponential backoff, then fails stage
- **Generation failure**: Template rendering error, LLM refusal → logged, returns partial report
- **Critique failure**: Coverage below threshold after max iterations → saves final report with validation=False

### Observability

- Structured logging at each stage (namespace: `clinirepgen.<module>`)
- Provenance chain: every fact traces back to source document, section, and offset
- Metrics tracked: checklist coverage %, LLM token usage, iteration count, elapsed time
- Output artifacts: manifest JSON, facts JSON, reports (Markdown), critiques (Markdown)

## Design Tradeoffs

| Decision | Tradeoff | Rationale |
|----------|----------|-----------|
| SHA-256 IDs for all entities | Hashing overhead on ingest | Reproducible references across runs; audit trail integrity |
| Checklist-driven extraction | More LLM calls than bulk summarization | Prevents hallucination; missing data = null, not fabricated |
| Pydantic v2 schemas throughout | Rigid contracts vs flexible dicts | Invalid data fails fast; type safety at all boundaries |
| Separate agent roles | More code than monolithic script | Enables independent testing, iteration, and failure isolation |
| Iterative critique loop | Higher compute cost per run | Converges on coverage thresholds; single-shot often incomplete |
| Provenance at fact granularity | Storage overhead | Enables citation, audit, and validation; required for regulatory trust |

## Repository Layout

```
clinirepgen/
├── schemas/
│   ├── provenance.py       # Provenance tracking models
│   ├── trial_facts.py      # TrialFacts and FactValue schemas
│   ├── consort.py          # CONSORT 2025 checklist
│   └── ich_e3.py           # ICH E3 checklist
├── manifest/
│   ├── models.py           # TrialManifest, Section, Table models
│   ├── builder.py          # ManifestBuilder implementation
│   └── section_splitter.py # Heuristic section detection
├── tools/
│   ├── manifest_tools.py   # Search and access utilities for agents
│   ├── search.py           # Semantic search over sections/tables
│   └── access.py           # Typed accessors for manifest entities
├── agents/
│   ├── base.py             # BaseAgent with LLM client and retry logic
│   ├── fact_finder.py      # FactFinderAgent (extraction)
│   ├── writer.py           # WriterAgent (narrative generation)
│   └── critic.py           # CriticAgent (validation)
├── pipeline/
│   ├── orchestrator.py     # Pipeline and iteration logic
│   ├── ingest.py           # IngestStage wrapper
│   ├── extract.py          # ExtractStage wrapper
│   └── generate.py         # GenerateStage wrapper
├── reports/
│   ├── templates.py        # Report section templates
│   └── renderer.py         # Markdown rendering utilities
├── cli.py                  # Click CLI entry point
└── config.py               # Configuration and environment handling

sample_data/
└── demo_protocol.txt       # Sample protocol for demo mode

scripts/
└── demo.sh                 # Non-interactive demo script (Phase 4)

.github/workflows/
└── ci.yml                  # CI workflow (Phase 5)
```

## Evaluation

Correctness is defined by:

1. **Checklist coverage**: % of CONSORT/ICH E3 required items populated with high/medium confidence
2. **Provenance fidelity**: Every fact value traces to exact source location; no hallucinated facts
3. **Citation completeness**: Every claim in generated report backed by inline citation
4. **Reproducibility**: Identical inputs produce identical manifests and facts (SHA-256 stability)

### Commands

```bash
# Run demo (no LLM, manifest-only)
make run-demo

# Run full pipeline (requires API_KEY)
clinirepgen run \
  --trial NCT00000001 \
  --input sample_data/ \
  --out output/

# Validate outputs
ls output/  # Check for manifest, facts, reports, critiques
grep "Coverage:" output/*_critique*.md  # Check coverage %

# Reproducibility test (run twice, compare SHA-256s)
clinirepgen ingest --trial NCT00000001 --input sample_data/ --out manifest1.json
clinirepgen ingest --trial NCT00000001 --input sample_data/ --out manifest2.json
diff <(jq -S . manifest1.json) <(jq -S . manifest2.json)  # Should be identical
```

### Pass Criteria

- Coverage ≥ 70% for required checklist items
- Zero unsupported claims in final report
- Zero unused high-confidence facts
- Manifest SHA-256 IDs stable across identical inputs

## Demo

See [DEMO.md](DEMO.md) for full demo instructions.

**Quickstart (no API key required):**

```bash
make run-demo
# Outputs: demo_output/demo_manifest.json
```

**Full pipeline (requires OpenAI API key):**

```bash
export API_KEY="sk-..."
clinirepgen run \
  --trial NCT00000001 \
  --input sample_data/ \
  --ctgov sample_data/demo_trial.json \
  --out output/
```

## Installation

### Prerequisites

- Python ≥ 3.10
- OpenAI API key (for LLM stages; demo mode does not require this)

### Install

```bash
# Install package
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"

# Verify
clinirepgen --version
```

### Configuration

Set environment variables:

```bash
export API_KEY="sk-..."                     # Required for LLM stages
export CLINIREPGEN_MODEL="gpt-4o"          # Optional, default: gpt-4o
export CLINIREPGEN_MAX_ITERATIONS="3"      # Optional, default: 3
export CLINIREPGEN_OUTPUT_DIR="output"     # Optional, default: output
```

Or create `config.yaml`:

```yaml
llm:
  model: gpt-4o
  temperature: 0.3
  max_tokens: 4096

pipeline:
  max_iterations: 3
  min_score_to_pass: 70.0

output:
  output_dir: output
  save_intermediate: true
```

## Limitations

- **Document parsing**: Basic heuristics for section splitting; complex tables or nested structures may be misinterpreted
- **Semantic search**: No vector embeddings; uses keyword matching; may miss relevant sections with different terminology
- **LLM nondeterminism**: Default `temperature=0.3` introduces variability; set to `0.0` for deterministic extraction
- **No ground truth validation**: Critique validates internal consistency (coverage, citations) but not factual correctness against source documents
- **Single trial scope**: Pipeline designed for one trial at a time; no batch processing or cross-trial analysis
- **English only**: No multi-language support

## License

Apache License 2.0 — see [LICENSE](LICENSE).
