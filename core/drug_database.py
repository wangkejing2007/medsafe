import json
import os
from typing import List, Dict, Optional
from medsafe.config import settings

class DrugDatabase:
    """藥物資料庫模組：管理藥物基本資訊與交互作用資料"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.cyp_data = self._load_json("cyp450_substrates.json")
        self.aliases = self._load_json("drug_aliases_tw.json")
        self.known_interactions = self._load_json("known_interactions.json")

    def _load_json(self, filename: str) -> Dict:
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def find_drug_name(self, query: str) -> str:
        """根據查詢字串（中英文、品牌名）尋找標準成分名（Generic Name）"""
        query_lower = query.strip().lower()
        
        # 1. 直接匹配英文名
        for name in self.aliases.keys():
            if name.lower() == query_lower:
                return name
        
        # 2. 搜尋別名（中文名、品牌名）
        for name, aliases in self.aliases.items():
            for alias in aliases:
                if alias.lower() == query_lower:
                    return name
        
        # 3. 若找不到，回傳原字串（可能不在本地資料庫中）
        return query

    def get_zh_name(self, name: str) -> str:
        """獲取藥物的中文名稱"""
        aliases = self.aliases.get(name, [])
        return aliases[0] if aliases else name

    def get_known_interaction(self, drug_a: str, drug_b: str) -> Optional[Dict]:
        """查詢兩藥物之間已知的交互作用"""
        a, b = drug_a.lower(), drug_b.lower()
        for item in self.known_interactions:
            ia = item["drug_a"].lower()
            ib = item["drug_b"].lower()
            if (ia == a and ib == b) or (ia == b and ib == a):
                return item
        return None
