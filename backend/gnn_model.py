import torch.nn as nn
from torch_geometric.nn import GCNConv


class SuperNodeGNN(nn.Module):
    def __init__(self, node_features=2, hidden_dim=32):
        super(SuperNodeGNN, self).__init__()
        self.gcn = GCNConv(node_features, hidden_dim)
        self.lstm = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
        self.relu = nn.ReLU()

    def forward(self, x, edge_index):
        num_nodes, seq_len, num_feats = x.size()
        x_in = x.view(-1, num_feats)
        x_gcn = self.relu(self.gcn(x_in, edge_index))
        x_lstm = x_gcn.view(num_nodes, seq_len, -1)
        _, (hn, _) = self.lstm(x_lstm)
        return self.fc(hn.squeeze(0))
