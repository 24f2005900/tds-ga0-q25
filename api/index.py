import os
import json
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Enable CORS for all origins (Required by the assignment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

@app.post("/api/latency")
async def calculate_latency(payload: AnalyticsRequest):
    # Vercel copies the root files to the runtime environment
    # Use a relative path from the current working directory
    file_path = os.path.join(os.getcwd(), 'q-vercel-latency.json')

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"error": "Data file not found."}

    results = {}

    for region in payload.regions:
        region_data = [d for d in data if d.get("region") == region]

        if not region_data:
            continue

        latencies = [d["latency"] for d in region_data]
        uptimes = [d["uptime"] for d in region_data]

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for l in latencies if l > payload.threshold_ms)

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return results
