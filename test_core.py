import sys
import os

# 將專案根目錄的父目錄加入路徑，以便 import medsafe
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from medsafe.core.risk_scorer import RiskScorer

def test_analysis():
    print("=== MedSafe Core Engine Verification Test ===")
    scorer = RiskScorer()
    
    # 測試案例：阿布昔替尼 (Abrocitinib) + 妥舒平 (Doxepin) + 艾來 (Fexofenadine)
    test_drugs = ["Abrocitinib", "Doxepin", "Fexofenadine"]
    print(f"測試藥物: {', '.join(test_drugs)}")
    
    results = scorer.analyze_all(test_drugs)
    
    print(f"\n綜合風險等級: {results['overall_level_zh']} ({results['overall_level']})")
    print(f"交互作用配對數: {len(results['pair_results'])}")
    
    for res in results['pair_results']:
        print(f"\n[ 配對: {res['drug_a_zh']} + {res['drug_b_zh']} ]")
        print(f"風險分數: {res['score']}")
        print(f"風險等級: {res['level_zh']}")
        for reason in res['reasons']:
            print(f"- 來源: {reason['source']}")
            print(f"- 描述: {reason['description']}")
            print(f"- 機制: {reason['mechanism']}")
            if "ai_details" in reason:
                details = reason["ai_details"]
                print(f"  [AI 詳情] 分數: {details['score']}, 基準值: {details['base_value']}")
                print(f"  [SHAP 分析] 貢獻特徵: {', '.join([f'{d['feature']}({d['contribution']})' for d in details['shap_summary']])}")

if __name__ == "__main__":
    test_analysis()
