import requests
import logging

logger = logging.getLogger(__name__)

class OpenFDAClient:
    """
    Client for interacting with the OpenFDA API to fetch drug label information.
    """
    BASE_URL = "https://api.fda.gov/drug/label.json"

    def __init__(self, api_key=None):
        self.api_key = api_key

    def search_drug(self, name: str):
        """
        Search for a drug by its generic name or brand name using OpenFDA.
        Returns a dictionary with standard names if found, else None.
        """
        params = {
            "search": f'openfda.generic_name:"{name}" openfda.brand_name:"{name}"',
            "limit": 1
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                openfda = result.get("openfda", {})
                
                # Extract best names
                generic_names = openfda.get("generic_name", [])
                brand_names = openfda.get("brand_name", [])
                
                canonical_name = generic_names[0] if generic_names else (brand_names[0] if brand_names else name)
                
                return {
                    "generic_name": canonical_name,
                    "brand_names": brand_names,
                    "source": "OpenFDA"
                }
        except Exception as e:
            logger.error(f"OpenFDA search error for {name}: {e}")
            
        return None
