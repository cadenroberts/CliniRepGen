#!/usr/bin/env bash
# Demo script for CliniRepGen
# Non-interactive smoke test that validates basic functionality
# Exits non-zero on failure
# Ends with DEMO_OK (full execution) or SMOKE_OK (build-only)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    if [ -d "$DEMO_DIR" ]; then
        rm -rf "$DEMO_DIR"
    fi
}

# Error handler
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    cleanup
    exit 1
}

# Success message
success() {
    echo -e "${GREEN}$1${NC}"
}

# Info message
info() {
    echo -e "${YELLOW}$1${NC}"
}

# Main demo
main() {
    DEMO_DIR="$(mktemp -d)"
    
    info "=== CliniRepGen Demo Script ==="
    echo "Demo directory: $DEMO_DIR"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error_exit "python3 not found"
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "Python version: $PYTHON_VERSION"
    
    # Check clinirepgen installed
    if ! python3 -m clinirepgen.cli --version &> /dev/null; then
        error_exit "clinirepgen not installed (run: pip install -e .)"
    fi
    
    success "clinirepgen is installed"
    
    # Check if API_KEY is set
    if [ -z "${API_KEY:-}" ]; then
        info "API_KEY not set - running smoke test only (ingest stage)"
        RUN_MODE="smoke"
    else
        info "API_KEY detected - running full demo"
        RUN_MODE="full"
    fi
    
    # Stage 1: Ingest (always run)
    info "\n=== Stage 1: Ingest ==="
    
    # Run demo command (creates sample data and builds manifest)
    python3 -m clinirepgen.cli demo &> "$DEMO_DIR/demo_output.log" || error_exit "Demo command failed"
    
    # Check manifest exists
    if [ ! -f "demo_output/demo_manifest.json" ]; then
        error_exit "Manifest not created"
    fi
    
    success "Manifest created: demo_output/demo_manifest.json"
    
    # Validate manifest structure
    if ! command -v jq &> /dev/null; then
        info "jq not found - skipping JSON validation"
    else
        TRIAL_ID=$(jq -r '.trial_id' demo_output/demo_manifest.json)
        DOC_COUNT=$(jq '.documents | length' demo_output/demo_manifest.json)
        SEC_COUNT=$(jq '.sections | length' demo_output/demo_manifest.json)
        
        if [ "$TRIAL_ID" != "NCT00000001" ]; then
            error_exit "Invalid trial_id in manifest: $TRIAL_ID"
        fi
        
        echo "  Trial ID: $TRIAL_ID"
        echo "  Documents: $DOC_COUNT"
        echo "  Sections: $SEC_COUNT"
        
        if [ "$DOC_COUNT" -lt 1 ] || [ "$SEC_COUNT" -lt 1 ]; then
            error_exit "Manifest is incomplete (no documents or sections)"
        fi
        
        success "Manifest structure is valid"
    fi
    
    # If smoke test only, stop here
    if [ "$RUN_MODE" = "smoke" ]; then
        info "\n=== Smoke Test Complete ==="
        success "SMOKE_OK"
        cleanup
        exit 0
    fi
    
    # Stage 2: Extract (full demo only)
    info "\n=== Stage 2: Extract ==="
    
    python3 -m clinirepgen.cli extract \
        --manifest demo_output/demo_manifest.json \
        --out "$DEMO_DIR/facts.json" \
        --checklist consort \
        &> "$DEMO_DIR/extract_output.log" || error_exit "Extract stage failed"
    
    if [ ! -f "$DEMO_DIR/facts.json" ]; then
        error_exit "Facts file not created"
    fi
    
    success "Facts extracted: $DEMO_DIR/facts.json"
    
    # Validate facts
    if command -v jq &> /dev/null; then
        POPULATED=$(jq '[.consort_facts | to_entries[] | select(.value.value != null)] | length' "$DEMO_DIR/facts.json")
        TOTAL=$(jq '.consort_facts | length' "$DEMO_DIR/facts.json")
        COVERAGE=$(jq -r '.checklist_coverage.consort // 0' "$DEMO_DIR/facts.json")
        
        echo "  Populated facts: $POPULATED / $TOTAL"
        echo "  Coverage: $(echo "$COVERAGE * 100" | bc -l | cut -c1-5)%"
        
        if [ "$POPULATED" -lt 1 ]; then
            error_exit "No facts extracted"
        fi
        
        success "Facts are valid"
    fi
    
    # Stage 3: Generate (full demo only)
    info "\n=== Stage 3: Generate ==="
    
    python3 -m clinirepgen.cli generate \
        --facts "$DEMO_DIR/facts.json" \
        --type consort \
        --out "$DEMO_DIR/report" \
        --no-critique \
        &> "$DEMO_DIR/generate_output.log" || error_exit "Generate stage failed"
    
    # Check report exists (exact filename may vary)
    REPORT_FILE=$(find "$DEMO_DIR" -name "*_consort_*.md" | head -1)
    
    if [ -z "$REPORT_FILE" ]; then
        error_exit "Report not created"
    fi
    
    success "Report generated: $REPORT_FILE"
    
    # Validate report has content
    WORD_COUNT=$(wc -w < "$REPORT_FILE")
    
    if [ "$WORD_COUNT" -lt 10 ]; then
        error_exit "Report is too short ($WORD_COUNT words)"
    fi
    
    echo "  Word count: $WORD_COUNT"
    success "Report is valid"
    
    # Full demo complete
    info "\n=== Full Demo Complete ==="
    success "DEMO_OK"
    
    cleanup
    exit 0
}

# Trap errors
trap cleanup EXIT

# Run main
main "$@"
