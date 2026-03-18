from fastapi import APIRouter, HTTPException
from typing import List
import json
from pydantic import BaseModel
from core.risk_scorer import RiskScorer
from core.drug_database import DrugDatabase
from core.molecular_analyzer import MolecularAnalyzer
from core.openfda_client import OpenFDAClient
from core.mcp_client import client as mcp_client

router = APIRouter()
scorer = RiskScorer()
db = DrugDatabase()
mol_analyzer = MolecularAnalyzer()
fda_client = OpenFDAClient()

class AnalysisRequest(BaseModel):
    drugs: List[str]

class HealthFoodCheckRequest(BaseModel):
    drugs: List[str]
    health_foods: List[str]

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

    # 3. Enhanced TFDA Search via MCP (Async)
    try:
        tfda_res = await mcp_client.search_tfda_drug(query)
        if tfda_res and tfda_res.content:
            text = tfda_res.content[0].text
            try:
                data = json.loads(text)
                if data and "results" in data and len(data["results"]) > 0:
                    top_match = data["results"][0]
                    # 優先使用 TFDA 的資料
                    std_name = top_match.get("name_en", std_name)
                    zh_name = top_match.get("name_zh", zh_name)
                    source = "TFDA (MCP)"
            except json.JSONDecodeError:
                # If not JSON, it might be a plain string from TFDA search
                # We can try to extract name if it follows a pattern, but for now just skip
                pass
    except Exception as e:
        print(f"MCP Search Error: {e}")

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

@router.post("/mcp/health-food-check")
async def check_health_food(request: HealthFoodCheckRequest):
    """檢查用藥清單與健康食品的衝突"""
    try:
        # res 是一個列表，包含多個 MCP 工具的回傳結果
        raw_results = await mcp_client.check_health_food_conflict(request.drugs, request.health_foods)
        processed_results = []
        for r in raw_results:
            if r and r.content:
                text = r.content[0].text
                try:
                    processed_results.append(json.loads(text))
                except json.JSONDecodeError:
                    processed_results.append({"raw_text": text})
        return {"results": processed_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate")
async def validate_drug(query: str):
    """Check if a drug exists in our database."""
    std_name = db.find_drug_name(query)
    return {"exists": std_name is not None, "standard_name": std_name}
