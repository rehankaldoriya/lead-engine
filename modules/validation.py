import re
from typing import Optional

def validate_email(email: str) -> bool:
    if not email:
        return True  # Optional field
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    if not url:
        return True  # Optional field
    # Basic URL validation
    pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+.*$'
    return bool(re.match(pattern, url))

def validate_phone(phone: str) -> bool:
    if not phone:
        return True  # Optional field
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\(\)\-\+]', '', phone)
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15

def validate_coordinates(lat: float, lon: float) -> bool:
    if lat is None or lon is None:
        return True  # Optional
    return -90 <= lat <= 90 and -180 <= lon <= 180
