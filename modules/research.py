from typing import List, Dict, Any, Optional
from datetime import datetime
from modules.database import DatabaseManager

class ResearchManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.checklist_items = [
            "venue_fits_profile",
            "website_reviewed",
            "instagram_reviewed",
            "digital_menu_reviewed",
            "customer_experience_researched",
            "existing_solution_identified",
            "opportunity_identified",
            "phone_verified",
            "email_verified",
            "social_verified",
            "decision_maker_identified",
            "multiple_branches_checked"
        ]

    def get_checklist(self, lead_id: int) -> List[Dict[str, Any]]:
        """Gets the research checklist status for a lead."""
        results = self.db.fetch_all(
            "SELECT item_key, is_checked FROM research_checklist WHERE lead_id = ?",
            (lead_id,)
        )

        checked_keys = {r['item_key'] for r in results}

        checklist = []
        for item in self.checklist_items:
            checklist.append({
                "item_key": item,
                "is_checked": item in checked_keys
            })
        return checklist

    def update_checklist_item(self, lead_id: int, item_key: str, is_checked: bool):
        """Updates a single checklist item."""
        if item_key not in self.checklist_items:
            return

        # Check if it already exists
        existing = self.db.fetch_one(
            "SELECT checklist_id FROM research_checklist WHERE lead_id = ? AND item_key = ?",
            (lead_id, item_key)
        )

        if existing:
            self.db.execute_query(
                "UPDATE research_checklist SET is_checked = ?, checked_at = CURRENT_TIMESTAMP WHERE checklist_id = ?",
                (1 if is_checked else 0, existing['checklist_id'])
            )
        else:
            self.db.execute_query(
                "INSERT INTO research_checklist (lead_id, item_key, is_checked, checked_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (lead_id, item_key, 1 if is_checked else 0)
            )

    def update_research_notes(self, lead_id: int, notes: str, verification_status: str):
        """Updates the research notes and verification status."""
        self.db.update_lead(lead_id, {
            "research_notes": notes,
            "verification_status": verification_status,
            "last_verified_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
