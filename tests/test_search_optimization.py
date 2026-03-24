import sqlite3
import os
import json
import sys

# Add src to path if needed (assuming test is in tests/)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "mcp_server", "src"))
from drug_service import DrugService

def setup_test_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS licenses")
    cursor.execute("""
        CREATE TABLE licenses (
            license_id TEXT,
            name_zh TEXT,
            name_en TEXT,
            indication TEXT,
            category TEXT
        )
    """)
    
    # Mock Data
    data = [
        ("ID1", "普拿疼加強錠", "Panadol Extra", "退燒、止痛", "醫師藥師藥劑生指示藥品"),
        ("ID2", "乙醯胺酚錠", "Acetaminophen Tablets", "退燒、解除頭痛", "醫師處方用藥"),
        ("ID3", "止痛藥 A", "Pain Reliever A", "含有普拿疼成分可用於退燒", "指示藥品"),
        ("ID4", "阿斯匹靈", "Aspirin", "頭痛、肌肉發炎（與普拿疼不同）", "指示藥品"),
    ]
    cursor.executemany("INSERT INTO licenses VALUES (?, ?, ?, ?, ?)", data)
    conn.commit()
    conn.close()

def test_optimization():
    db_path = "test_drugs.db"
    setup_test_db(db_path)
    
    # Initialize DrugService with local data dir
    service = DrugService(os.getcwd())
    service.db_path = db_path # Override for testing
    
    print("\n--- Test 1: Search 'Panadol' (Literal Match) ---")
    res1 = json.loads(service.search_drug("Panadol"))
    for r in res1.get("results", []):
        print(f"[{r['relevance']} pts] {r['name_en']} ({r['name_zh']}) - Indication: {r['indication'][:20]}...")

    print("\n--- Test 2: Search '普拿疼' (Chinese Literal) ---")
    res2 = json.loads(service.search_drug("普拿疼"))
    for r in res2.get("results", []):
        print(f"[{r['relevance']} pts] {r['name_en']} ({r['name_zh']})")

    print("\n--- Test 3: Search 'Panadol' with Generic 'Acetaminophen' (The Optimization) ---")
    res3 = json.loads(service.search_drug("Panadol", generic_name="Acetaminophen"))
    for r in res3.get("results", []):
        print(f"[{r['relevance']} pts] {r['name_en']} ({r['name_zh']})")

    # Clean up
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_optimization()
