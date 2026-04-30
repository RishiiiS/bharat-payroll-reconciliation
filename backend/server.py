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
        
        # Merge worker_name from workers CSV
        import glob
        workers_files = glob.glob(os.path.join(root_dir, 'data', 'workers*.csv'))
        if workers_files:
            workers_df = pd.read_csv(workers_files[0])
            if 'worker_id' in workers_df.columns and 'name' in workers_df.columns:
                df = df.merge(workers_df[['worker_id', 'name']], on='worker_id', how='left')
        
        # Convert to object to safely hold None instead of NaN
        df = df.astype(object)
        df = df.where(pd.notnull(df), None)
        
        # Convert to dictionary format
        records = df.to_dict(orient="records")
        return records
    except Exception as e:
        return {"error": f"Failed to load data: {str(e)}"}

@app.get("/worker/{worker_id}/shifts")
def get_worker_shifts(worker_id: str):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(root_dir, 'data', 'shift_level_expected_pay.csv')
    
    if not os.path.exists(csv_path):
        return {"error": "Shift level data not found. Please run the financial audit pipeline first."}
        
    try:
        df = pd.read_csv(csv_path)
        
        # Filter by worker_id
        worker_shifts = df[df['worker_id'] == worker_id].copy()
        
        # Convert to object to safely hold None instead of NaN
        worker_shifts = worker_shifts.astype(object)
        worker_shifts = worker_shifts.where(pd.notnull(worker_shifts), None)
        
        records = worker_shifts.to_dict(orient="records")
        return records
    except Exception as e:
        return {"error": f"Failed to load shift data: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
