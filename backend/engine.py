import torch
import numpy as np

from optimize import OptimizationNode
from gnn_model import SuperNodeGNN

class FinancialOptimizationEngine:
    def __init__(self, gnn_model, device=None):
        self.model = gnn_model
        self.model.eval()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.optimizer = OptimizationNode()

    @staticmethod
    def load_gnn_model(model_path, node_features=2, hidden_dim=32, device=None):
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        model = SuperNodeGNN(node_features=node_features, hidden_dim=hidden_dim).to(device)
        state = torch.load(model_path, map_location=device)
        model.load_state_dict(state)
        model.eval()
        return model

    def get_predictions(self, x_window, edge_index):
        """Step 1: Get Forecasted Node Signals from the trained GNN"""
        with torch.no_grad():
            x_window = x_window.to(self.device)
            edge_index = edge_index.to(self.device)
            predicted_output = self.model(x_window, edge_index).squeeze(-1)
        return predicted_output

    @staticmethod
    def build_obligations(node_scores, base_obligations=None):
        """
        Map node-level predictions to an obligations matrix suitable for netting.
        If a base matrix is provided, scale rows by predicted stress.
        Otherwise, infer flows from payers (negative) to receivers (positive).
        """
        if base_obligations is not None:
            base_obligations = base_obligations.to(node_scores.device)
            scale = 1 + torch.clamp(node_scores, min=-0.9, max=1.0)
            obligations = base_obligations * scale.unsqueeze(1)
        else:
            payers = torch.relu(-node_scores)
            receivers = torch.relu(node_scores)
            obligations = torch.outer(payers, receivers)

        obligations = torch.clamp(obligations, min=0)
        obligations.fill_diagonal_(0)
        return obligations

    def generate_risk_jacobian(self, predicted_O, liquidity):
        """Step 2: Calculate the Risk Adjacency Matrix (The Sensitivity)"""
        predicted_O = predicted_O.clone().detach().requires_grad_(True)
        liquidity = liquidity.to(predicted_O.device).clone().detach()
        
        # We define the flow function locally for the Jacobian
        def flow_score(O_input):
            # i owes j. If j's liquidity drops, i's risk of not getting paid grows.
            inflow = torch.sum(O_input.T, dim=1)
            outflow = torch.sum(O_input, dim=1)
            net = (liquidity + inflow) - outflow
            # Normalize net position to keep sigmoid in its sensitive range.
            # Without this, large positive net positions saturate sigmoid to 0,
            # causing vanishing gradients and a dead Jacobian.
            scale = outflow.clamp(min=1.0)
            stress = torch.sigmoid(-net / scale)  # Normalized Stress Score
            return stress

        # Compute Jacobian: d(Stress)/d(Obligations)
        # J shape: [N (output), N (input row), N (input col)]
        J = torch.autograd.functional.jacobian(flow_score, predicted_O)
        
        # Collapse to [N, N] Risk Adjacency Matrix
        # J[i, j, k] = d(stress_i) / d(O[j,k])
        # Sum over k to get: how does changing row j affect node i
        risk_adj = J.sum(dim=2)  # [N, N]
        return risk_adj

    def run_pipeline(self, x_window, edge_index, liquidity_tensor, base_obligations=None):
        # 1. Predict node-level signals
        node_scores = self.get_predictions(x_window, edge_index)

        # 2. Build obligations matrix for optimization
        pred_O = self.build_obligations(node_scores, base_obligations)

        # 3. Analyze Sensitivity
        risk_adj = self.generate_risk_jacobian(pred_O, liquidity_tensor)
        hubs, stability = self.optimizer.get_systemic_hubs(risk_adj)

        # 4. Netting (Payload Reduction)
        netted_matrix, raw_load, net_load = self.optimizer.minimize_payload(pred_O, hubs)

        # 5. Result Formatting
        payload_reduction = ((raw_load - net_load) / raw_load * 100) if raw_load > 0 else 0.0

        return {
            "obligations_to_ccp": netted_matrix,
            "obligations_before": pred_O.detach().cpu().numpy(),
            "systemic_hubs": hubs,
            "stability": float(stability),
            "predicted_node_scores": node_scores.detach().cpu().numpy(),
            "payload_reduction": float(payload_reduction),
            "raw_load": float(raw_load),
            "net_load": float(net_load),
        }

# Usage:
# model = FinancialOptimizationEngine.load_gnn_model("super_node_v1.pth")
# engine = FinancialOptimizationEngine(model)
# results = engine.run_pipeline(x_window, edge_index, bank_liquidity_tensor)