# ALOREX Lead Engine
Local-first prospect discovery, research, qualification and sales pipeline for premium cafés/restaurants. Python, Streamlit, SQLite and Pandas.

## Safety and limitations
- This is a separate app and does not integrate with or modify any Alorex/Velora app.
- Data lives in `data/alorex_leads.sqlite3` by default. No cloud server or paid API is required.
- OpenStreetMap coverage is incomplete; data may be stale, absent or misclassified. Verify details before outreach. Fine dining and boutique categories use broad OSM tags, not reliable classifications.
- Scores are initial heuristics, not validated predictions. Unknown evidence receives zero points; a score is not proof a venue needs ALOREX.
- Outreach is draft-only. The app never sends messages automatically.
- OSM data is available under ODbL; source links are included. Respect Overpass policies and rate limits. No Google Maps/Instagram scraping or bypassing protections.

## Mac setup
Python 3.10+ recommended. Unzip the project so its folder is `~/Projects/alorex-lead-engine`, then run:
```bash
mkdir -p ~/Projects
cd ~/Projects/alorex-lead-engine
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```
Open the local URL Streamlit prints, usually `http://localhost:8501`. Stop with Ctrl+C in the terminal.

Keep this database isolated. Optional custom path for this app only:
```bash
ALOREX_LEAD_DB="$HOME/Projects/alorex-lead-engine/data/local-leads.sqlite3" streamlit run app.py
```
Do not point it at another app's database.

## Backup and restore
In **Backups & settings**, click **Prepare backup**, then **Download SQLite backup**. Restore a trusted backup and tick the confirmation checkbox. A pre-restore backup is saved beside the current database.
Manual backup with app stopped:
```bash
mkdir -p backups
cp data/alorex_leads.sqlite3 "backups/alorex-leads-$(date +%F).sqlite3"
```
Manual restore only with app stopped and after backing up current data:
```bash
cp backups/your-backup.sqlite3 data/alorex_leads.sqlite3
```

## CSV import/export
Download a template in **Import / export**. Import maps columns, previews rows, validates required business name and reports errors. Safe duplicate updates fill blank fields only and preserve existing values. Exports support filters or all leads. `sample_leads.csv` is an example only; verify or replace its data.

## Tests
```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```
Tests use temporary SQLite files and mocked network responses; they do not require Overpass connectivity.

## Included features
Dashboard, lead database, manual add/edit, scoring, pipeline, follow-up reminders, CSV import/export, OpenStreetMap discovery, lead research checklist/profile, outreach history, draft-only message generation and confirmed backup/restore. Scoring weights are editable in `scoring.py`.
