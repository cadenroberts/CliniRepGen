import json
import pandas as pd
from sqlalchemy import create_engine

# --- Connect to Supabase ---
engine = create_engine("postgresql://postgres:clinirepgen@db.rdxpprfzhkkoizwxrpou.supabase.co:5432/postgres")

# --- Load JSON file ---
with open("/Users/cwr/Downloads/drug-drugsfda-0001-of-0001.json", "r") as f:
    data = json.load(f)

# --- Extract only the drug records ---
results = data["results"]

# --- Flatten nested JSON (shallow flatten) ---
df = pd.json_normalize(results)

print("Columns:", len(df.columns))
print(df.columns[:20])

# --- Convert all nested (non-primitive) objects to JSON strings ---
for col in df.columns:
    df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)

# --- Upload to Supabase ---
df.columns = [c.replace('.', '_') for c in df.columns]

df.to_sql("drugsfda_results", engine, schema="fda", if_exists="replace", index=False)

print(f"✅ Upload complete. Rows inserted: {len(df)}")

