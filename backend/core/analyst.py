from openai import OpenAI
import os
from typing import Dict, Any, List


class ReLuLuAnalyst:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key=api_key
        )

    def summarize_risk(self, forecast_data: Dict[str, Any]) -> str:
        """
        Analyze systemic risk based on netting forecast data.
        
        Args:
            forecast_data: Dictionary containing:
                - hubs: List of primary systemic hub bank names
                - reduction_pct: Payload reduction percentage from netting
                - stability_index: System stability metric (< 1.0 = stable)
                - horizon: Forecast time horizon (days ahead)
                - is_stable: Boolean stability flag
                - raw_load: Total gross payment obligations
                - net_load: Total net payment obligations after netting
                - all_horizons: (Optional) List of all horizon data for temporal analysis
        
        Returns:
            AI-generated risk assessment summary
        """
        try:
            hub = forecast_data.get('hubs', ['Unknown'])[0]
            reduction = forecast_data.get('reduction_pct', 0)
            stability = forecast_data.get('stability_index', 0)
            horizon = forecast_data.get('horizon', 'N/A')
            is_stable = forecast_data.get('is_stable', False)
            raw_load = forecast_data.get('raw_load', 0)
            net_load = forecast_data.get('net_load', 0)
            
            # Check for multi-horizon temporal data
            all_horizons = forecast_data.get('all_horizons', None)
            
            if all_horizons and len(all_horizons) > 1:
                # Multi-horizon temporal analysis
                prompt = self._build_temporal_prompt(
                    hub, all_horizons, horizon, reduction, stability, 
                    is_stable, raw_load, net_load
                )
            else:
                # Single-horizon analysis (backward compatibility)
                prompt = self._build_single_prompt(
                    hub, reduction, stability, horizon, 
                    is_stable, raw_load, net_load
                )

            completion = self.client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )

            return completion.choices[0].message.content.strip()

        except Exception as e:
            return f"⚠️ AI service error: {str(e)}"

    def _build_single_prompt(
        self, hub: str, reduction: float, stability: float, 
        horizon: int, is_stable: bool, raw_load: float, net_load: float
    ) -> str:
        """Build prompt for single-horizon analysis."""
        return f"""Act as a systemic risk analyst for interbank payment networks.

Current Netting State (T+{horizon} forecast):
- Primary Systemic Hub: {hub}
- Payload Reduction: {reduction:.1f}%
- Stability Index: {stability:.4f} {'(STABLE)' if is_stable else '(UNSTABLE)'}
- Raw Load: {raw_load:.2f}
- Net Load: {net_load:.2f}

Provide a concise 2-3 sentence risk assessment focusing on:
1. Overall systemic health
2. Key vulnerabilities or strengths
3. Actionable insight

Be specific and professional. Do not use generic language."""

    def _build_temporal_prompt(
        self, hub: str, all_horizons: List[Dict], target_horizon: int,
        reduction: float, stability: float, is_stable: bool, 
        raw_load: float, net_load: float
    ) -> str:
        """Build prompt with multi-horizon temporal trend analysis."""
        
        # Extract trend data
        stability_trend = [h['stability_index'] for h in all_horizons]
        reduction_trend = [h['reduction_pct'] for h in all_horizons]
        load_trend = [h['net_load'] for h in all_horizons]
        
        # Calculate trend direction
        stability_direction = self._get_trend(stability_trend)
        reduction_direction = self._get_trend(reduction_trend)
        load_direction = self._get_trend(load_trend)
        
        # Build temporal summary
        temporal_summary = f"""
TEMPORAL TRENDS (T+1 to T+{len(all_horizons)}):
- Stability: {stability_trend[0]:.4f} → {stability_trend[-1]:.4f} ({stability_direction})
- Payload Reduction: {reduction_trend[0]:.1f}% → {reduction_trend[-1]:.1f}% ({reduction_direction})
- Net Load: {load_trend[0]:.2f} → {load_trend[-1]:.2f} ({load_direction})
"""

        return f"""Act as a systemic risk analyst for interbank payment networks using temporal GNN forecasts.

CURRENT STATE (T+{target_horizon}):
- Primary Systemic Hub: {hub}
- Stability Index: {stability:.4f} {'(STABLE)' if is_stable else '(UNSTABLE)'}
- Payload Reduction: {reduction:.1f}%
- Raw Load: {raw_load:.2f}
- Net Load: {net_load:.2f}
{temporal_summary}

Provide a 3-4 sentence risk assessment focusing on:
1. Current systemic health at T+{target_horizon}
2. Temporal trend implications (improving/degrading)
3. Key vulnerabilities or strengths identified across horizons
4. Actionable insight based on forecast trajectory

Be specific and professional. Highlight any concerning trend reversals or stability degradation."""

    @staticmethod
    def _get_trend(values: List[float]) -> str:
        """Determine trend direction from a list of values."""
        if len(values) < 2:
            return "stable"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff = second_half - first_half
        pct_change = abs(diff / first_half * 100) if first_half != 0 else 0
        
        if pct_change < 5:
            return "stable"
        elif diff > 0:
            return f"↑ increasing {pct_change:.1f}%"
        else:
            return f"↓ decreasing {pct_change:.1f}%"
