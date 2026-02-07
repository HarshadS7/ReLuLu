"""
Full standalone simulation — FinancialDigitalTwin + RiskEngine + OptimizationNode.

This was the original main.py proof-of-concept.  Kept as a runnable demo.

Usage:
    cd backend
    python -m scripts.simulation
"""

import torch
import torch.nn.functional as F
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


NUM_BANKS = 8
np.random.seed(42)
torch.manual_seed(42)


class FinancialDigitalTwin:
    def __init__(self, num_nodes):
        self.n = num_nodes

    def get_predicted_state(self):
        pred_obligations = torch.abs(torch.randn(self.n, self.n))
        pred_obligations.fill_diagonal_(0)
        pred_liquidity = torch.abs(torch.randn(self.n)) * 100 + 50
        pred_liquidity.requires_grad = True
        pred_reliability = torch.rand(self.n)
        return pred_obligations, pred_liquidity, pred_reliability


class RiskEngine:
    @staticmethod
    def flow_function(liquidity, obligations, reliability):
        inflow = torch.matmul(obligations.T, reliability)
        outflow = torch.sum(obligations, dim=1)
        net_position = (liquidity + inflow) - outflow
        scale = outflow.clamp(min=1.0)
        return torch.sigmoid(-net_position / scale)

    @staticmethod
    def get_risk_adjacency_matrix(L, O, R):
        return torch.autograd.functional.jacobian(
            lambda l: RiskEngine.flow_function(l, O, R), L
        )


class OptimizationNode:
    def __init__(self, risk_matrix):
        self.risk_matrix = risk_matrix.detach().numpy()

    def get_systemic_hubs(self):
        evals, evecs = np.linalg.eig(self.risk_matrix)
        idx = np.argmax(np.abs(evals))
        centrality = np.abs(evecs[:, idx])
        return centrality, np.max(np.abs(evals))

    def circular_netting(self, obligations_tensor):
        G = nx.DiGraph(obligations_tensor.detach().numpy())
        initial_load = G.size(weight="weight")
        try:
            for cycle in nx.simple_cycles(G):
                edges = list(zip(cycle, cycle[1:] + [cycle[0]]))
                weights = []
                valid = True
                for u, v in edges:
                    if G.has_edge(u, v):
                        weights.append(G[u][v]["weight"])
                    else:
                        valid = False
                        break
                if valid and weights:
                    m = min(weights)
                    for u, v in edges:
                        G[u][v]["weight"] -= m
                        if G[u][v]["weight"] <= 1e-4:
                            G.remove_edge(u, v)
        except Exception as e:
            print(f"Optimization notice: {e}")
        final_load = G.size(weight="weight")
        return nx.to_numpy_array(G), initial_load, final_load, G


def plot_results(G_before, G_after, hub_scores):
    plt.figure(figsize=(15, 6))
    pos = nx.spring_layout(G_before, seed=42)

    plt.subplot(1, 2, 1)
    plt.title("Before: Gross Obligations", fontsize=14, color="red")
    nx.draw(G_before, pos, with_labels=True, node_color="lightgray",
            edge_color="red", width=1, node_size=500, alpha=0.6)

    plt.subplot(1, 2, 2)
    plt.title("After: Netted Residuals", fontsize=14, color="green")
    nx.draw(G_after, pos, with_labels=True, node_color=hub_scores,
            cmap=plt.cm.Blues, edge_color="green", width=1.5, node_size=500)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    twin = FinancialDigitalTwin(NUM_BANKS)
    O, L, R = twin.get_predicted_state()
    risk_adj = RiskEngine.get_risk_adjacency_matrix(L, O, R)

    opt = OptimizationNode(risk_adj)
    hubs, stability = opt.get_systemic_hubs()

    print(f"Stability Index: {stability:.4f}")
    status = "UNSTABLE — aggressive netting" if stability > 1.0 else "STABLE"
    print(f"Status: {status}")

    G_before = nx.DiGraph(O.detach().numpy())
    _, start, end, G_after = opt.circular_netting(O)
    reduction = ((start - end) / start) * 100

    print(f"\nPayload: ${start:.2f}M → ${end:.2f}M  ({reduction:.1f}% saved)")
    plot_results(G_before, G_after, hubs)
