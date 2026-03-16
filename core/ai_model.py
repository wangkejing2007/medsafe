import numpy as np
import os
from typing import Dict, Any, List, Tuple
from medsafe.core.molecular_analyzer import MolecularAnalyzer

class AIInteractionModel:
    """
    自研輕量化 AI 藥物交互作用預測模型
    使用分子描述子作為特徵，預測潛在風險，並提供模擬的 SHAP 可解釋性分析。
    """

    def __init__(self):
        self.analyzer = MolecularAnalyzer()
        self.feature_names = ['mw', 'logp', 'h_donors', 'h_acceptors', 'tpsa', 'rotatable_bonds', 'lipinski_violations']
        # 定義特徵權重 (模擬訓練好的模型權重)
        self.weights = {
            'mw': 0.05,
            'logp': 10.0,
            'h_donors': 2.0,
            'h_acceptors': 1.0,
            'tpsa': 0.1,
            'rotatable_bonds': 0.5,
            'lipinski_violations': 20.0
        }
        self.base_value = 25.0

    def predict_risk(self, drug_a_smiles: str, drug_b_smiles: str) -> Tuple[float, Dict[str, Any]]:
        """
        預測兩藥物交互作用機率
        回傳: (機率分數, SHAP 解釋數據)
        """
        feat_a = self.analyzer.analyze_molecule(drug_a_smiles)
        feat_b = self.analyzer.analyze_molecule(drug_b_smiles)
        
        if "error" in feat_a or "error" in feat_b:
            return 0.0, {}

        # 計算合併特徵 (均值)
        combined_feat = {}
        for f in self.feature_names:
            combined_feat[f] = (feat_a[f] + feat_b[f]) / 2
            
        # 計算風險分數 (加權求和)
        raw_score = self.base_value
        shap_contributions = []
        
        for f, w in self.weights.items():
            # 這裡簡單模擬 SHAP：特徵值 * 權重 - 某個偏移量
            contribution = (combined_feat[f] * w) * 0.1  # 縮放貢獻度
            raw_score += contribution
            
            shap_contributions.append({
                "feature": f,
                "contribution": round(float(contribution), 2),
                "impact": "正向增加風險" if contribution > 0 else "負向降低風險"
            })
            
        risk_score = np.clip(raw_score, 0, 100)
        
        # 排序前三大貢獻特徵
        shap_contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        
        return float(risk_score), {
            "score": round(float(risk_score), 2),
            "shap_summary": shap_contributions[:3],
            "base_value": round(float(self.base_value), 2)
        }
