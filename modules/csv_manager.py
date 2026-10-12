import pandas as pd
import os
from typing import List, Dict, Any, Tuple
from modules.database import DatabaseManager
from modules.validation import validate_email, validate_url, validate_phone

class CSVManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.template_path = "templates/lead_import_template.csv"

    def create_template(self) -> str:
        """Creates a sample CSV template with fake examples."""
        headers = [
            "business_name", "city", "category", "area", "full_address",
            "website", "phone", "email", "instagram_url", "facebook_url",
            "menu_url", "source"
        ]

        data = [
            ["Sample Café One", "Ahmedabad", "Café", "Bodakdev", "123 Main St", "http://example.com/cafe1", "+91 98765 43210", "info@cafe1.com", "http://instagram.com/cafe1", "", "", "Manual Entry"],
            ["Example Restaurant Two", "Gandhinagar", "Restaurant", "Sector 11", "456 High St", "http://example.com/rest2", "+91 98765 43211", "contact@rest2.com", "http://instagram.com/rest2", "", "http://menu.com/rest2", "External List"]
        ]

        df = pd.DataFrame(data, columns=headers)
        os.makedirs(os.path.dirname(self.template_path), exist_ok=True)
        df.to_csv(self.template_path, index=False)
        return self.template_path

    def map_columns(self, df_columns: List[str]) -> Dict[str, str]:
        """Maps common CSV column aliases to database fields."""
        mapping_dict = {
            "name": "business_name",
            "restaurant": "business_name",
            "business": "business_name",
            "phone_number": "phone",
            "mobile": "phone",
            "url": "website",
            "site": "website",
            "location": "full_address",
            "neighbourhood": "area",
            "instagram": "instagram_url",
            "email_address": "email"
        }

        final_mapping = {}
        for col in df_columns:
            col_lower = col.lower().strip()
            if col_lower in mapping_dict:
                final_mapping[col] = mapping_dict[col_lower]
            elif col_lower == "city":
                final_mapping[col] = "city"
            elif col_lower == "category":
                final_mapping[col] = "business_category"
            # Add other direct mappings as needed

        return final_mapping

    def parse_csv(self, file_path: str) -> Tuple[pd.DataFrame, List[str]]:
        """Parses CSV and returns a normalized dataframe and a list of errors."""
        try:
            df = pd.read_csv(file_path)
            errors = []

            # Basic validation: check for required fields
            cols_lower = [c.lower().strip() for c in df.columns]
            has_name = any(c in cols_lower for c in ["name", "business_name", "restaurant", "business"])
            has_city = "city" in cols_lower

            if not has_name:
                errors.append("Missing business name column.")
            if not has_city:
                errors.append("Missing city column.")

            return df, errors
        except Exception as e:
            return pd.DataFrame(), [f"File read error: {str(e)}"]

    def analyze_import(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Analyzes the dataframe for duplicates and invalid records."""
        normalized_data = []
        for _, row in df.iterrows():
            record = {}
            for csv_col, db_col in mapping.items():
                record[db_col] = row[csv_col]
            normalized_data.append(record)

        normalized_df = pd.DataFrame(normalized_data)

        results = {
            "total": len(normalized_df),
            "new": 0,
            "updates": 0,
            "duplicates": 0,
            "invalid": 0,
            "conflicts": 0,
            "preview": normalized_df.head(10).to_dict('records')
        }

        for _, record in normalized_df.iterrows():
            # Basic validation
            if not record.get('business_name') or not record.get('city'):
                results["invalid"] += 1
                continue

            # Duplicate check (simple version for now)
            # In real implementation, this should call modules.deduplication
            existing = self.db.fetch_one(
                "SELECT lead_id FROM leads WHERE business_name = ? AND city = ?",
                (record['business_name'], record['city'])
            )

            if existing:
                results["updates"] += 1
            else:
                results["new"] += 1

        return results

    def safe_import(self, df: pd.DataFrame, mapping: Dict[str, str]):
        """Imports data using safe update logic."""
        normalized_data = []
        for _, row in df.iterrows():
            record = {}
            for csv_col, db_col in mapping.items():
                record[db_col] = row[csv_col]
            normalized_data.append(record)

        imported_count = 0
        updated_count = 0

        for record in normalized_data:
            if not record.get('business_name') or not record.get('city'):
                continue

            existing = self.db.fetch_one(
                "SELECT * FROM leads WHERE business_name = ? AND city = ?",
                (record['business_name'], record['city'])
            )

            if existing:
                # Safe update: only update if value is provided and existing is empty
                # or if it's a verified value (simplified here)
                update_payload = {}
                for key, value in record.items():
                    if value and (not existing[key] or existing[key] == ''):
                        update_payload[key] = value

                if update_payload:
                    self.db.update_lead(existing['lead_id'], update_payload)
                    updated_count += 1
            else:
                self.db.insert_lead(record)
                imported_count += 1

        return imported_count, updated_count

    def export_leads(self, leads: List[Dict[str, Any]], output_path: str):
        """Exports lead data to CSV."""
        if not leads:
            return
        df = pd.DataFrame(leads)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
