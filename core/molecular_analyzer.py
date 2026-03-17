from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem, Draw
import os
from typing import Dict, Any, Optional

class MolecularAnalyzer:
    """RDKit 分子分析引擎：計算分子描述子與指紋"""

    def __init__(self):
        # 簡易 SMILES 資料庫（實際應用中應從 API 或大型資料庫獲取）
        self.smiles_db = {
            "Abrocitinib": "CCS(=O)(=O)N1CC(C1)(CC2=NC=C(N2)C3=C4C=CNC4=NC=N3)NC",
            "Doxepin": "CN(C)CC=C1C2=CC=CC=C2OCC3=CC=CC=C31",
            "Fexofenadine": "CC(C)(C1=CC=C(C=C1)C(C2=CC=CC=C2)(C3=CC=CC=C3)O)CCN4CCC(CC4)C(C5=CC=CC=C5)(C6=CC=CC=C6)O",
            "Warfarin": "CC(=O)CC(C1=CC=C(C=C1)O)C2=C(C3=CC=CC=C3OC2=O)O", # Simplified
            "Aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
            "Acetaminophen": "CC(=O)NC1=CC=C(C=C1)O",
            "Ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
            "Naproxen": "CC(C1=CC2=C(C=C1)C=C(C=C2)OC)C(=O)O",
            "Omeprazole": "CC1=CN=C(C(=C1OC)C)CS(=O)C2=NC3=C(N2)C=C(C=C3)OC"
        }

    def get_smiles(self, drug_name: str) -> Optional[str]:
        return self.smiles_db.get(drug_name)

    def analyze_molecule(self, smiles: str) -> Dict[str, Any]:
        """分析 SMILES 結構並回傳物理化學屬性"""
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return {"error": "Invalid SMILES"}

        analysis = {
            "mw": round(Descriptors.MolWt(mol), 2),
            "logp": round(Descriptors.MolLogP(mol), 2),
            "h_donors": Descriptors.NumHDonors(mol),
            "h_acceptors": Descriptors.NumHAcceptors(mol),
            "tpsa": round(Descriptors.TPSA(mol), 2),
            "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
            "heavy_atoms": mol.GetNumHeavyAtoms(),
            "rings": Descriptors.RingCount(mol)
        }
        
        # Lipinski Rule of 5 check
        analysis["lipinski_violations"] = sum([
            analysis["mw"] > 500,
            analysis["logp"] > 5,
            analysis["h_donors"] > 5,
            analysis["h_acceptors"] > 10
        ])
        
        return analysis

    def get_similarity(self, smiles1: str, smiles2: str) -> float:
        """計算兩個分子之間的 Tanimoto 相似度"""
        mol1 = Chem.MolFromSmiles(smiles1)
        mol2 = Chem.MolFromSmiles(smiles2)
        if not mol1 or not mol2:
            return 0.0
            
        fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, 2, nBits=2048)
        fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, 2, nBits=2048)
        
        from rdkit import DataStructs
        return DataStructs.TanimotoSimilarity(fp1, fp2)

    def save_molecule_image(self, smiles: str, filename: str, output_dir: str):
        """生成分子結構圖"""
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            path = os.path.join(output_dir, filename)
            Draw.MolToFile(mol, path, size=(300, 300))
            return path
        return None
