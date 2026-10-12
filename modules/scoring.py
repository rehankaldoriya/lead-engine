from typing import Dict, Any, List, Tuple
from modules.database import DatabaseManager

class ScoringEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def calculate_preliminary_score(self, evidence: Dict[str, Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
        """
        Calculates the lead score based on the defined factors.
        evidence: { 'category_name': { 'score': 0-max, 'evidence': '...', 'source': '...' } }
        """
        total_score = 0
        breakdown = {}

        # Definition of scoring factors and their max weights
        factors = {
            "Premium positioning": 25,
            "Ambience/Experience": 20,
            "Specialty Concept": 15,
            "Independent/Boutique": 15,
            "Digital Opportunity": 15,
            "Expansion Potential": 10
        }

        for factor, max_score in factors.items():
            item = evidence.get(factor, {"score": 0, "evidence": "Unknown", "source": "N/A"})
            score = min(item.get('score', 0), max_score)
            total_score += score
            breakdown[factor] = item

        return total_score, breakdown

    def get_priority(self, score: int) -> str:
        """Classifies priority based on score."""
        if score >= 70:
            return "High"
        elif score >= 45:
            return "Medium"
        else:
            return "Low"

    def save_score(self, lead_id: int, breakdown: Dict[str, Any], manual_adj: int = 0, adj_reason: str = ""):
        """Saves the scoring breakdown and updates the lead's final score."""
        total_preliminary = sum(item.get('score', 0) for item in breakdown.values())
        final_score = max(0, min(100, total_preliminary + manual_adj))
        priority = self.get_priority(final_score)

        # Update lead record
        self.db.update_lead(lead_id, {
            "lead_score": total_preliminary,
            "manual_score_adjustment": manual_adj,
            "final_score": final_score,
            "lead_priority": priority,
            "score_reason": adj_reason
        })

        # Save breakdown details
        for category, data in breakdown.items():
            self.db.execute_query(
                "INSERT INTO scoring_breakdown (lead_id, category, score, evidence, source, confidence, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (lead_id, category, data.get('score', 0), data.get('evidence', ""), data.get('source', ""), data.get('confidence', ""), data.get('notes', ""))
            )
