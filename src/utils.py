"""Reading and writing data."""

import pandas as pd
import networkx as nx
from tqdm import tqdm
from scipy import sparse
from texttable import Texttable
import torch
import numpy as np
import random

# Reproductabilidade
torch.manual_seed(0)
random.seed(0)
np.random.seed(0)

def read_graph(graph_path):
    """
    Method to read graph and create a target matrix with pooled adjacency matrix powers.
    :param args: Arguments object.
    :return graph: graph.
    """
    graph = nx.from_edgelist(pd.read_csv(graph_path).values.tolist())
    graph.remove_edges_from(nx.selfloop_edges(graph))
    return graph

def tab_printer(args):
    """
    Function to print the logs in a nice tabular format.
    :param args: Parameters used for the model.
    """
    args = vars(args)
    keys = sorted(args.keys())
    t = Texttable()
    t.add_rows([["Parameter", "Value"]])
    t.add_rows([[k.replace("_", " ").capitalize(), args[k]] for k in keys])
    print(t.draw())

def feature_calculator(args, graph):
    """
    Calculating the feature tensor.
    :param args: Arguments object.
    :param graph: NetworkX graph.
    :return target_matrices: Target tensor.
    """
    torch.manual_seed(0)
    random.seed(0)
    np.random.seed(0)
    index_1 = [edge[0] for edge in graph.edges()] + [edge[1] for edge in graph.edges()]
    index_2 = [edge[1] for edge in graph.edges()] + [edge[0] for edge in graph.edges()]
    values = [1 for edge in index_1]
    node_count = max(max(index_1)+1, max(index_2)+1)
    adjacency_matrix = sparse.coo_matrix((values, (index_1, index_2)),
                                         shape=(node_count, node_count),
                                         dtype=np.float32)

    degrees = adjacency_matrix.sum(axis=0)[0].tolist()
    degs = sparse.diags(degrees, [0])
    normalized_adjacency_matrix = degs.power(-1/2).dot(adjacency_matrix).dot(degs.power(-1/2))
    target_matrices = [normalized_adjacency_matrix.todense()]
    powered_A = normalized_adjacency_matrix
    if args.window_size > 1:
        for power in range(args.window_size-1):
            powered_A = powered_A.dot(normalized_adjacency_matrix)
            to_add = powered_A.todense()
            target_matrices.append(to_add)
    target_matrices = np.array(target_matrices)
    return target_matrices

def adjacency_opposite_calculator(graph):
    """
    Creating no edge indicator matrix.
    :param graph: NetworkX object.
    :return adjacency_matrix_opposite: Indicator matrix.
    """
    torch.manual_seed(0)
    random.seed(0)
    np.random.seed(0)
    adjacency_matrix = sparse.csr_matrix(nx.adjacency_matrix(graph), dtype=np.float32).todense()
    adjacency_matrix_opposite = np.ones(adjacency_matrix.shape) - adjacency_matrix
    return adjacency_matrix_opposite
