import requests
import os

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

url = "https://data.chhs.ca.gov/dataset/b91d0f25-d2b1-4c9f-b22d-13be3a6c5c90/resource/be06665a-7695-4a0b-af07-f0556d7e6707/download/disposition_ed_2024masked.csv"

response = requests.get(url)
response.raise_for_status()

out_path = os.path.join(DATA_DIR, "hcai_ed_by_county.csv")
with open(out_path, "wb") as f:
    f.write(response.content)

print(f"Saved to {out_path}, size: {len(response.content)} bytes")