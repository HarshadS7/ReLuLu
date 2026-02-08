"""
Pydantic response schemas for the REST API.
"""

from pydantic import BaseModel


class BankResult(BaseModel):
    name: str
    predicted_score: float
    hub_score: float
    risk_factor: float


class EdgeResult(BaseModel):
    source: str
    target: str
    weight_before: float
    weight_after: float


class HorizonSnapshot(BaseModel):
    horizon: int
    banks: list[BankResult]
    edges_before: list[EdgeResult]
    edges_after: list[EdgeResult]
    stability: float
    is_stable: bool
    payload_reduction: float
    raw_load: float
    net_load: float
    risk_buffer: float
    risk_adjusted_net_load: float
    risk_adjusted_payload_reduction: float
    worst_case_buffer: float
    worst_case_net_load: float
    worst_case_payload_reduction: float
    obligations_before: list[list[float]]
    obligations_after: list[list[float]]


class DataMeta(BaseModel):
    tickers: list[str]
    num_banks: int
    total_days: int
    date_range: list[str]
    last_updated: str
    model_type: str


class ForecastResponse(BaseModel):
    """Top-level response with per-horizon snapshots + data metadata."""
    horizons: list[HorizonSnapshot]
    metadata: DataMeta


class PipelineResponse(BaseModel):
    """Legacy single-snapshot response (backward compat)."""
    banks: list[BankResult]
    edges_before: list[EdgeResult]
    edges_after: list[EdgeResult]
    stability: float
    is_stable: bool
    payload_reduction: float
    raw_load: float
    net_load: float
    risk_buffer: float
    risk_adjusted_net_load: float
    risk_adjusted_payload_reduction: float
    worst_case_buffer: float
    worst_case_net_load: float
    worst_case_payload_reduction: float
    obligations_before: list[list[float]]
    obligations_after: list[list[float]]
