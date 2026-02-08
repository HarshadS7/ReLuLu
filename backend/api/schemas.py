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
    obligations_after: list[list[float]]


class AnalystResponse(BaseModel):
    risk_assessment: str
    status: str


class BacktestMetrics(BaseModel):
    mae: float | None
    directional_accuracy: float | None
    correlation: float | None


class BacktestAggregate(BaseModel):
    total_days: int
    avg_mae: float | None
    avg_directional_accuracy: float | None
    best_day: str | None
    worst_day: str | None


class BacktestResponse(BaseModel):
    aggregate: BacktestAggregate
    results: list[dict]
    timestamp: str


class AlertConfig(BaseModel):
    id: str
    type: str
    name: str
    description: str
    threshold: float
    enabled: bool
    created_at: str


class AlertTriggered(BaseModel):
    id: str
    type: str
    name: str
    message: str
    triggered_at: str
    current_value: float | None


class AlertCreateRequest(BaseModel):
    type: str
    name: str
    threshold: float
    description: str = ""
    enabled: bool = True
