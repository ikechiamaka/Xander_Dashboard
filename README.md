# Monterey Capstone Dashboard

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
streamlit run app.py
```

The dashboard reads `data/capstone.db` and opens at `http://localhost:8501`.

## Refresh the data

Run `run_pipeline.bat` from Windows Task Scheduler once per day. Or, from an
elevated PowerShell window in this directory, run `.\schedule_pipeline.ps1`.
The pipeline
fetches CDC PLACES and HCAI data, downloads the four CDPH trend exports, and
loads them into the SQLite database. It is safe to run repeatedly.

The sheriff's log is intentionally not used until Monterey County confirms that its data may be published.

The sheriff's log is intentionally not used until Monterey County confirms that its data may be published.
