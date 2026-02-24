# REPO_AUDIT

## 1. Purpose

CliniRepGen automates the generation of regulatory-compliant clinical trial reports (CONSORT 2025, ICH E3) from source documents. It ingests heterogeneous trial artifacts (ClinicalTrials.gov JSON, protocols, CSRs, PDFs), builds a deterministic manifest with SHA-256 stable IDs, extracts facts with full provenance, generates narrative reports, and iteratively validates completeness via critique agents.

## 2. Entry Points

### Primary Entry Points

**CLI:** `clinirepgen` command (installed via `pyproject.toml` scripts)
- Implemented in: `clinirepgen/cli.py`
- Commands: `run`, `ingest`, `extract`, `generate`, `demo`, `info`

**Python API:** `clinirepgen.pipeline.orchestrator.Pipeline`
- Programmatic access to full pipeline
- Convenience function: `run_pipeline()`

**Demo Mode:** No LLM required
```bash
make run-demo
# OR
python -m clinirepgen.cli demo
```

### Pipeline Stages

1. **Ingest:** Build Trial Manifest from documents
2. **Extract:** Extract facts using FactFinder agent (LLM + semantic search)
3. **Generate:** Compose reports using Writer agent
4. **Critique:** Validate reports using Critic agent
5. **Iterate:** Re-extract missing facts until validation passes or max iterations reached

## 3. Dependency Surface

### Runtime Dependencies (Core)
- `pydantic>=2.0` - Schema validation
- `openai>=1.0` - LLM client
- `click>=8.0` - CLI framework
- `pdfplumber>=0.10` - PDF parsing
- `python-docx>=1.0` - DOCX parsing
- `tabulate>=0.9` - Table formatting
- `PyYAML>=6.0` - Config file support
- `tqdm>=4.0` - Progress bars

### Runtime Dependencies (Heavy)
Current `requirements.txt` includes 189 packages (vllm, torch, transformers, etc.). Most appear unused by the codebase. **Issue:** Dependency bloat. Only core dependencies above are actually imported.

### Development Dependencies
- `pytest>=7.0`, `pytest-cov>=4.0`
- `black>=23.0`, `ruff>=0.1`, `mypy>=1.0`

### Missing Lockfile
No `requirements.lock`, `poetry.lock`, or `Pipfile.lock`. Determinism risk for deployment.

## 4. Configuration Surface

### Environment Variables
Defined in `clinirepgen/config.py`:

**LLM:**
- `CLINIREPGEN_MODEL` (default: `gpt-4o`)
- `API_KEY` (required for LLM stages)
- `API_BASE` (default: OpenAI endpoint)
- `CLINIREPGEN_TEMPERATURE`

**Pipeline:**
- `CLINIREPGEN_MAX_ITERATIONS`
- `CLINIREPGEN_STRICT`
- `CLINIREPGEN_OUTPUT_DIR`

### Config Files
Supports `config.yaml`, `config.yml`, `config.json`, `clinirepgen.yaml` in working directory. Optional.

### CLI Arguments
All parameters overridable via CLI flags (`--model`, `--iterations`, `--out`, etc.)

## 5. Data Flow

```
Documents (PDF/TXT/JSON) 
  ↓
ManifestBuilder → TrialManifest (SHA-256 IDs, sections, tables)
  ↓
FactFinderAgent (LLM + semantic search) → TrialFacts (provenance-backed)
  ↓
WriterAgent (LLM + templates) → GeneratedReport (CONSORT/ICH E3)
  ↓
CriticAgent (validation) → CritiqueResult
  ↓
(Iterate if validation fails)
  ↓
Final reports + critiques saved to output/
```

High-level: Deterministic SHA-256 IDs assigned to all document entities (documents, sections, tables). Facts extracted per checklist item with full provenance (file, section, table cell, character offsets). Reports assembled from facts with inline citations. Critique validates coverage, fidelity, and flags unsupported claims.

## 6. Determinism Risks

### High Risk
- **LLM calls:** `temperature=0.0` by default. Model responses are deterministic when temperature is zero.
- **No seed control:** No random seed or LLM seed parameter exposed.
- **Dependency versions:** No lockfile means different library versions across environments.

### Medium Risk
- **Timestamp in manifest_id:** `manifest_builder.py:73` embeds `datetime.now()` in manifest ID, making builds non-reproducible.
- **File iteration order:** Ingesting directories may depend on filesystem order.

### Low Risk
- **SHA-256 hashing:** Deterministic IDs for entities (good).

- Set `temperature=0.0` for deterministic mode (already default in config)
- Add LLM seed parameter
- Add lockfile (requirements.lock or Poetry)
- Make manifest_id deterministic (hash-based, not timestamp-based)

## 7. Observability

### Logging
- Python `logging` module used throughout
- Log level configurable via CLI (`--verbose`)
- Per-agent and per-stage logging (namespace: `clinirepgen.*`)

### Provenance Tracking
Strong: Every `FactValue` stores full provenance chain (file, section, table, character offsets). Reports can trace back to source documents.

### Metrics
- Iteration count
- Coverage % (populated facts / total checklist items)
- Validation pass/fail
- LLM token usage tracked per call
- Duration logged for full pipeline

### Error Handling
- Typed exceptions via Pydantic validation
- LLM client has retry logic (3 attempts, exponential backoff)
- Document ingest failures logged but do not halt pipeline

### Visibility Gaps
- No structured event log (only text logs)
- No cost tracking aggregation (tokens logged per call but not summed)
- No timing breakdown per stage

## 8. Test State

**No test suite found.** 
- `pyproject.toml` references `testpaths = ["tests"]` but no `tests/` directory exists
- Makefile includes test targets but they will fail
- Zero test coverage

**Test Plan Required:**
- Unit tests for schemas (Pydantic validation)
- Unit tests for manifest builder (section splitting, SHA-256 stability)
- Integration tests for pipeline stages (using mock LLM)
- End-to-end smoke test with sample data

## 9. Reproducibility

### Good
- SHA-256 stable IDs for all entities
- Pydantic schemas enforce contracts
- Sample data provided (`sample_data/demo_protocol.txt`)
- Demo mode works without API key

### Needs Improvement
- No lockfile (install determinism not guaranteed)
- LLM temperature > 0 (nondeterministic by default)
- No CI/CD workflow yet
- Manifest ID embeds timestamp (non-reproducible)

### Full Reproducibility Requirements
1. Add `requirements.lock` or migrate to Poetry
2. Set `temperature=0.0` or expose seed parameter
3. Make manifest_id deterministic (hash-based)
4. Add CI workflow (`make test`, `make run-demo`)
5. Pin model versions explicitly (e.g., `gpt-4o-2024-08-06`)

## 10. Security Surface

### Secrets
- `API_KEY` required for LLM stages
- Currently read from environment (good)
- No secret leakage detected in logs

### External API Calls
- OpenAI API (or compatible endpoint via `API_BASE`)
- Network dependency: pipeline fails if API unavailable

### File Access
- Reads arbitrary files from `--input` directory
- No sandbox or path traversal validation
- Writes to `--out` directory (user-controlled)

**Security Risks:**
- Path traversal: User-supplied paths not validated
- Arbitrary file read: `--input` accepts any directory
- LLM prompt injection: User documents directly embedded in prompts

**Mitigations Needed:**
- Validate input paths (no `..`, restrict to workspace)
- Sanitize document text before embedding in prompts
- Add rate limiting for LLM calls (cost control)

## 11. Ranked Improvement List

### P0 (Critical for Production)
1. **Add test suite** (zero coverage currently)
2. **Add lockfile** (requirements.lock or Poetry)
3. **Add CI workflow** (test + demo on push)
4. **Set temperature=0.0** for deterministic mode
5. **Validate input paths** (security: prevent path traversal)

### P1 (High Priority)
6. **Make manifest_id deterministic** (hash-based, not timestamp)
7. **Trim dependencies** (remove unused vllm, torch, etc. from requirements.txt)
8. **Add cost tracking** (aggregate token usage across run)
9. **Add smoke test** using `scripts/demo.sh` (Phase 4)
10. **Document API key setup** (README quickstart missing this)

### P2 (Nice to Have)
11. **Add structured event log** (JSON lines for observability)
12. **Add LLM seed parameter** (full determinism)
13. **Add parallel extraction** (checklist items independent)
14. **Add caching** (avoid re-extracting identical inputs)
15. **Add HTML report output** (currently only Markdown)

---

**Assessment Date:** 2026-02-10  
**Auditor:** /repo workflow  
**Scope:** Full codebase (< 500 tracked files, comprehensive audit)
