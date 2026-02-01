from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import json
import os

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load data once at startup
DATA_PATH = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
with open(DATA_PATH, "r") as f:
    df = pd.DataFrame(json.load(f))

@app.get("/api")
def get_students(class_list: Optional[List[str]] = Query(None, alias="class")):
    """
    Returns student data. Supports multiple ?class= params.
    """
    # If ?class= is provided in the URL
    if class_list:
        # Filter the dataframe for any class in the list
        filtered_df = df[df["class"].isin(class_list)]
    else:
        # If no query param, return everyone
        filtered_df = df

    # Convert to the exact JSON format requested
    # to_dict('records') maintains the original CSV row order
    return {"students": filtered_df.to_dict(orient="records")}

@app.post("/api/latency")
async def get_latency_metrics(payload: dict = Body(...)):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 0)
    
    results = {}
    for region in regions:
        # Filter data for the specific region
        region_df = df[df['region'] == region]
        
        if region_df.empty:
            continue
            
        # Calculate metrics
        avg_latency = float(region_df['latency_ms'].mean())
        p95_latency = float(np.percentile(region_df['latency_ms'], 95))
        avg_uptime = float(region_df['uptime_pct'].mean())
        breaches = int((region_df['latency_ms'] > threshold).sum())
        
        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }
    
    return results