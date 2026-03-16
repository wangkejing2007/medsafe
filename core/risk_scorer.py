from typing import List, Dict, Any
from medsafe.core.drug_database import DrugDatabase
from medsafe.core.molecular_analyzer import MolecularAnalyzer
from medsafe.core.cyp450_analyzer import CYP450Analyzer
from medsafe.config import settings

class RiskScorer:
    """綜合風險評分引擎"""

    def __init__(self):
        self.db = DrugDatabase()
        self.mol_analyzer = MolecularAnalyzer()
        self.cyp_analyzer = CYP450Analyzer()

    def calculate_interaction_risk(self, drug_a: str, drug_b: str) -> Dict[str, Any]:
        """計算兩藥物之間的綜合風險"""
        score = 0
        reasons = []
        
        # 1. 檢查已知交互作用
        known = self.db.get_known_interaction(drug_a, drug_b)
        if known:
            severity = known["severity"].lower()
            if severity == "major":
                score = max(score, 90)
            elif severity == "moderate":
                score = max(score, 60)
            reasons.append({
                "source": "known_database",
                "severity": severity,
                "description": known["effect"],
                "mechanism": known["mechanism"]
            })

        # 2. 檢查 CYP450 代謝衝突
        cyp_conflicts = self.cyp_analyzer.check_interaction(drug_a, drug_b)
        if cyp_conflicts:
            score = max(score, 50)
            for conflict in cyp_conflicts:
                reasons.append({
                    "source": "cyp450_analysis",
                    "severity": "moderate",
                    "description": conflict["mechanism"],
                    "mechanism": f"Metabolism conflict via {conflict['enzyme']}"
                })

        # 3. 檢查分子相似度 (AI/預測部分)
        smiles_a = self.mol_analyzer.get_smiles(drug_a)
        smiles_b = self.mol_analyzer.get_smiles(drug_b)
        if smiles_a and smiles_b:
            similarity = self.mol_analyzer.get_similarity(smiles_a, smiles_b)
            if similarity > 0.8:
                score = max(score, 40)
                reasons.append({
                    "source": "molecular_similarity",
                    "severity": "low",
                    "description": f"分子結構高度相似 (相似度: {similarity:.2f})，可能有藥效疊加風險",
                    "mechanism": f"Structural similarity: {similarity:.2f}"
                })

        # 判定分級
        if score > settings.RISK_YELLOW_MAX:
             level = "red"
             level_zh = "高風險"
        elif score > settings.RISK_GREEN_MAX:
             level = "yellow"
             level_zh = "中風險"
        else:
             level = "green"
             level_zh = "安全"

        return {
            "score": score,
            "level": level,
            "level_zh": level_zh,
            "reasons": reasons
        }

    def analyze_all(self, drug_list: List[str]) -> Dict[str, Any]:
        """分析整份藥藥單"""
        # 紀錄原始輸入與解析後的對應
        resolved_drugs = []
        for d in drug_list:
            generic = self.db.find_drug_name(d)
            resolved_drugs.append({
                "input": d,
                "generic": generic,
                "zh": self.db.get_zh_name(generic)
            })
            
        num_drugs = len(resolved_drugs)
        pair_results = []
        max_score = 0
        overall_level = "green"

        for i in range(num_drugs):
            for j in range(i + 1, num_drugs):
                drug_a_info = resolved_drugs[i]
                drug_b_info = resolved_drugs[j]
                
                res = self.calculate_interaction_risk(drug_a_info["generic"], drug_b_info["generic"])
                res["drug_a"] = drug_a_info["generic"]
                res["drug_b"] = drug_b_info["generic"]
                res["drug_a_zh"] = drug_a_info["zh"]
                res["drug_b_zh"] = drug_b_info["zh"]
                res["drug_a_input"] = drug_a_info["input"]
                res["drug_b_input"] = drug_b_info["input"]
                pair_results.append(res)
                
                if res["score"] > max_score:
                    max_score = res["score"]
                    overall_level = res["level"]

        return {
            "overall_level": overall_level,
            "overall_level_zh": "高風險" if overall_level == "red" else ("中風險" if overall_level == "yellow" else "安全"),
            "pair_results": pair_results,
            "num_drugs": num_drugs,
            "disclaimer": settings.DISCLAIMER
        }
