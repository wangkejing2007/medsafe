from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from core.risk_scorer import RiskScorer
from core.drug_database import DrugDatabase
from core.molecular_analyzer import MolecularAnalyzer
from core.openfda_client import OpenFDAClient

router = APIRouter()
scorer = RiskScorer()
db = DrugDatabase()
mol_analyzer = MolecularAnalyzer()
fda_client = OpenFDAClient()

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
    # 1. Try Local Database
    std_name = db.find_drug_name(query)
    zh_name = None
    source = "Local"

    if not std_name:
        # 2. Fallback to OpenFDA
        fda_res = fda_client.search_drug(query)
        if fda_res:
            std_name = fda_res["generic_name"]
            source = "OpenFDA"
            # Attempt to see if we have a ZH name for the FDA generic name locally
            zh_name = db.get_zh_name(std_name)
            if zh_name == std_name:
                zh_name = f"{std_name} (FDA)"
    else:
        zh_name = db.get_zh_name(std_name)

    smiles = mol_analyzer.get_smiles(std_name) if std_name else None
    
    mol_info = {}
    if smiles:
        mol_info = mol_analyzer.analyze_molecule(smiles)
        
    return {
        "query": query,
        "generic_name": std_name,
        "zh_name": zh_name,
        "smiles": smiles,
        "molecular_info": mol_info,
        "source": source
    }

@router.get("/validate")
async def validate_drug(query: str):
    """Check if a drug exists in our database."""
    std_name = db.find_drug_name(query)
    return {"exists": std_name is not None, "standard_name": std_name}
