import json
import os
from typing import List, Dict, Any, Optional

class CYP450Analyzer:
    """CYP450 代謝途徑分析模組"""

    def __init__(self):
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cyp450_substrates.json")
        with open(data_path, "r", encoding="utf-8") as f:
            self.cyp_data = json.load(f)

    def get_drug_role(self, drug_name: str) -> Dict[str, List[str]]:
        """獲取藥物在各個 CYP 酶中的角色 (substrate, inhibitor, inducer)"""
        roles = {
            "substrate_of": [],
            "inhibitor_of": [],
            "inducer_of": []
        }
        
        for enzyme, data in self.cyp_data.items():
            if any(s["name"].lower() == drug_name.lower() for s in data["substrates"]):
                roles["substrate_of"].append(enzyme)
            if any(i["name"].lower() == drug_name.lower() for i in data["inhibitors"]):
                roles["inhibitor_of"].append(enzyme)
            if any(ind["name"].lower() == drug_name.lower() for ind in data["inducers"]):
                roles["inducer_of"].append(enzyme)
                
        return roles

    def check_interaction(self, drug_a: str, drug_b: str) -> List[Dict[str, Any]]:
        """檢查兩藥物間的 CYP 代謝衝突"""
        interactions = []
        role_a = self.get_drug_role(drug_a)
        role_b = self.get_drug_role(drug_b)
        
        # 檢查 A 是否抑制/誘導 B 的代謝酶
        for enzyme in role_b["substrate_of"]:
            if enzyme in role_a["inhibitor_of"]:
                interactions.append({
                    "enzyme": enzyme,
                    "mechanism": f"{drug_a} 抑制 {enzyme}，可能減慢 {drug_b} 的代謝",
                    "type": "inhibition"
                })
            if enzyme in role_a["inducer_of"]:
                interactions.append({
                    "enzyme": enzyme,
                    "mechanism": f"{drug_a} 誘導 {enzyme}，可能加速 {drug_b} 的代謝",
                    "type": "induction"
                })
                
        # 檢查 B 是否抑制/誘導 A 的代謝酶
        for enzyme in role_a["substrate_of"]:
            if enzyme in role_b["inhibitor_of"]:
                interactions.append({
                    "enzyme": enzyme,
                    "mechanism": f"{drug_b} 抑制 {enzyme}，可能減慢 {drug_a} 的代謝",
                    "type": "inhibition"
                })
            if enzyme in role_b["inducer_of"]:
                interactions.append({
                    "enzyme": enzyme,
                    "mechanism": f"{drug_b} 誘導 {enzyme}，可能加速 {drug_a} 的代謝",
                    "type": "induction"
                })
                
        return interactions
