"""
Alert System
=============
Manages configurable alerts for systemic risk thresholds.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

# Simple file-based storage for alerts
ALERTS_STORAGE_PATH = os.path.join(os.path.dirname(__file__), "..", "alerts.json")


class AlertManager:
    """Manages alert configuration and triggering."""

    # Alert types
    ALERT_STABILITY_THRESHOLD = "stability_threshold"
    ALERT_PAYLOAD_CHANGE = "payload_change"
    ALERT_HUB_SHIFT = "hub_shift"

    def __init__(self):
        self.alerts: List[Dict] = self._load_alerts()
        self.triggered: List[Dict] = []

    def _load_alerts(self) -> List[Dict]:
        """Load alerts from storage."""
        if os.path.exists(ALERTS_STORAGE_PATH):
            try:
                with open(ALERTS_STORAGE_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return self._default_alerts()

    def _default_alerts(self) -> List[Dict]:
        """Create default alert configurations."""
        return [
            {
                "id": str(uuid.uuid4()),
                "type": self.ALERT_STABILITY_THRESHOLD,
                "name": "High Instability Warning",
                "description": "Triggers when stability index exceeds 1.0",
                "threshold": 1.0,
                "enabled": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "type": self.ALERT_PAYLOAD_CHANGE,
                "name": "Low Netting Efficiency",
                "description": "Triggers when payload reduction drops below 20%",
                "threshold": 20.0,
                "enabled": True,
                "created_at": datetime.now().isoformat(),
            },
        ]

    def _save_alerts(self):
        """Save alerts to storage."""
        try:
            with open(ALERTS_STORAGE_PATH, "w") as f:
                json.dump(self.alerts, f, indent=2)
        except Exception as e:
            print(f"[AlertManager] Failed to save alerts: {e}")

    def create_alert(
        self,
        alert_type: str,
        name: str,
        threshold: float,
        description: str = "",
        enabled: bool = True,
    ) -> Dict:
        """
        Create a new alert.
        
        Args:
            alert_type: Type of alert (stability_threshold, payload_change, hub_shift)
            name: Human-readable name
            threshold: Numeric threshold for triggering
            description: Optional description
            enabled: Whether the alert is active
        
        Returns:
            Created alert configuration
        """
        alert = {
            "id": str(uuid.uuid4()),
            "type": alert_type,
            "name": name,
            "description": description,
            "threshold": threshold,
            "enabled": enabled,
            "created_at": datetime.now().isoformat(),
        }
        self.alerts.append(alert)
        self._save_alerts()
        return alert

    def delete_alert(self, alert_id: str) -> bool:
        """
        Delete an alert by ID.
        
        Returns:
            True if deleted, False if not found
        """
        for i, alert in enumerate(self.alerts):
            if alert["id"] == alert_id:
                self.alerts.pop(i)
                self._save_alerts()
                return True
        return False

    def update_alert(self, alert_id: str, updates: Dict) -> Optional[Dict]:
        """
        Update an existing alert.
        
        Args:
            alert_id: ID of alert to update
            updates: Dict of fields to update
        
        Returns:
            Updated alert or None if not found
        """
        for alert in self.alerts:
            if alert["id"] == alert_id:
                for key, value in updates.items():
                    if key in alert and key != "id":
                        alert[key] = value
                self._save_alerts()
                return alert
        return None

    def get_alerts(self) -> List[Dict]:
        """Get all configured alerts."""
        return self.alerts

    def check_alerts(self, forecast_data: Dict) -> List[Dict]:
        """
        Check all enabled alerts against current forecast data.
        
        Args:
            forecast_data: Dict containing stability, payload_reduction, etc.
        
        Returns:
            List of triggered alerts
        """
        triggered = []
        now = datetime.now().isoformat()

        for alert in self.alerts:
            if not alert.get("enabled", True):
                continue

            is_triggered = False
            message = ""

            if alert["type"] == self.ALERT_STABILITY_THRESHOLD:
                stability = forecast_data.get("stability", 0)
                if stability >= alert["threshold"]:
                    is_triggered = True
                    message = f"Stability index {stability:.4f} exceeds threshold {alert['threshold']}"

            elif alert["type"] == self.ALERT_PAYLOAD_CHANGE:
                reduction = forecast_data.get("payload_reduction", 100)
                if reduction < alert["threshold"]:
                    is_triggered = True
                    message = f"Payload reduction {reduction:.1f}% below threshold {alert['threshold']}%"

            elif alert["type"] == self.ALERT_HUB_SHIFT:
                # This would require tracking hub changes over time
                pass

            if is_triggered:
                triggered_alert = {
                    **alert,
                    "triggered_at": now,
                    "message": message,
                    "current_value": forecast_data.get("stability") or forecast_data.get("payload_reduction"),
                }
                triggered.append(triggered_alert)
                self.triggered.append(triggered_alert)

        # Keep only last 50 triggered alerts in memory
        self.triggered = self.triggered[-50:]
        return triggered

    def get_triggered_alerts(self, since: Optional[str] = None) -> List[Dict]:
        """
        Get recently triggered alerts.
        
        Args:
            since: Optional ISO timestamp to filter alerts after
        
        Returns:
            List of triggered alert events
        """
        if since:
            return [a for a in self.triggered if a["triggered_at"] > since]
        return self.triggered[-10:]

    def clear_triggered(self):
        """Clear triggered alerts history."""
        self.triggered = []


# Global instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the singleton AlertManager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
