"""
SuperNodeGNN — Original single-snapshot model
===============================================
Architecture: GCN → LSTM → Linear
Checkpoint  : super_node_v1.pth
"""

import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv


class SuperNodeGNN(nn.Module):
    """Single-snapshot GCN + LSTM — the architecture of super_node_v1.pth."""

    def __init__(self, node_features: int = 2, hidden_dim: int = 32):
        super().__init__()
        self.gcn = GCNConv(node_features, hidden_dim)
        self.lstm = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # x: [N, T, F]
        num_nodes, seq_len, num_feats = x.size()
        x_in = x.view(-1, num_feats)
        x_gcn = self.relu(self.gcn(x_in, edge_index))
        x_lstm = x_gcn.view(num_nodes, seq_len, -1)
        _, (hn, _) = self.lstm(x_lstm)
        return self.fc(hn.squeeze(0))
