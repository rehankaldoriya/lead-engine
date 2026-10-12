# ALOREX Lead Engine

A professional lead-generation, business-research, qualification, and sales-management application for cafés and restaurants.

## Setup Instructions (macOS)

1. **Navigate to project directory**:
   ```bash
   cd path/to/alorEx-lead-engine
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   python3 -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Launch the application**:
   ```bash
   streamlit run app.py
   ```

The application should now be available at `http://localhost:8501`.

## Usage Guide

1. **Discovery**: Use the 'Business Discovery' page to find restaurants and cafés in Ahmedabad and Gandhinagar using OpenStreetMap data.
2. **Management**: Review and edit leads in the 'All Leads' and 'Lead Profile' pages.
3. **Qualification**: Use 'Research & Qualification' to score leads based on ALOREX's premium criteria.
4. **Sales**: Track outreach, meetings, and deals via the 'Follow-ups' and 'Outreach Generator' pages.
5. **Data**: Import external lists via CSV or create backups in the 'Backups' page.

## Stopping the Application
Press `Control + C` in the terminal where the application is running.

## Restarting
```bash
source .venv/bin/activate
streamlit run app.py
```
