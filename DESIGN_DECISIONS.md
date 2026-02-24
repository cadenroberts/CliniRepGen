# Design Decisions

Architecture Decision Records documenting key design choices in CliniRepGen.

## ADR-001: SHA-256 IDs for All Entities

**Date:** 2024-01 (inferred from codebase)  
**Status:** Accepted  

### Context

Trial manifests must reference documents, sections, and tables. References must be stable across pipeline runs to enable reproducible provenance and audit trails. Options:
1. Sequential integers (doc_1, sec_1, etc.)
2. UUIDs (random or timestamp-based)
3. Content-based hashes (SHA-256)

### Decision

Use SHA-256 hashes of normalized entity content as deterministic IDs. Format: `{type}_{hash_prefix}` (e.g., `sec_a3f2b1c8`).

### Consequences

**Positive:**
- Identical content → identical ID across runs
- No central ID registry required
- Collisions astronomically unlikely (SHA-256 space)
- Audit trail: ID change implies content change

**Negative:**
- Hashing overhead (~10ms per entity)
- IDs not human-readable (cannot infer meaning from ID)
- Content normalization required (whitespace, encoding) to ensure determinism

**Mitigations:**
- Normalize content before hashing (strip leading/trailing whitespace, UTF-8 encoding)
- Include human-readable metadata alongside ID (e.g., section title)

### Implementation

See `manifest/builder.py`:
```python
def _compute_section_id(self, text: str, title: str) -> str:
    content = f"{title}|||{text}".encode('utf-8')
    hash_digest = hashlib.sha256(content).hexdigest()
    return f"sec_{hash_digest[:16]}"
```

---

## ADR-002: Checklist-Driven Extraction

**Date:** 2024-01  
**Status:** Accepted  

### Context

Two approaches to fact extraction:
1. **Bulk summarization**: Ask LLM to summarize entire document
2. **Checklist-driven**: For each checklist item, ask targeted question

Bulk summarization is faster (fewer LLM calls) but prone to hallucination and missing data.

### Decision

Extract facts one checklist item at a time. Each item becomes a specific query (e.g., "How was sample size determined?"). LLM searches manifest and returns fact or null.

### Consequences

**Positive:**
- Prevents hallucination: LLM cannot fabricate facts for missing data
- Missing data = explicit null, not silently omitted
- Granular provenance: each fact has precise source
- Parallelizable: items independent

**Negative:**
- More LLM calls (25 CONSORT items vs 1 bulk call)
- Higher latency (serial: ~50s vs bulk: ~5s)
- Higher cost (~$0.50 per trial vs ~$0.05)

**Mitigations:**
- Parallelize extraction (not yet implemented; P2)
- Cache extracted facts for identical inputs (not yet implemented; P2)

### Implementation

See `agents/fact_finder.py`:
```python
for item in checklist:
    query = item.description
    sections = self.tools.search_sections(query)
    fact = self._extract_fact_from_sections(item, sections)
    facts.add(item.item_id, fact)
```

---

## ADR-003: Pydantic v2 Schemas Throughout

**Date:** 2024-02  
**Status:** Accepted  

### Context

Data validation options:
1. No validation (plain dicts)
2. Runtime assertions (manual checks)
3. Pydantic v2 schemas (declarative validation)

Plain dicts are flexible but error-prone. Manual checks are verbose and incomplete.

### Decision

Use Pydantic v2 `BaseModel` for all data structures: `TrialManifest`, `TrialFacts`, `GeneratedReport`, `CritiqueResult`, etc.

### Consequences

**Positive:**
- Invalid data fails immediately at boundary (not deep in pipeline)
- Type hints enable static analysis (mypy)
- JSON serialization/deserialization automatic
- Schema serves as documentation

**Negative:**
- Rigid: schema changes break compatibility
- Overhead: validation adds ~5% runtime
- Learning curve: Pydantic patterns (Field, validators, model_validator)

**Mitigations:**
- Version schemas explicitly (e.g., `TrialFactsV1`)
- Add migration helpers for schema upgrades

### Implementation

Example from `schemas/trial_facts.py`:
```python
class FactValue(BaseModel):
    value: Optional[Any] = Field(default=None)
    provenance: ProvenanceList = Field(default_factory=ProvenanceList)
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.UNVERIFIED)
    notes: Optional[str] = None
```

---

## ADR-004: Separate Agent Roles

**Date:** 2024-02  
**Status:** Accepted  

### Context

Pipeline architecture options:
1. **Monolithic**: Single script with ingest, extract, generate, critique functions
2. **Agent-based**: Separate agents for FactFinder, Writer, Critic

Monolithic is simpler but harder to test and iterate. Agent-based has more code but better separation of concerns.

### Decision

Implement four agent classes:
- `ManifestBuilder`: Ingest documents → TrialManifest
- `FactFinderAgent`: Extract facts → TrialFacts
- `WriterAgent`: Generate reports → GeneratedReport
- `CriticAgent`: Validate reports → CritiqueResult

Each agent is independently testable and swappable.

### Consequences

**Positive:**
- Clear boundaries: each agent has single responsibility
- Independent testing: mock LLM for unit tests
- Iterative refinement: replace FactFinder without touching Writer
- Failure isolation: Writer crash does not affect Critic

**Negative:**
- More code: 4 classes vs 1 script
- More files: 4 modules vs 1
- Interface overhead: agents communicate via schemas

**Mitigations:**
- Shared `BaseAgent` reduces boilerplate (LLM client, logging, retry logic)
- Schemas enforce contracts (agent changes break at boundaries, not runtime)

### Implementation

See `agents/` directory. Each agent inherits from `BaseAgent` and implements `run(**kwargs) -> Output`.

---

## ADR-005: Iterative Critique Loop

**Date:** 2024-02  
**Status:** Accepted  

### Context

Report generation strategies:
1. **Single-shot**: Extract → Generate → Done
2. **Iterative**: Extract → Generate → Critique → [Re-extract if failed] → repeat

Single-shot is fast but often incomplete (missing facts, unsupported claims). Iterative is slower but converges on coverage thresholds.

### Decision

Implement critique loop with max iterations (default: 3). After each generation, critique validates coverage and suggests re-extraction queries. Orchestrator re-extracts missing facts and regenerates report until pass or budget exhausted.

### Consequences

**Positive:**
- Higher coverage: missing items identified and re-extracted
- Self-correcting: unsupported claims flagged and removed
- Convergence: scores improve each iteration (typically)

**Negative:**
- Higher compute cost: 3x LLM calls vs single-shot
- Higher latency: ~150s vs ~50s
- Risk of infinite loop if critique always fails

**Mitigations:**
- Max iterations cap prevents infinite loop
- Suggested queries guide re-extraction (not blind retry)
- Early exit if validation passes (no wasted iterations)

### Implementation

See `pipeline/orchestrator.py`:
```python
for iteration in range(max_iterations):
    report = writer.run(facts)
    critique = critic.run(report, facts)
    if critique.passes_validation:
        break
    facts = reextract_missing(critique.suggested_queries)
```

---

## ADR-006: Provenance at Fact Granularity

**Date:** 2024-01  
**Status:** Accepted  

### Context

Provenance tracking levels:
1. **Document-level**: Fact → file name
2. **Section-level**: Fact → file + section
3. **Span-level**: Fact → file + section + character offsets

Document-level is insufficient for validation. Span-level is most precise but adds overhead.

### Decision

Track provenance at section/table cell level with optional text span. Every `FactValue` includes:
- File name
- Section ID or table ID
- Text span (exact quote) for sections
- Row/col coordinates for tables
- Page number (if available)

### Consequences

**Positive:**
- Enables citation: report can link back to source
- Enables validation: critique can verify claim against provenance
- Audit trail: every fact traceable to origin
- Regulatory compliance: provenance required for FDA submissions

**Negative:**
- Storage overhead: provenance ~100 bytes per fact
- Extraction complexity: LLM must return structured provenance
- Parsing risk: text span may not exactly match source (whitespace, encoding)

**Mitigations:**
- Provenance optional for null facts (no source to cite)
- Store both ID (stable) and human-readable metadata (title, file name)
- Normalize text spans before comparison

### Implementation

See `schemas/provenance.py`:
```python
class Provenance(BaseModel):
    file_name: str
    section_id: Optional[str] = None
    table_id: Optional[str] = None
    text_span: Optional[str] = None
    row_num: Optional[int] = None
    col_num: Optional[int] = None
    page_num: Optional[int] = None
```

---

## ADR-007: Markdown as Primary Report Format

**Date:** 2024-03  
**Status:** Accepted  

### Context

Report output format options:
1. **JSON**: Machine-readable, structured, but not human-friendly
2. **HTML**: Rich formatting, but requires rendering
3. **Markdown**: Plain text, human-readable, version-controllable
4. **PDF**: Polished, but not editable

Regulatory workflows require human review and editing before submission.

### Decision

Generate reports as Markdown with inline citations. Format:
```markdown
## Methods
The study enrolled 200 patients [consort.sample_size] across 50 sites [consort.sites]...
```

### Consequences

**Positive:**
- Human-readable: reviewers can read/edit in any text editor
- Version-controllable: diff-friendly, can track changes via Git
- Extensible: convert to HTML/PDF via pandoc
- Citation format clear: `[fact_path]` links to TrialFacts

**Negative:**
- Limited formatting: no tables, figures, complex layouts
- Not submission-ready: requires conversion to PDF for FDA
- Citation syntax custom: not standard academic format (e.g., not BibTeX)

**Mitigations:**
- Provide conversion scripts (Markdown → HTML → PDF) in future
- Document citation format in README
- Export TrialFacts as JSON for programmatic access

### Implementation

See `reports/renderer.py`:
```python
def render_section(section: ReportSection) -> str:
    content = section.content
    for citation in section.citations:
        content = content.replace(f"[{citation}]", f"[{citation}]")
    return f"## {section.title}\n\n{content}\n\n"
```

---

## ADR-008: Deterministic Pipeline Defaults

**Date:** 2026-02-24
**Status:** Accepted

### Context

Reproducible outputs are required for auditability and regression testing. Non-determinism sources include LLM randomness (`temperature`), timestamp-based IDs, and filesystem iteration order.

### Decision

Set conservative, deterministic defaults and compute IDs from content rather than timestamps:

- Default `temperature` = `0.0` (deterministic LLM sampling)
- Compute `manifest_id` from sorted document file hashes (SHA-256)
- Sort and deduplicate file lists during ingest to avoid filesystem ordering differences

### Consequences

**Positive:**
- Identical inputs produce identical manifests and (with the same model version) extracted facts.
- Easier regression testing and CI comparisons.

**Negative:**
- May reduce helpful variability for creative tasks (can be adjusted via `CLINIREPGEN_TEMPERATURE`).

### Implementation

See `clinirepgen/config.py` (default temperature), `clinirepgen/manifest/builder.py` (manifest hash), and `clinirepgen/pipeline/ingest.py` (file list sorting and path validation).

---

## Summary Table

| ADR | Decision | Key Tradeoff | Status |
|-----|----------|--------------|--------|
| 001 | SHA-256 IDs | Hashing cost vs reproducibility | Accepted |
| 002 | Checklist-driven extraction | More LLM calls vs no hallucination | Accepted |
| 003 | Pydantic v2 schemas | Rigidity vs type safety | Accepted |
| 004 | Separate agent roles | More code vs modularity | Accepted |
| 005 | Iterative critique loop | Higher cost vs coverage | Accepted |
| 006 | Provenance at fact level | Storage overhead vs audit trail | Accepted |
| 007 | Markdown output | Limited formatting vs editability | Accepted |

## Future Decisions

**Under Consideration:**
- ADR-008: Parallel extraction (trade latency for complexity)
- ADR-009: Vector embeddings for semantic search (trade accuracy for dependencies)
- ADR-010: Local LLM support (trade quality for privacy)
