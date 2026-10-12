import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "data/leads.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Leads Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_name TEXT NOT NULL,
                    business_category TEXT,
                    subcategory TEXT,
                    city TEXT NOT NULL,
                    area TEXT,
                    full_address TEXT,
                    postal_code TEXT,
                    latitude REAL,
                    longitude REAL,
                    website TEXT,
                    phone TEXT,
                    email TEXT,
                    instagram_url TEXT,
                    facebook_url TEXT,
                    other_social_urls TEXT,
                    menu_url TEXT,
                    google_maps_url TEXT,
                    osm_type TEXT,
                    osm_id TEXT,
                    source_url TEXT,
                    source_name TEXT,
                    discovery_date DATETIME,
                    last_verified_date DATETIME,
                    verification_status TEXT DEFAULT 'Unverified',
                    lead_score INTEGER DEFAULT 0,
                    manual_score_adjustment INTEGER DEFAULT 0,
                    final_score INTEGER DEFAULT 0,
                    lead_priority TEXT,
                    score_reason TEXT,
                    research_notes TEXT,
                    outreach_status TEXT DEFAULT 'New',
                    last_contacted_date DATETIME,
                    next_follow_up_date DATETIME,
                    last_response TEXT,
                    meeting_date DATETIME,
                    deal_status TEXT,
                    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                    date_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    brand_name TEXT,
                    parent_group TEXT
                )
            ''')

            # 2. Scoring Breakdown Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scoring_breakdown (
                    breakdown_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    category TEXT,
                    score INTEGER,
                    evidence TEXT,
                    source TEXT,
                    confidence TEXT,
                    notes TEXT,
                    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE
                )
            ''')

            # 3. Outreach History Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outreach_history (
                    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    activity_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    activity_type TEXT,
                    channel TEXT,
                    notes TEXT,
                    outcome TEXT,
                    next_action TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE
                )
            ''')

            # 4. Research Checklist Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS research_checklist (
                    checklist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    item_key TEXT,
                    is_checked BOOLEAN DEFAULT 0,
                    checked_at DATETIME,
                    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE
                )
            ''')

            # 5. Discovery Jobs Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS discovery_jobs (
                    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT,
                    area TEXT,
                    category TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    records_found INTEGER,
                    new_records INTEGER,
                    duplicates INTEGER,
                    errors TEXT,
                    source TEXT,
                    status TEXT
                )
            ''')

            # 6. Import History Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS import_history (
                    import_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    records_imported INTEGER,
                    duplicates_found INTEGER,
                    errors TEXT
                )
            ''')

            # 7. Application Settings Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS application_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT
                )
            ''')

            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_name ON leads(business_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_city ON leads(city)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_osm_id ON leads(osm_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_website ON leads(website)")

            conn.commit()

    def execute_query(self, query: str, params: tuple = ()):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def insert_lead(self, lead_data: Dict[str, Any]) -> int:
        columns = ', '.join(lead_data.keys())
        placeholders = ', '.join(['?'] * len(lead_data))
        query = f"INSERT INTO leads ({columns}) VALUES ({placeholders})"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(lead_data.values()))
            conn.commit()
            return cursor.lastrowid

    def update_lead(self, lead_id: int, update_data: Dict[str, Any]):
        if not update_data:
            return

        update_data['date_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        set_clause = ', '.join([f"{col} = ?" for col in update_data.keys()])
        query = f"UPDATE leads SET {set_clause} WHERE lead_id = ?"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(update_data.values()) + (lead_id,))
            conn.commit()

    def delete_lead(self, lead_id: int):
        query = "DELETE FROM leads WHERE lead_id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (lead_id,))
            conn.commit()

    def get_lead(self, lead_id: int) -> Optional[Dict[str, Any]]:
        return self.fetch_one("SELECT * FROM leads WHERE lead_id = ?", (lead_id,))
