import re
from typing import List, Dict, Any, Optional
from modules.database import DatabaseManager

class Deduplicator:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def normalize_name(self, name: str) -> str:
        """Normalizes business names for better matching."""
        if not name:
            return ""
        name = name.lower().strip()
        # Remove common suffixes
        suffixes = [
            r"\bpvt ltd\b", r"\bllp\b", r"\bprivate limited\b",
            r"\binc\b", r"\bcorp\b", r"\bcorporation\b"
        ]
        for suffix in suffixes:
            name = re.sub(suffix, "", name)

        # Remove extra whitespace and punctuation
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def find_duplicates(self, lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Checks for duplicates based on strong and secondary identifiers.
        """
        duplicates = []

        # 1. Strong Identifiers (High Confidence)
        # OSM ID
        if lead_data.get('osm_id'):
            res = self.db.fetch_all(
                "SELECT * FROM leads WHERE osm_id = ? AND osm_type = ?",
                (lead_data['osm_id'], lead_data.get('osm_type'))
            )
            duplicates.extend(res)

        # Website domain
        website = lead_data.get('website')
        if website:
            domain = self._extract_domain(website)
            if domain:
                res = self.db.fetch_all(
                    "SELECT * FROM leads WHERE website LIKE ?",
                    (f"%{domain}%",)
                )
                duplicates.extend(res)

        # Phone
        phone = lead_data.get('phone')
        if phone:
            cleaned_phone = re.sub(r'[\s\(\)\-\+]', '', phone)
            if cleaned_phone:
                res = self.db.fetch_all(
                    "SELECT * FROM leads WHERE phone = ? OR phone LIKE ?",
                    (phone, f"%{cleaned_phone}%")
                )
                duplicates.extend(res)

        # 2. Secondary Matching (Medium Confidence)
        # Normalized Name + City + Area
        name = self.normalize_name(lead_data.get('business_name', ""))
        city = lead_data.get('city')
        area = lead_data.get('area')

        if name and city:
            res = self.db.fetch_all(
                "SELECT * FROM leads WHERE city = ? AND business_name LIKE ?",
                (city, f"%{name}%")
            )

            # Filter results to only keep those in the same area if area is provided
            filtered_res = []
            for r in res:
                if area and r['area'] and r['area'] != area:
                    continue
                filtered_res.append(r)

            duplicates.extend(filtered_res)

        # Remove duplicates from the list (by lead_id)
        unique_duplicates = {d['lead_id']: d for d in duplicates}.values()
        return list(unique_duplicates)

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extracts domain from a URL."""
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc
            if not domain:
                return None
            # Remove www.
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return None
