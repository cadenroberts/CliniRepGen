#!/usr/bin/env python3
"""
Fetch Open Access file links for PMCIDs in drug_pm_pmc_map.csv
Outputs: drug_pmc_oa_links.csv
"""

import pandas as pd
import requests
import xml.etree.ElementTree as ET
import time
import csv

# === Configuration ===
INPUT = "drug_pm_pmc_map.csv"
OUTPUT = "drug_pmc_oa_links.csv"
BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
DELAY = 0.34  # seconds between requests to be polite to NCBI

# === Load PMCIDs ===
df = pd.read_csv(INPUT)
if "pmcid" not in df.columns:
    raise ValueError("Input file must contain a 'pmcid' column.")

# keep unique, valid PMCIDs (strip 'PMC' prefix if missing)
pmcids = (
    df["pmcid"]
    .dropna()
    .astype(str)
    .str.extract(r'(PMC\d+)')[0]
    .dropna()
    .unique()
    .tolist()
)

print(f"Found {len(pmcids)} PMCIDs to query")

# === Prepare CSV writer ===
with open(OUTPUT, "w", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["pmcid", "citation", "license", "format", "updated", "href"])

    for i, pmcid in enumerate(pmcids, start=1):
        try:
            r = requests.get(BASE_URL, params={"id": pmcid}, timeout=20)
            r.raise_for_status()
            root = ET.fromstring(r.text)

            for rec in root.findall(".//record"):
                citation = rec.get("citation", "")
                license_ = rec.get("license", "")
                for link in rec.findall(".//link"):
                    fmt = link.get("format")
                    href = link.get("href")
                    updated = link.get("updated", "")
                    writer.writerow([pmcid, citation, license_, fmt, updated, href])

            if i % 20 == 0:
                print(f"Processed {i} / {len(pmcids)}")
            time.sleep(DELAY)

        except Exception as e:
            print(f"[Error] {pmcid}: {e}")
            time.sleep(DELAY)

print(f"\nSaved Open Access links to {OUTPUT}")

