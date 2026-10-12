import requests
from typing import Optional

def fetch_public_website(url: str) -> Optional[str]:
    """
    Fetches the content of a public website for research.
    """
    try:
        headers = {
            'User-Agent': 'ALOREX-Lead-Engine/1.0 (Business Research Tool)'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text[:10000] # Return first 10k characters for analysis
        return None
    except Exception:
        return None
