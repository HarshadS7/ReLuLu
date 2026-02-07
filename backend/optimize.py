import networkx as nx
import numpy as np

class OptimizationNode:
    def __init__(self):
        pass

    def get_systemic_hubs(self, risk_matrix):
        """
        Uses Eigen-decomposition to find which banks are 'load bearing'.
        """
        # Calculate Eigenvalues and Eigenvectors of the Risk Matrix
        eigenvalues, eigenvectors = np.linalg.eig(risk_matrix.detach().numpy())
        
        # The Principal Eigenvector (associated with largest eigenvalue)
        # tells us the "Centrality" or importance of each node.
        idx = np.argmax(np.abs(eigenvalues))
        centrality = np.abs(eigenvectors[:, idx])
        
        stability_limit = np.max(np.abs(eigenvalues))
        return centrality, stability_limit

    def minimize_payload(self, predicted_trades, centrality_scores):
        """
        Performs Circular Netting, prioritizing high-risk hubs.
        """
        # 1. Convert Matrix to Graph
        G = nx.DiGraph(predicted_trades.detach().numpy())
        initial_volume = G.size(weight='weight')

        # 2. Circular Netting (The "Zero Risk" Mechanism)
        # We look for cycles (A->B->C->A) and cancel out the math.
        # We sort nodes by centrality to prioritize clearing Hubs first.
        try:
            cycles = list(nx.simple_cycles(G))
            # Sort cycles by 'Risk Weight' (sum of centrality of nodes in cycle)
            cycles.sort(key=lambda c: sum(centrality_scores[n] for n in c), reverse=True)
            
            for cycle in cycles:
                # Find the edges in this cycle
                edges = list(zip(cycle, cycle[1:] + [cycle[0]]))
                # Find the minimum amount we can net out
                if not edges: continue
                
                # Check if edges exist and get weights
                weights = []
                valid_cycle = True
                for u, v in edges:
                    if G.has_edge(u, v):
                        weights.append(G[u][v]['weight'])
                    else:
                        valid_cycle = False
                        break
                
                if valid_cycle and weights:
                    min_val = min(weights)
                    # Subtract that amount from all edges
                    for u, v in edges:
                        G[u][v]['weight'] -= min_val
                        # Remove edge if it hits 0
                        if G[u][v]['weight'] <= 1e-5:
                            G.remove_edge(u, v)
                            
        except Exception as e:
            print(f"Netting optimization skipped: {e}")

        final_volume = G.size(weight='weight')
        
        # 3. Return the Optimized Matrix (Residuals)
        optimized_matrix = nx.to_numpy_array(G, nodelist=range(len(centrality_scores)))
        return optimized_matrix, initial_volume, final_volume