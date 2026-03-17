import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__name__)))

from core.ai_model import AIInteractionModel

def quick_check():
    print("Initializing AI Model...")
    model = AIInteractionModel()
    print("Model Initialized.")
    
    # Warfarin + Aspirin SMILES
    s1 = "CC(=O)OC1=CC=CC=C1C(=O)O"
    s2 = "CC(=O)CC(C1=CC=C(C=C1)O)C2=C(C3=CC=CC=C3OC2=O)O"
    
    print("Predicting Risk...")
    score, details = model.predict_risk(s1, s2)
    print(f"Score: {score}")
    print(f"Details: {details}")

if __name__ == "__main__":
    quick_check()
