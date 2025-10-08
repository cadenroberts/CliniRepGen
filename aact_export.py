#!/usr/bin/env python3
import psycopg2
import json
import sys

def fetch_dicts(cur):
    """Helper: fetch all rows as list of dicts"""
    cols = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def export_trial(nct_id, user, password, outfile=None):
    conn = psycopg2.connect(
        host="aact-db.ctti-clinicaltrials.org",
        dbname="aact",
        user=user,
        password=password,
        sslmode="require"
    )
    cur = conn.cursor()

    # Study metadata
    cur.execute("""
        SELECT nct_id, brief_title, official_title, phase, study_type,
               enrollment, start_date, completion_date, overall_status
        FROM ctgov.studies
        WHERE nct_id = %s
    """, (nct_id,))
    study = fetch_dicts(cur)
    study = study[0] if study else None

    # Interventions
    cur.execute("""
        SELECT intervention_type, name, description
        FROM ctgov.interventions
        WHERE nct_id = %s
    """, (nct_id,))
    interventions = fetch_dicts(cur)

    # Outcomes
    cur.execute("""
        SELECT outcome_type, title, time_frame, description
        FROM ctgov.outcomes
        WHERE nct_id = %s
    """, (nct_id,))
    outcomes = fetch_dicts(cur)

    # Outcome measurements
    cur.execute("""
        SELECT outcome_id, title, param_type, param_value,
               dispersion_type, dispersion_value
        FROM ctgov.outcome_measurements
        WHERE nct_id = %s
    """, (nct_id,))
    measurements = fetch_dicts(cur)

    # Adverse events
    cur.execute("""
        SELECT event_type, organ_system, adverse_event_term,
               subjects_affected, subjects_at_risk
        FROM ctgov.reported_events
        WHERE nct_id = %s
    """, (nct_id,))
    adverse_events = fetch_dicts(cur)

    bundle = {
        "study": study,
        "interventions": interventions or None,
        "outcomes": outcomes or None,
        "measurements": measurements or None,
        "adverse_events": adverse_events or None
    }

    conn.close()

    if outfile is None:
        outfile = f"trial_{nct_id}.json"

    with open(outfile, "w") as f:
        json.dump(bundle, f, indent=2, default=str)

    print(f"✅ Exported {nct_id} to {outfile}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python aact_export.py <NCT_ID> <AACT_USERNAME>")
        sys.exit(1)

    nct_id = sys.argv[1]
    user = sys.argv[2]
    password = input("Password for AACT user: ")
    export_trial(nct_id, user, password)

