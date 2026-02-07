"""
FastAPI server that exposes the FinancialOptimizationEngine to the frontend.
Run: python api.py
"""
import os
import sys
import torch
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure imports resolve relative to this file's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from engine import FinancialOptimizationEngine

# --- App Setup ---
app = FastAPI(title="ReLuLu Financial Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load model once at startup ---
BANK_NAMES = ["JPM", "BAC", "WFC", "C", "USB", "GS", "MS"]
NUM_BANKS = len(BANK_NAMES)
SEQ_LEN = 10
MODEL_PATH = "super_node_v1.pth"

engine: FinancialOptimizationEngine | None = None


@app.on_event("startup")
def load_engine():
    global engine
    model = FinancialOptimizationEngine.load_gnn_model(
        MODEL_PATH, node_features=2, hidden_dim=32
    )
    engine = FinancialOptimizationEngine(model)
    print(f"Engine loaded with model from {MODEL_PATH}")


# --- Response Schema ---
class BankResult(BaseModel):
    name: str
    predicted_score: float
    hub_score: float


class EdgeResult(BaseModel):
    source: str
    target: str
    weight_before: float
    weight_after: float


class PipelineResponse(BaseModel):
    banks: list[BankResult]
    edges_before: list[EdgeResult]
    edges_after: list[EdgeResult]
    stability: float
    is_stable: bool
    payload_reduction: float
    raw_load: float
    net_load: float
    obligations_before: list[list[float]]
    obligations_after: list[list[float]]


# --- Routes ---
@app.get("/api/run", response_model=PipelineResponse)
def run_pipeline():
    """
    Runs the full GNN → Risk → Netting pipeline with synthetic inputs
    and returns structured results for the frontend dashboard.
    """
    # Generate synthetic inputs (same as test_engine.py)
    x_window = torch.randn(NUM_BANKS, SEQ_LEN, 2)

    edges = []
    for i in range(NUM_BANKS):
        edges.append([i, (i + 1) % NUM_BANKS])
        edges.append([(i + 1) % NUM_BANKS, i])
        if i < NUM_BANKS - 2:
            edges.append([i, i + 2])
            edges.append([i + 2, i])
    edge_index = torch.tensor(edges, dtype=torch.long).T

    liquidity = torch.abs(torch.randn(NUM_BANKS)) * 100 + 50
    base_obligations = torch.abs(torch.randn(NUM_BANKS, NUM_BANKS)) * 10
    base_obligations.fill_diagonal_(0)

    # Run the engine
    result = engine.run_pipeline(x_window, edge_index, liquidity, base_obligations)

    # Format bank-level results
    banks = []
    for i, name in enumerate(BANK_NAMES):
        banks.append(BankResult(
            name=name,
            predicted_score=round(float(result["predicted_node_scores"][i]), 6),
            hub_score=round(float(result["systemic_hubs"][i]), 4),
        ))

    # Format edges (before & after netting) — only include non-trivial edges
    ob_before = result["obligations_before"]
    ob_after = result["obligations_to_ccp"]

    edges_before = []
    edges_after = []
    for i in range(NUM_BANKS):
        for j in range(NUM_BANKS):
            if i == j:
                continue
            w_before = float(ob_before[i][j])
            w_after = float(ob_after[i][j])
            if w_before > 0.01:
                edges_before.append(EdgeResult(
                    source=BANK_NAMES[i],
                    target=BANK_NAMES[j],
                    weight_before=round(w_before, 4),
                    weight_after=round(w_after, 4),
                ))
            if w_after > 0.01:
                edges_after.append(EdgeResult(
                    source=BANK_NAMES[i],
                    target=BANK_NAMES[j],
                    weight_before=round(w_before, 4),
                    weight_after=round(w_after, 4),
                ))

    return PipelineResponse(
        banks=banks,
        edges_before=edges_before,
        edges_after=edges_after,
        stability=round(result["stability"], 6),
        is_stable=result["stability"] < 1.0,
        payload_reduction=round(result["payload_reduction"], 2),
        raw_load=round(result["raw_load"], 2),
        net_load=round(result["net_load"], 2),
        obligations_before=[[round(float(v), 4) for v in row] for row in ob_before],
        obligations_after=[[round(float(v), 4) for v in row] for row in ob_after],
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": engine is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
