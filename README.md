# Monterey Capstone Dashboard

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

The dashboard reads `data/capstone.db` and opens at `http://localhost:8501`.

The sheriff's log is intentionally not used until Monterey County confirms that its data may be published.
