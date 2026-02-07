"""
Optimization Node
==================
Eigen-decomposition for systemic hub detection +
circular netting for CCP payload minimization.
"""

import numpy as np
import networkx as nx


class OptimizationNode:
    def __init__(self):
        pass

    def get_systemic_hubs(self, risk_matrix):
        """
        Uses Eigen-decomposition to find which banks are 'load bearing'.
        Returns (centrality_scores, stability_index).
        """
        eigenvalues, eigenvectors = np.linalg.eig(risk_matrix.detach().numpy())

        # The principal eigenvector (largest eigenvalue) gives node centrality
        idx = np.argmax(np.abs(eigenvalues))
        centrality = np.abs(eigenvectors[:, idx])

        stability_limit = np.max(np.abs(eigenvalues))
        return centrality, stability_limit

    def minimize_payload(self, predicted_trades, centrality_scores):
        """
        Performs circular netting, prioritizing high-risk hubs.
        Returns (optimized_matrix, initial_volume, final_volume).
        """
        G = nx.DiGraph(predicted_trades.detach().numpy())
        initial_volume = G.size(weight="weight")

        try:
            cycles = list(nx.simple_cycles(G))
            # Sort cycles by risk weight (sum of centrality of nodes in cycle)
            cycles.sort(
                key=lambda c: sum(centrality_scores[n] for n in c), reverse=True
            )

            for cycle in cycles:
                edges = list(zip(cycle, cycle[1:] + [cycle[0]]))
                if not edges:
                    continue

                weights = []
                valid_cycle = True
                for u, v in edges:
                    if G.has_edge(u, v):
                        weights.append(G[u][v]["weight"])
                    else:
                        valid_cycle = False
                        break

                if valid_cycle and weights:
                    min_val = min(weights)
                    for u, v in edges:
                        G[u][v]["weight"] -= min_val
                        if G[u][v]["weight"] <= 1e-5:
                            G.remove_edge(u, v)

        except Exception as e:
            print(f"Netting optimization skipped: {e}")

        final_volume = G.size(weight="weight")
        optimized_matrix = nx.to_numpy_array(
            G, nodelist=range(len(centrality_scores))
        )
        return optimized_matrix, initial_volume, final_volume
