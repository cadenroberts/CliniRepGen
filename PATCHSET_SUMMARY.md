# PATCHSET_SUMMARY

## BASELINE SNAPSHOT

**Branch:** main  
**HEAD Commit:** 8b38ad4a1b9275538011f0b875d2e594db7f06bc  
**Tracked Files:** 0 (repository not tracking files in git index yet)  
**Date:** 2026-02-10

### Primary Entry Points
- CLI: `clinirepgen.cli:main` (installed as `clinirepgen` command)
- Python API: `clinirepgen.pipeline.orchestrator.Pipeline`

### How the Project Currently Runs

**Demo (no LLM required):**
```bash
make run-demo
# OR
python -m clinirepgen.cli demo
```

**Full Pipeline (requires OpenAI API key):**
```bash
clinirepgen run \
  --trial NCT00000001 \
  --ctgov sample_data/demo_trial.json \
  --input sample_data/ \
  --out output/
```

**Individual Stages:**
```bash
# 1. Ingest
clinirepgen ingest --trial NCT00000001 --input sample_data/ --out manifest.json

# 2. Extract
clinirepgen extract --manifest manifest.json --out facts.json

# 3. Generate
clinirepgen generate --facts facts.json --type consort --out report.md
```

**Testing:**
```bash
make test        # Run all tests
make test-cov    # Run with coverage
```

### Current State
Repository appears to be functional Python package with:
- Modular pipeline architecture (ingest → extract → generate → critique)
- Pydantic v2 schemas for data validation
- Click-based CLI
- Makefile for common operations
- Sample data for demo
- No test suite visible yet
- Documentation present but will be rebuilt per workflow requirements

---

## COMMITS MADE

_(Will be updated after each phase)_

---

## VERIFICATION

**Command:** `./scripts/demo.sh`

**Output (smoke test, no API key):**
```
=== CliniRepGen Demo Script ===
Demo directory: /var/folders/.../tmp.JaCq8iKj4V
Python version: 3.13.9
clinirepgen is installed
API_KEY not set - running smoke test only (ingest stage)

=== Stage 1: Ingest ===
Manifest created: demo_output/demo_manifest.json
  Trial ID: NCT00000001
  Documents: 1
  Sections: 4
Manifest structure is valid

=== Smoke Test Complete ===
SMOKE_OK
```

**Result:** Smoke test passes. Ingest stage functional, manifest deterministic.

**Limitation:** Full demo (extract/generate/critique stages) requires OpenAI API key and would cost ~$1-3 per run. Smoke test validates core functionality (manifest building, SHA-256 IDs) without LLM dependency.

---

## REMAINING WORK

_(Will be updated in Phase 6)_
