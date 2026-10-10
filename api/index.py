import os
import json
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# 1. Changed to "*" to explicitly allow the browser's preflight OPTIONS request
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"], 
    allow_headers=["*"],
)

class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

@app.post("/api/latency")
async def calculate_latency(payload: AnalyticsRequest):
    # 2. Safely resolve the file path relative to this script's actual location
    current_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(current_dir, '..', 'q-vercel-latency.json')
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"error": f"Data file not found at {file_path}"}
        
    results = {}
    
    for region in payload.regions:
            region_data = [d for d in data if d.get("region") == region]
            
            if not region_data:
                continue
                
            # Safely extract values only if the keys exist in the dictionary
            latencies = [d["latency"] for d in region_data if "latency" in d]
            uptimes = [d["uptime"] for d in region_data if "uptime" in d]
            
            # Avoid errors if the filtered lists are empty
            avg_latency = float(np.mean(latencies)) if latencies else 0.0
            p95_latency = float(np.percentile(latencies, 95)) if latencies else 0.0
            avg_uptime = float(np.mean(uptimes)) if uptimes else 0.0
            breaches = sum(1 for l in latencies if l > payload.threshold_ms)
            
            results[region] = {
                "avg_latency": avg_latency,
                "p95_latency": p95_latency,
                "avg_uptime": avg_uptime,
                "breaches": breaches
            }
        
    return results
