import pandas as pd, requests, time

df = pd.read_csv("drug_trials_pmids.csv")

# Convert PMIDs to strings early
pmids = list(df["pmid"].dropna().astype(str).unique())

rows = []
for chunk_start in range(0, len(pmids), 200):
    batch = pmids[chunk_start:chunk_start+200]
    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    r = requests.get(url, params={"ids": ",".join(batch), "format": "json"})
    r.raise_for_status()
    rows.extend(r.json().get("records", []))
    print(f"Processed {chunk_start + len(batch)} / {len(pmids)}")
    time.sleep(0.3)

pd.DataFrame(rows).to_csv("drug_pm_pmc_map.csv", index=False)
print("Saved drug_pm_pmc_map.csv")

