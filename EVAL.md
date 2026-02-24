# Evaluation

## Correctness Definition

CliniRepGen correctness is defined by four properties:

1. **Checklist Coverage**: Percentage of required CONSORT/ICH E3 items populated with high or medium confidence
2. **Provenance Fidelity**: Every fact value traces to an exact source location (file, section, offset); no hallucinated facts
3. **Citation Completeness**: Every claim in the generated report is backed by an inline citation to a fact with provenance
4. **Reproducibility**: Identical inputs produce identical manifests, facts, and reports (deterministic when `temperature=0.0`)

## Metrics

### 1. Checklist Coverage

**Definition:** Fraction of required checklist items with non-null, high/medium confidence facts.

**Formula:**
```
coverage = populated_required / total_required

where:
  populated_required = count(item in required_items where fact.value != null and fact.confidence in [high, medium])
  total_required = count(item in checklist where item.required == true)
```

**Target:** ≥ 70% for production use

**Command:**
```bash
clinirepgen extract --manifest manifest.json --out facts.json --checklist consort
grep -A 1 "Coverage:" facts.json
```

**Example Output:**
```json
{
  "trial_id": "NCT00000001",
  "checklist_coverage": {
    "consort": 0.72,
    "ich_e3": 0.68
  },
  "populated_facts": 18,
  "total_facts": 25
}
```

### 2. Provenance Fidelity

**Definition:** Fraction of populated facts with valid provenance (non-empty file_name, section_id or table_id).

**Formula:**
```
fidelity = facts_with_provenance / populated_facts

where:
  facts_with_provenance = count(fact where fact.value != null and fact.provenance.file_name != null)
  populated_facts = count(fact where fact.value != null)
```

**Target:** 100% (every fact must have provenance)

**Command:**
```bash
python -c "
import json
with open('facts.json') as f:
    facts = json.load(f)
# Traverse fact tree, count provenance
"
```

### 3. Citation Completeness

**Definition:** Fraction of report statements backed by citations; count of unsupported claims.

**Formula:**
```
completeness = cited_claims / total_claims
unsupported = total_claims - cited_claims

where:
  total_claims = sentences in report that contain factual assertion
  cited_claims = claims followed by [fact_path] citation
```

**Target:** 100% completeness, 0 unsupported claims

**Command:**
```bash
clinirepgen generate --facts facts.json --type consort --critique --out report.md
grep "Unsupported claims:" report_critique.md
```

**Example Output:**
```
Unsupported claims: 0
Total claims: 45
Citation rate: 100%
```

### 4. Reproducibility

**Definition:** Identical inputs produce identical SHA-256 hashes for manifests and facts.

**Formula:**
```
reproducible = (hash(manifest1) == hash(manifest2)) and (hash(facts1) == hash(facts2))
```

**Target:** True (bit-for-bit identical)

**Command:**
```bash
# Run 1
clinirepgen ingest --trial NCT00000001 --input sample_data/ --out manifest1.json
sha256sum manifest1.json

# Run 2
clinirepgen ingest --trial NCT00000001 --input sample_data/ --out manifest2.json
sha256sum manifest2.json

# Compare
diff <(jq -S . manifest1.json) <(jq -S . manifest2.json)
```

**Expected:** No diff (exit code 0)

**Known Issues:**
- Manifest ID embeds timestamp → not reproducible (issue #1, P0)
- LLM temperature > 0 → facts may vary (issue #2, P0)

## Measurable Commands

### Full Pipeline Evaluation

Run complete pipeline and extract metrics:

```bash
# Run pipeline
clinirepgen run \
  --trial NCT00000001 \
  --input sample_data/ \
  --ctgov sample_data/demo_trial.json \
  --out output/ \
  --iterations 3 \
  --verbose

# Extract coverage
jq '.checklist_coverage' output/NCT00000001_facts.json

# Extract validation status
grep "Validation:" output/NCT00000001_consort_critique_iter*.md | tail -1

# Count unsupported claims
grep "Unsupported claims:" output/NCT00000001_consort_critique_iter*.md | tail -1

# Check iteration count
ls output/NCT00000001_consort_iter*.md | wc -l
```

### Manifest Determinism Test

Verify SHA-256 stability:

```bash
# Ingest twice
for i in 1 2; do
  clinirepgen ingest \
    --trial NCT00000001 \
    --input sample_data/ \
    --out manifest_$i.json
done

# Compare section IDs (should be identical)
diff \
  <(jq -S '.sections | keys | sort' manifest_1.json) \
  <(jq -S '.sections | keys | sort' manifest_2.json)

# Compare document SHA-256s
diff \
  <(jq -S '.documents | map(.sha256) | sort' manifest_1.json) \
  <(jq -S '.documents | map(.sha256) | sort' manifest_2.json)
```

**Expected:** No diff

### Extraction Accuracy Test (Manual Ground Truth)

For a manually curated trial with known facts:

```bash
# Extract facts
clinirepgen extract \
  --manifest ground_truth_manifest.json \
  --out extracted_facts.json

# Compare against ground truth
python scripts/compare_facts.py \
  extracted_facts.json \
  ground_truth_facts.json
```

**Metrics:**
- Precision: extracted_correct / extracted_total
- Recall: extracted_correct / ground_truth_total
- F1: 2 * (precision * recall) / (precision + recall)

**Target:** F1 ≥ 0.85

*Note: `scripts/compare_facts.py` not yet implemented (P1)*

### Citation Validation Test

Parse report and validate all citations:

```bash
# Generate report
clinirepgen generate \
  --facts facts.json \
  --type consort \
  --out report.md

# Extract citations
grep -oE '\[consort\.[a-z_]+\]' report.md | sort -u > citations.txt

# Check all citations exist in facts
python -c "
import json
with open('facts.json') as f:
    facts = json.load(f)
with open('citations.txt') as f:
    citations = [line.strip()[1:-1] for line in f]  # Remove []
missing = [c for c in citations if c not in facts['consort_facts']]
if missing:
    print(f'Missing facts: {missing}')
    exit(1)
print('All citations valid')
"
```

**Expected:** "All citations valid", exit code 0

## Pass/Fail Criteria

### Pass Criteria (Production Ready)

A pipeline run **passes** if:
1. Checklist coverage ≥ 70% for required items
2. Provenance fidelity = 100%
3. Citation completeness = 100%
4. Unsupported claims = 0
5. Reproducibility: manifest SHA-256s identical across runs (deterministic mode)

### Fail Criteria (Needs Review)

A pipeline run **fails** if:
1. Coverage < 70% after max iterations
2. Provenance fidelity < 100% (any fact missing provenance)
3. Unsupported claims > 0
4. Reproducibility: manifest SHA-256s differ across identical inputs

### Manual Review Triggers

Even if automated criteria pass, **manual review required** if:
1. Coverage 70-80% (marginal)
2. Any low-confidence facts cited in report
3. Any notes field contains "conflict" or "ambiguous"
4. Source documents include handwritten notes or scanned images (OCR risk)

## Performance Expectations

### Latency

Typical latency for single trial (10 documents, ~200 pages):

| Stage | Time | Notes |
|-------|------|-------|
| Ingest | 10-30s | PDF parsing bottleneck |
| Extract (CONSORT, 25 items) | 40-60s | LLM calls dominate |
| Extract (ICH E3, 50 items) | 80-120s | More items → more time |
| Generate (per report) | 15-25s | Template-driven, faster |
| Critique | 5-10s | Validation logic, no LLM |
| **Total (single iteration)** | **60-90s** | |
| **Total (3 iterations)** | **180-270s** | Worst case: all iterations needed |

### Cost

Typical LLM token usage (gpt-4o pricing: $5/1M input, $15/1M output):

| Stage | Input Tokens | Output Tokens | Cost |
|-------|--------------|---------------|------|
| Extract (25 items) | 125k | 5k | $0.70 |
| Generate (CONSORT) | 20k | 3k | $0.15 |
| Generate (ICH E3) | 30k | 5k | $0.23 |
| **Total per iteration** | **175k** | **13k** | **$1.08** |
| **Total (3 iterations)** | **525k** | **39k** | **$3.24** |

*Note: Actual usage varies by document complexity. Reduce cost by setting `--checklist consort` (only CONSORT, not ICH E3).*

### Resource Usage

- **Memory:** ~500MB peak (document parsing)
- **Disk:** ~5MB per trial (manifest + facts + reports)
- **Network:** ~700KB per LLM call (compressed HTTP)

## Troubleshooting

### Low Coverage (< 70%)

**Symptom:** Pipeline completes but coverage below threshold.

**Diagnosis:**
```bash
# Check which items are missing
jq '.consort_facts | to_entries | map(select(.value.value == null)) | map(.key)' facts.json
```

**Common Causes:**
1. Missing source documents (e.g., no CSR provided)
2. Poor search queries (checklist question does not match document terminology)
3. LLM extraction failure (returned null despite relevant sections)

**Fixes:**
1. Provide more complete source documents
2. Manually inspect sections for missing items; if present, file issue with query
3. Increase `max_tokens` or switch to more capable model

### Unsupported Claims

**Symptom:** Critique flags unsupported claims (statements without citations).

**Diagnosis:**
```bash
grep -A 5 "Unsupported claims:" output/*_critique*.md
```

**Common Causes:**
1. Writer generated inferred statement not directly in facts
2. Writer hallucinated fact
3. Citation parsing failed (wrong format)

**Fixes:**
1. Re-generate with stricter system prompt (orchestrator does this automatically)
2. Manual review: remove or rephrase unsupported claim
3. Check citation format: must be `[fact_path]` exactly

### Reproducibility Failure

**Symptom:** Identical inputs produce different manifest SHA-256s.

**Diagnosis:**
```bash
diff <(jq -S . manifest1.json) <(jq -S . manifest2.json)
```

**Common Causes:**
1. Timestamp in manifest_id (known issue)
2. Filesystem iteration order (file list not sorted)
3. Nondeterministic PDF parsing (pdfplumber version change)

**Fixes:**
1. Ignore `manifest_id` field when comparing
2. Sort file lists before ingest
3. Pin pdfplumber version in requirements.lock

## Continuous Evaluation

### Regression Test Suite (Not Yet Implemented)

Proposed structure:

```bash
tests/
  regression/
    nct00000001/
      input/
        protocol.pdf
        csr.pdf
        ctgov.json
      expected/
        manifest.json
        facts.json
        coverage.json
    nct00000002/
      ...
```

**Test Script:**
```bash
pytest tests/regression/test_pipeline.py

# For each trial:
# 1. Run pipeline
# 2. Compare coverage against expected
# 3. Validate all citations
# 4. Check reproducibility
```

**Status:** P1, not implemented yet

## Summary

CliniRepGen correctness is measurable via:
1. Coverage metrics (automated)
2. Provenance validation (automated)
3. Citation checking (automated)
4. Reproducibility tests (partially automated)

All metrics accessible via CLI commands. Pass criteria: coverage ≥ 70%, no unsupported claims, full provenance, reproducible manifests.
