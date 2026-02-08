// =====================================================================
// Types — matches the /api/forecast schema
// =====================================================================
export interface BankResult {
  name: string;
  predicted_score: number;
  hub_score: number;
  risk_factor: number;
}

export interface EdgeResult {
  source: string;
  target: string;
  weight_before: number;
  weight_after: number;
}

export interface HorizonSnapshot {
  horizon: number;
  banks: BankResult[];
  edges_before: EdgeResult[];
  edges_after: EdgeResult[];
  stability: number;
  is_stable: boolean;
  payload_reduction: number;
  raw_load: number;
  net_load: number;
  risk_buffer: number;
  risk_adjusted_net_load: number;
  risk_adjusted_payload_reduction: number;
  worst_case_buffer: number;
  worst_case_net_load: number;
  worst_case_payload_reduction: number;
  obligations_before: number[][];
  obligations_after: number[][];
}

export interface DataMeta {
  tickers: string[];
  num_banks: number;
  total_days: number;
  date_range: string[];
  last_updated: string;
  model_type: string;
}

export interface ForecastResponse {
  horizons: HorizonSnapshot[];
  metadata: DataMeta;
}

export interface TickStatus {
  tick_count: number;
  last_data_refresh: string;
  last_forecast_time: string;
  ticker_active: boolean;
  consecutive_errors: number;
  data_refresh_interval_s: number;
  forecast_recompute_interval_s: number;
}
