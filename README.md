# CliniRepGen

Production-grade clinical trial report generation system with deterministic provenance enforcement and iterative validation.

## What it does

- **Ingestion**: Constructs a deterministic Trial Manifest by segmenting CT.gov exports, protocols, and CSRs into sections and tables with SHA-256-stable IDs and rich metadata.
- **Provenance-aware extraction**: For each CONSORT 2025 and ICH-E3 checklist item, extracts structured facts with full source provenance (file, section, table cell, character offsets). Every value traces back to its origin.
- **Narrative generation**: Produces both CONSORT narratives and ICH-E3 CSR synopses using LLMs under strict guidance, assembling extracted facts into coherent sections with inline citations.
- **Critique and refinement**: Validates generated reports for missing items, unused facts, and unsupported claims; iterates extraction and generation until critical checks pass or the iteration budget is exhausted.
- **CLI & Python API**: Typed Pydantic interface and ergonomic CLI for ingestion, extraction, generation, and pipeline orchestration.

## Architecture

CliniRepGen treats report generation as a deterministic pipeline with four stages:

```
 INGEST          EXTRACT          GENERATE         CRITIQUE
┌──────────┐   ┌──────────┐    ┌──────────┐    ┌──────────┐
│ CT.gov   │──▶│FactFinder│──▶ │ Writer   │──▶ │ Critic   │
│ Protocols│   │ Tools    │    │ Templates│    │ Loop     │
│ CSRs     │   │ LLM      │    │ Renderer │    │          │
└──────────┘   └──────────┘    └──────────┘    └──────────┘
      │              │               │               │
      ▼              ▼               ▼               ▼
 TrialManifest  TrialFacts      Reports         Findings
 • Documents    • Values        • CONSORT       • Missing
 • Sections     • Provenance    • ICH E3        • Unused
 • Tables       • Confidence    • Markdown      • Claims
```

- **Ingest** reads CT.gov JSON and trial documents, splits them into sections/tables, assigns SHA-256 IDs, and persists a searchable `TrialManifest`.
- **Extract** uses semantic search and targeted prompts to fill a `TrialFacts` object for each checklist item, recording provenance and confidence.
- **Generate** composes narrative reports from facts using templated prompts and inserts citations.
- **Critique** compares reports against facts, flags gaps and unsupported claims. The orchestrator loops through extraction and generation until validation succeeds or the iteration budget is reached.

## Key design decisions

| Decision | Tradeoff | Rationale |
|----------|----------|-----------|
| Deterministic SHA-256 IDs for all entities | Extra hashing cost per ingestion | Guarantees reproducible manifest references and audit trails across runs |
| Checklist-driven extraction (one question per item) | More LLM calls than open-ended summarization | Prevents hallucination; missing data logged as null instead of fabricated |
| Typed Pydantic v2 schemas throughout | Rigid contracts vs flexible dicts | Invalid data fails fast; schema correctness enforced at every boundary |
| Separate agents (Ingest, FactFinder, Writer, Critic) | More code surface than monolithic pipeline | Enables targeted iteration, independent testing, and clear failure isolation |
| Iterative critique loop | Higher compute cost per run | Reports converge on checklist coverage thresholds instead of single-shot generation |

## Evaluation

| Metric | Definition |
|--------|------------|
| Coverage | % of checklist items populated at high/medium confidence vs missing |
| Fidelity | Fraction of narrative statements backed by provenance; count of unsupported claims |
| Iteration cost | LLM calls and tokens per extraction/generation cycle |
| Reproducibility | Identical inputs produce identical manifests, facts, and reports across runs |

Run evaluation: `make test`

## Production considerations

- **Determinism**: SHA-256 IDs and gating ensure reproducible outputs. All prompts and templates are versioned.
- **Observability**: Structured per-stage logging and provenance output allow tracing from final report back to raw source documents.
- **Failure modes**: Missing documents or malformed CT.gov exports cause explicit ingest failures. API errors propagate as typed exceptions. The orchestrator respects a maximum iteration budget.
- **Cost & latency**: Tune `max_tokens`, `temperature`, and checklist subsets to balance coverage and compute cost. Independent checklist items can be parallelized.

## Quickstart

```bash
# Ingest trial documents into a manifest
clinirepgen ingest \
  --trial NCT00000001 \
  --ctgov data/ctgov.json \
  --input data/docs \
  --out manifest.json

# Extract facts
clinirepgen extract \
  --trial NCT00000001 \
  --manifest manifest.json \
  --out facts.json \
  --checklist all

# Generate reports
clinirepgen generate \
  --trial NCT00000001 \
  --facts facts.json \
  --out reports/ \
  --format all

# Full pipeline with critique loop
clinirepgen run \
  --trial NCT00000001 \
  --ctgov data/ctgov.json \
  --input data/docs \
  --out reports/ \
  --max-iterations 3
```

## Repo map

```
clinirepgen/
├── schemas/       Pydantic models: provenance, facts, manifests, checklists
├── manifest/      Manifest builder and section splitter
├── tools/         Manifest search and access utilities for agents
├── agents/        LLM-powered agents (FactFinder, Writer, Critic)
├── pipeline/      Orchestrator and stage implementations
├── reports/       Report templates and renderers
├── cli.py         Typer CLI
└── config.py      Configuration management
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).
