from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import json

app = FastAPI()

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/reconciliation")
def get_reconciliation_data():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(root_dir, 'data', 'financial_audit_results.csv')
    
    if not os.path.exists(csv_path):
        return {"error": "Reconciliation data not found. Please run the financial audit pipeline first."}
        
    try:
        df = pd.read_csv(csv_path)
        
        # Replace NaN/infinity with None to ensure valid JSON
        df = df.replace([pd.NA, pd.NaT, float('inf'), float('-inf')], None)
        df = df.where(pd.notnull(df), None)
        
        # Convert to dictionary format
        records = df.to_dict(orient="records")
        return records
    except Exception as e:
        return {"error": f"Failed to load data: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
