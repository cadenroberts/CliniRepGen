# Demo

## Prerequisites

- Python ≥ 3.10
- CliniRepGen installed (`pip install -e .`)
- For full pipeline: OpenAI API key

## Quick Demo (No API Key Required)

The simplest demo runs **ingest-only** mode, which builds a Trial Manifest from sample data without LLM calls.

```bash
# Run demo
make run-demo

# Or explicitly:
python -m clinirepgen.cli demo
```

### Expected Output

```
Running CliniRepGen demo
   Created sample data: demo_output/demo_ctgov.json
   Created manifest: demo_output/demo_manifest.json
   Documents: 1
   Sections: 8
   Tables: 3

Demo complete!

To run full pipeline with LLM extraction, set API_KEY and run:
  clinirepgen run --trial NCT00000001 --ctgov demo_output/demo_ctgov.json --out demo_output
```

### Inspect Outputs

```bash
# View manifest structure
jq . demo_output/demo_manifest.json | head -50

# List sections
jq '.sections | keys' demo_output/demo_manifest.json

# View a section
jq '.sections["sec_..."]' demo_output/demo_manifest.json

# List tables
jq '.tables | keys' demo_output/demo_manifest.json
```

### What This Tests

- Document ingestion (CT.gov JSON parsing)
- Manifest building (deterministic IDs)
- Section/table extraction

**Limitations:** No LLM stages (extract, generate, critique), so no facts or reports.

---

## Full Pipeline Demo (Requires API Key)

### Setup

```bash
# Set API key
export API_KEY="sk-..."

# Verify
echo $API_KEY | head -c 10  # Should print "sk-proj-..." or similar
```

### Run Pipeline

```bash
clinirepgen run \
  --trial NCT00000001 \
  --input sample_data/ \
  --out output/ \
  --types consort \
  --iterations 3 \
  --verbose
```

### Expected Output

```
Starting CliniRepGen pipeline for NCT00000001
   Input: sample_data/
   Output: output/
   Found 1 documents
   
=== Stage 1: Ingest ===
Ingesting 1 documents
Saved manifest to output/NCT00000001_manifest.json
   Documents: 1
   Sections: 8
   Tables: 3

=== Stage 2: Extract ===
Extracting facts from manifest
Extracting CONSORT items: 25
...
Saved facts to output/NCT00000001_facts.json
   Coverage: 72.0%
   Populated: 18 / 25

=== Iteration 1/3 ===
Generating consort report
Critiquing consort report
   Score: 68.5, 4 issues
   Missing items: [7b, 12a, 15, 21]

=== Iteration 2/3 ===
Re-extracting 4 missing items
Generating consort report
Critiquing consort report
   Score: 76.0, 1 issue
   Missing items: [21]

=== Iteration 3/3 ===
Re-extracting 1 missing item
Generating consort report
Critiquing consort report
   Score: 80.0, 0 issues

All reports passed validation!

Pipeline completed in 142.3s
Iterations: 3, Passed: True
Output files: 8
   - output/NCT00000001_manifest.json
   - output/NCT00000001_facts.json
   - output/NCT00000001_consort_iter1.md
   - output/NCT00000001_consort_critique_iter1.md
   - output/NCT00000001_consort_iter2.md
   - output/NCT00000001_consort_critique_iter2.md
   - output/NCT00000001_consort_iter3.md
   - output/NCT00000001_consort_critique_iter3.md
```

### Inspect Outputs

#### Manifest
```bash
jq '.trial_id, .documents | length, .sections | length' output/NCT00000001_manifest.json
```

#### Facts
```bash
# Coverage summary
jq '.checklist_coverage' output/NCT00000001_facts.json

# Sample fact
jq '.consort_facts.sample_size' output/NCT00000001_facts.json
```

**Example:**
```json
{
  "value": "A sample size of 200 patients (100 per arm) was determined...",
  "confidence": "high",
  "provenance": {
    "file_name": "demo_protocol.txt",
    "section_id": "sec_a3f2b1c8",
    "section_title": "Statistical Analysis",
    "text_span": "A sample size of 200 patients...",
    "page_num": null
  },
  "notes": null
}
```

#### Report
```bash
cat output/NCT00000001_consort_iter3.md | head -100
```

**Example:**
```markdown
# Clinical Trial Report: NCT00000001

## Title and Abstract

This randomized, double-blind, placebo-controlled trial [consort.trial_design]...

## Methods

### Study Design
The study was conducted at 50 sites across the United States and Europe [consort.sites]...
```

#### Critique
```bash
cat output/NCT00000001_consort_critique_iter3.md
```

**Example:**
```markdown
# Critique: CONSORT Report (Iteration 3)

## Overall Score: 80.0 / 100

## Checklist Coverage
- Required items: 25
- Populated: 20 (80%)
- Missing: 5 (20%)

## Missing Items
- 21: Harms

## Unused Facts
None

## Unsupported Claims
None

## Validation: PASSED
```

---

## Smoke Test (Automated)

For automated testing (CI), use `scripts/demo.sh` (created in Phase 4):

```bash
./scripts/demo.sh
```

**Expected:** Exits with code 0 and prints `SMOKE_OK` (or `DEMO_OK` if full LLM execution feasible).

---

## Individual Stage Demos

### Ingest Only

```bash
clinirepgen ingest \
  --trial NCT00000001 \
  --input sample_data/ \
  --out manifest.json

# Inspect
jq . manifest.json | head -50
```

### Extract Only (requires manifest + API key)

```bash
clinirepgen extract \
  --manifest manifest.json \
  --out facts.json \
  --checklist consort

# Inspect
jq '.checklist_coverage' facts.json
```

### Generate Only (requires facts + API key)

```bash
clinirepgen generate \
  --facts facts.json \
  --type consort \
  --out report.md \
  --no-critique

# View report
cat report.md
```

### Info (inspect existing artifacts)

```bash
# Manifest info
clinirepgen info --manifest manifest.json

# Facts info
clinirepgen info --facts facts.json
```

---

## Troubleshooting

### Error: "API_KEY not set"

**Fix:** Export API key before running:
```bash
export API_KEY="sk-..."
```

### Error: "No documents found"

**Fix:** Verify input directory contains files:
```bash
ls sample_data/
```

Expected: `demo_protocol.txt` or other files.

### Error: "Rate limit exceeded"

**Fix:** Wait 60 seconds and retry. Or reduce concurrency:
```bash
clinirepgen run ... --iterations 1  # Fewer LLM calls
```

### Error: "Invalid JSON response from LLM"

**Fix:** Check LLM model version:
```bash
export CLINIREPGEN_MODEL="gpt-4o-2024-08-06"  # Pin to specific version
```

Or increase max_tokens:
```bash
# Not yet exposed via CLI; requires code change in config.py
```

### Slow Execution (> 5 minutes)

**Likely cause:** Large documents or many checklist items.

**Fixes:**
1. Reduce checklist scope: `--types consort` (omit ICH E3)
2. Reduce iterations: `--iterations 1`
3. Use faster model: `export CLINIREPGEN_MODEL="gpt-4o-mini"`

### Low Coverage (< 70%)

**Diagnosis:**
```bash
jq '.consort_facts | to_entries | map(select(.value.value == null)) | map(.key)' facts.json
```

**Fix:** Provide more complete source documents (protocol, CSR, etc.). Sample data is minimal; real trials require full document set.

---

## Expected Runtimes

| Demo Type | Duration | Notes |
|-----------|----------|-------|
| Quick demo (no API) | 1-2s | Ingest only |
| Full pipeline (CONSORT only) | 60-90s | 1 trial, 25 items, 1 iteration |
| Full pipeline (3 iterations) | 180-270s | Worst case: all iterations |
| Individual stage (ingest) | 5-10s | Depends on document count |
| Individual stage (extract) | 40-60s | Depends on checklist size |
| Individual stage (generate) | 15-25s | Per report type |

---

## Success Criteria

Demo is **successful** if:
1. **Quick demo:** Outputs `Demo complete!` and creates `demo_manifest.json`
2. **Full pipeline:** Exits with "Pipeline completed!" and `Passed: True` (or `False` after max iterations)
3. **Coverage:** ≥ 70% for CONSORT required items (may fail with minimal sample data; acceptable)
4. **Outputs:** All expected files created (manifest, facts, reports, critiques)

Demo is **failed** if:
1. Python exception (stack trace)
2. API error with no retry (should retry 3x automatically)
3. Missing output files
4. Corrupt JSON (cannot parse with `jq`)

---

## Next Steps After Demo

1. **Inspect outputs:** Review generated reports for quality
2. **Try real data:** Replace `sample_data/` with actual trial documents
3. **Tune configuration:** Adjust `max_iterations`, `temperature`, model
4. **Evaluate coverage:** Compare against EVAL.md metrics
5. **Iterate:** If coverage < 70%, add missing source documents and re-run
