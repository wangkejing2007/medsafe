from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from medsafe.core.risk_scorer import RiskScorer
from medsafe.core.drug_database import DrugDatabase
from medsafe.core.molecular_analyzer import MolecularAnalyzer

router = APIRouter()
scorer = RiskScorer()
db = DrugDatabase()
mol_analyzer = MolecularAnalyzer()

class AnalysisRequest(BaseModel):
    drugs: List[str]

class DrugSearchQuery(BaseModel):
    query: str

@router.post("/analyze")
async def analyze_drugs(request: AnalysisRequest):
    if not request.drugs:
        raise HTTPException(status_code=400, detail="Drug list cannot be empty")
    
    results = scorer.analyze_all(request.drugs)
    return results

@router.get("/drug/search")
async def search_drug(query: str):
    std_name = db.find_drug_name(query)
    zh_name = db.get_zh_name(std_name)
    smiles = mol_analyzer.get_smiles(std_name)
    
    mol_info = {}
    if smiles:
        mol_info = mol_analyzer.analyze_molecule(smiles)
        
    return {
        "query": query,
        "generic_name": std_name,
        "zh_name": zh_name,
        "smiles": smiles,
        "molecular_info": mol_info
    }
