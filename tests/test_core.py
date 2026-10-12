import unittest
from modules.database import DatabaseManager
from modules.deduplication import Deduplicator
from modules.scoring import ScoringEngine
import os
import sqlite3

class TestALOREXLeadEngine(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "data/test_leads.db"
        self.db = DatabaseManager(self.test_db_path)
        self.dedup = Deduplicator(self.db)
        self.scoring = ScoringEngine(self.db)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_database_creation(self):
        """Test if database tables are created successfully."""
        leads = self.db.fetch_all("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        self.assertTrue(len(leads) > 0)

    def test_lead_crud(self):
        """Test basic insert and retrieve."""
        lead_data = {"business_name": "Test Café", "city": "Ahmedabad"}
        lead_id = self.db.insert_lead(lead_data)
        lead = self.db.get_lead(lead_id)
        self.assertEqual(lead['business_name'], "Test Café")

    def test_duplicate_detection(self):
        """Test duplicate detection by name and city."""
        lead_data = {"business_name": "Unique Café", "city": "Ahmedabad"}
        self.db.insert_lead(lead_data)

        dups = self.dedup.find_duplicates(lead_data)
        self.assertEqual(len(dups), 1)

    def test_scoring_boundaries(self):
        """Test scoring logic and priority boundaries."""
        evidence = {
            "Premium positioning": {"score": 20},
            "Ambience/Experience": {"score": 15},
            "Specialty Concept": {"score": 10},
            "Independent/Boutique": {"score": 10},
            "Digital Opportunity": {"score": 10},
            "Expansion Potential": {"score": 5}
        }
        # Total = 70 (High)
        score, _ = self.scoring.calculate_preliminary_score(evidence)
        self.assertEqual(score, 70)
        self.assertEqual(self.scoring.get_priority(score), "High")

        # Test Low
        low_score = 40
        self.assertEqual(self.scoring.get_priority(low_score), "Low")

if __name__ == "__main__":
    unittest.main()
