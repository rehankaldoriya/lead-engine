from typing import List, Dict, Any, Optional
from modules.database import DatabaseManager

class OutreachManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def update_pipeline_status(self, lead_id: int, status: str):
        """Updates the status of a lead in the sales pipeline."""
        self.db.update_lead(lead_id, {"outreach_status": status})

    def log_activity(self, lead_id: int, activity_type: str, channel: str, notes: str, outcome: str, next_action: str):
        """Logs an outreach activity."""
        self.db.execute_query(
            "INSERT INTO outreach_history (lead_id, activity_type, channel, notes, outcome, next_action) VALUES (?, ?, ?, ?, ?, ?)",
            (lead_id, activity_type, channel, notes, outcome, next_action)
        )

    def get_outreach_history(self, lead_id: int) -> List[Dict[str, Any]]:
        """Retrieves the outreach history for a lead."""
        return self.db.fetch_all(
            "SELECT * FROM outreach_history WHERE lead_id = ? ORDER BY activity_date DESC",
            (lead_id,)
        )

    def generate_message_draft(self, lead: Dict[str, Any], message_type: str) -> str:
        """
        Generates a professional message draft based on verified facts.
        """
        name = lead.get('business_name', 'your business')
        area = lead.get('area', '')

        # Base templates
        templates = {
            "Instagram DM": (
                f"Hello {name}! 👋\n\nWe've been following your presence in {area} and love the aesthetic you're building. "
                "We specialize in premium digital experiences for venues like yours and would love to share how "
                "ALOREX can enhance your customer's digital journey. Would you be open to a brief chat?"
            ),
            "WhatsApp": (
                f"Hi {name}, this is [Your Name] from ALOREX. We're working with premium cafés and restaurants in {area} "
                "to upgrade their digital presence and customer interfaces. I'd love to send over a few ideas "
                "specifically for your venue. Do you have a moment this week?"
            ),
            "Email": (
                f"Subject: Enhancing the Digital Experience at {name}\n\n"
                f"Dear {name} Team,\n\n"
                f"I am reaching out from ALOREX, a platform dedicated to creating premium digital experiences "
                f"for boutique dining and specialty cafés in {area}.\n\n"
                "We believe that the digital presentation of a venue should match the quality of its physical ambience. "
                "Our solutions are designed to seamlessly integrate with your brand identity and elevate the customer journey.\n\n"
                "I would appreciate the opportunity to discuss how ALOREX could support your vision. "
                "Are you available for a brief introductory call next week?\n\n"
                "Best regards,\n[Your Name]\nALOREX"
            ),
            "Follow-up": (
                f"Hi {name}, just following up on my previous message. I'm still very interested in seeing how "
                f"ALOREX could support your venue in {area}. Let me know if you have a few minutes to connect!"
            )
        }

        return templates.get(message_type, "Please select a valid message type.")
