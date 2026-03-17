import requests
import json

url = "http://localhost:8001/api/analyze"
payload = {
    "drugs": ["Aspirin", "Warfarin"]
}
try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    data = response.json()
    interactions = data.get("pair_results", [])
    if interactions:
        print("Interactions found.")
        first = interactions[0]
        ai_found = False
        for reason in first.get("reasons", []):
            if "ai_details" in reason:
                print("SUCCESS: Found ai_details in response!")
                print(json.dumps(reason["ai_details"], indent=2, ensure_ascii=False))
                ai_found = True
                break
        if not ai_found:
            print("FAILURE: No ai_details found in reasons.")
    else:
        print("No interactions found.")
except Exception as e:
    print(f"Error: {e}")
