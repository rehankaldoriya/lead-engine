import requests
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from modules.database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscoveryEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.timeout = 120
        self.retry_count = 3
        self.backoff_factor = 2

    def _build_overpass_query(self, area_name: str, categories: List[str]) -> str:
        """
        Builds a comprehensive Overpass query for the given area and categories.
        """
        # Category tags mapping
        category_filters = []

        # Basic amenities
        if "Cafés" in categories or "All Restaurants & Cafés" in categories:
            category_filters.append('amenity="cafe"')
        if "Restaurants" in categories or "All Restaurants & Cafés" in categories:
            category_filters.append('amenity="restaurant"')
        if "Fast casual" in categories or "All Restaurants & Cafés" in categories:
            category_filters.append('amenity="fast_food"')
        if "Bakeries" in categories or "All Restaurants & Cafés" in categories:
            category_filters.append('shop="bakery"')
        if "Patisseries" in categories or "All Restaurants & Cafés" in categories:
            category_filters.append('shop="pastry"')
        if "Dessert cafés" in categories or "All Restaurants & Cafés" in categories:
            category_filters.append('shop="confectionery"')
        if "Hotel restaurants" in categories or "All Restaurants & Cafés" in categories:
            category_filters.append('tourism="hotel"') # We'll filter for restaurants inside hotels later or use a combined query
        if "Bars/pubs with food" in categories or "All Restaurants & Cafés" in categories:
            category_filters.append('amenity="bar"')
            category_filters.append('amenity="pub"')
        if "Food courts" in categories or "All Restaurants & Cafés" in categories:
            category_filters.append('amenity="food_court"')

        filter_stmt = " (" + " OR ".join(category_filters) + ");" if category_filters else " (amenity=\"restaurant\" OR amenity=\"cafe\");"

        # Query to find the area first, then find nodes/ways/relations within it
        query = f'''
        [out:json][timeout:25];
        area[name="{area_name}"]->.searchArea;
        (
            node{filter_stmt}(area.searchArea);
            way{filter_stmt}(area.searchArea);
            relation{filter_stmt}(area.searchArea);
        );
        out body;
        out skel qt;
        '''
        return query

    def _fetch_from_overpass(self, query: str) -> Optional[Dict[str, Any]]:
        """Fetches data from Overpass API with retry logic."""
        for attempt in range(self.retry_count):
            try:
                response = requests.post(self.overpass_url, data={'data': query}, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait = self.backoff_factor ** (attempt + 1)
                    logger.warning(f"Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"Overpass error {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error on attempt {attempt + 1}: {e}")
                time.sleep(self.backoff_factor ** attempt)

        return None

    def _normalize_osm_data(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Converts an OSM element into a lead dictionary."""
        tags = element.get('tags', {})

        # Resolve name
        name = tags.get('name') or tags.get('name:en')
        if not name:
            return None

        # Resolve coordinates
        lat = element.get('lat')
        lon = element.get('lon')
        if not lat or not lon:
            # For ways/relations, coordinates are in members. We'll simplify for now
            # or just use the first member's coords.
            if 'members' in element:
                # This is a simplification; proper way is to fetch center
                lat = None
                lon = None

        return {
            "business_name": name,
            "city": "", # To be filled by the discovery job
            "area": tags.get('addr:suburb') or tags.get('addr:city_district') or "",
            "full_address": f"{tags.get('addr:housenumber', '')} {tags.get('addr:street', '')}, {tags.get('addr:suburb', '')}".strip(', '),
            "postal_code": tags.get('addr:postcode', ""),
            "latitude": lat,
            "longitude": lon,
            "website": tags.get('website') or tags.get('contact:website', ""),
            "phone": tags.get('phone') or tags.get('contact:phone', ""),
            "email": tags.get('email') or tags.get('contact:email', ""),
            "instagram_url": tags.get('instagram') or tags.get('contact:instagram', ""),
            "facebook_url": tags.get('facebook') or tags.get('contact:facebook', ""),
            "menu_url": tags.get('menu', ""),
            "osm_type": element.get('type', 'node'),
            "osm_id": element.get('id'),
            "source_name": "OpenStreetMap",
            "discovery_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "verification_status": "Unverified"
        }

    def discover(self, city: str, categories: List[str],
                  progress_callback=None) -> Dict[str, Any]:
        """
        Main discovery method for a city.
        """
        if progress_callback:
            progress_callback(f"Starting discovery for {city}...")

        query = self._build_overpass_query(city, categories)

        if progress_callback:
            progress_callback(f"Querying OpenStreetMap for {city}...")

        data = self._fetch_from_overpass(query)
        if not data:
            return {"status": "error", "message": "Failed to fetch data from Overpass API"}

        elements = data.get('elements', [])
        total_found = len(elements)

        if progress_callback:
            progress_callback(f"Processing {total_found} results...")

        leads_to_insert = []
        for elem in elements:
            normalized = self._normalize_osm_data(elem)
            if normalized:
                normalized['city'] = city
                leads_to_insert.append(normalized)

        # Save to DB and track duplicates
        new_count = 0
        updated_count = 0
        duplicate_count = 0

        for lead in leads_to_insert:
            # Use a simple duplicate check here, a more robust one is in modules.deduplication
            existing = self.db.fetch_one(
                "SELECT lead_id FROM leads WHERE osm_id = ? AND osm_type = ?",
                (lead['osm_id'], lead['osm_type'])
            )

            if existing:
                # Update existing record safely
                self.db.update_lead(existing['lead_id'], lead)
                updated_count += 1
                duplicate_count += 1
            else:
                self.db.insert_lead(lead)
                new_count += 1

        # Record discovery job
        self.db.execute_query(
            "INSERT INTO discovery_jobs (city, category, started_at, completed_at, records_found, new_records, duplicates, source, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (city, ", ".join(categories), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'), total_found, new_count, duplicate_count, "OpenStreetMap", "Completed")
        )

        return {
            "status": "success",
            "total_found": total_found,
            "new_leads": new_count,
            "updated_leads": updated_count,
            "duplicates": duplicate_count,
            "city": city
        }
