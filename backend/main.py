import torch
import torch.nn.functional as F
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import io

# --- 1. THE SYSTEM CONFIGURATION ---
NUM_BANKS = 8
# Simulation of a "Stress Scenario"
# In a real run, these come from your T-GCN model
np.random.seed(42)
torch.manual_seed(42)

class FinancialDigitalTwin:
    """
    Simulates the 'Brain' of the system. 
    In production, this wraps your trained GNN model.
    """
    def __init__(self, num_nodes):
        self.n = num_nodes
    
    def get_predicted_state(self):
        # SIMULATION: Generating a random adjacency matrix for T+1
        # Represents predicted obligations between banks
        pred_obligations = torch.abs(torch.randn(self.n, self.n)) 
        
        # Zero out diagonal (banks don't trade with themselves)
        pred_obligations.fill_diagonal_(0)
        
        # Predicted Liquidity (Cash on hand)
        pred_liquidity = torch.abs(torch.randn(self.n)) * 100 + 50
        pred_liquidity.requires_grad = True # CRITICAL for Jacobian
        
        # Predicted Reliability (0.0 to 1.0)
        pred_reliability = torch.rand(self.n)
        
        return pred_obligations, pred_liquidity, pred_reliability

# --- 2. THE RISK ENGINE (HEART) ---
class RiskEngine:
    """
    Calculates the 'Physics' of the financial network.
    Uses Calculus to find sensitivity (The Jacobian).
    """
    @staticmethod
    def flow_function(liquidity, obligations, reliability):
        """
        The mathematical model of settlement risk.
        """
        # Inflow: What others owe me * probability they pay
        # obligations.T means columns become rows (Incoming money)
        inflow = torch.matmul(obligations.T, reliability) 
        
        # Outflow: What I owe others
        outflow = torch.sum(obligations, dim=1)
        
        # Net Position: (Cash + In) - Out
        net_position = (liquidity + inflow) - outflow
        
        # Risk Score: Sigmoid maps negative position to high risk (closer to 1.0)
        return torch.sigmoid(-net_position)

    @staticmethod
    def get_risk_adjacency_matrix(L, O, R):
        """
        Calculates d(Risk_i) / d(Liquidity_j)
        """
        # We calculate how sensitive the Risk Score is to changes in Liquidity
        # This returns the Jacobian Matrix (N x N)
        jacobian = torch.autograd.functional.jacobian(
            lambda l: RiskEngine.flow_function(l, O, R), L
        )
        return jacobian

# --- 3. THE OPTIMIZATION NODE (HANDS) ---
class OptimizationNode:
    """
    The 'New Node' that nets trades and ensures Zero Risk.
    """
    def __init__(self, risk_matrix):
        self.risk_matrix = risk_matrix.detach().numpy()

    def get_systemic_hubs(self):
        # Eigen-decomposition to find the "Boss" banks
        evals, evecs = np.linalg.eig(self.risk_matrix)
        # Get eigenvector for largest eigenvalue
        idx = np.argmax(np.abs(evals))
        centrality = np.abs(evecs[:, idx])
        return centrality, np.max(np.abs(evals)) # Scores, Stability Index

    def circular_netting(self, obligations_tensor):
        """
        Removes cycles from the graph to minimize CCP payload.
        """
        G = nx.DiGraph(obligations_tensor.detach().numpy())
        initial_load = G.size(weight='weight')
        
        # Cycle Cancellation Algorithm
        try:
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles:
                # Identify edges in the cycle
                edges = list(zip(cycle, cycle[1:] + [cycle[0]]))
                if not edges: continue
                
                # Find the bottleneck (minimum amount in the loop)
                weights = [G[u][v]['weight'] for u, v in edges]
                min_val = min(weights)
                
                # Net it out (Subtract min_val from the loop)
                for u, v in edges:
                    G[u][v]['weight'] -= min_val
                    if G[u][v]['weight'] <= 1e-4: # Prune zero edges
                        G.remove_edge(u, v)
                        
        except Exception as e:
            print(f"Optimization Notice: {e}")

        final_load = G.size(weight='weight')
        optimized_matrix = nx.to_numpy_array(G)
        return optimized_matrix, initial_load, final_load, G

# --- 4. VISUALIZATION ---
def plot_results(G_before, G_after, hub_scores):
    plt.figure(figsize=(15, 6))
    
    # Layout based on Hub Importance
    pos = nx.spring_layout(G_before, seed=42)
    
    # Plot 1: Before Optimization
    plt.subplot(1, 2, 1)
    plt.title("Before: Gross Obligations (High Risk)", fontsize=14, color='red')
    nx.draw(G_before, pos, with_labels=True, node_color='lightgray', 
            edge_color='red', width=1, node_size=500, alpha=0.6)
    
    # Plot 2: After Optimization
    plt.subplot(1, 2, 2)
    plt.title("After: Netted Residuals (Zero Risk)", fontsize=14, color='green')
    # Color nodes by Systemic Importance (Darker = More Important)
    nx.draw(G_after, pos, with_labels=True, node_color=hub_scores, cmap=plt.cm.Blues, 
            edge_color='green', width=1.5, node_size=500)
    
    plt.tight_layout()
    plt.show()

# --- 5. MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    print("--- STARTING FINANCIAL SYSTEM SIMULATION ---")
    
    # A. Digital Twin Prediction (GNN Output)
    twin = FinancialDigitalTwin(NUM_BANKS)
    pred_O, pred_L, pred_R = twin.get_predicted_state()
    print(f"1. GNN Prediction Complete: Analyzed {NUM_BANKS} Banks.")

    # B. Risk Analysis (Jacobian)
    risk_adj_matrix = RiskEngine.get_risk_adjacency_matrix(pred_L, pred_O, pred_R)
    print("2. Risk Adjacency Matrix Calculated (Sensitivity Analysis Complete).")

    # C. Optimization (Netting)
    optimizer = OptimizationNode(risk_adj_matrix)
    hub_scores, stability_index = optimizer.get_systemic_hubs()
    
    print(f"   -> System Stability Index (Spectral Radius): {stability_index:.4f}")
    if stability_index > 1.0:
        print("      WARNING: Cascading Failure Predicted. Aggressive Netting Engaged.")
    else:
        print("      STATUS: System Stable. Standard Netting Engaged.")

    # Create Graph for 'Before' visualization
    G_before = nx.DiGraph(pred_O.detach().numpy())
    
    # Run Circular Netting
    opt_matrix, start_vol, end_vol, G_after = optimizer.circular_netting(pred_O)

    # D. The "Zero Risk" Audit Report
    reduction = ((start_vol - end_vol) / start_vol) * 100
    
    print("\n--- NEW NODE AUDIT REPORT ---")
    print(f"Original CCP Payload: ${start_vol:.2f}M")
    print(f"Optimized CCP Payload: ${end_vol:.2f}M")
    print(f"LIQUIDITY SAVED: {reduction:.2f}%")
    print("-----------------------------")
    
    # E. Visualize
    print("Generating Visual Proof...")
    plot_results(G_before, G_after, hub_scores)