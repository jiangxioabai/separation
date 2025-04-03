import os
import networkx as nx
import matplotlib.pyplot as plt
import sys
import random
import gc
import argparse  # 引入 argparse
from cnfgen import TseitinFormula, CNF
from pathlib import Path

# 设定脚本的工作目录
os.chdir('/home/jiangtao/separation/328')

# 添加对 cnfgen 库的引用路径
sys.path.append('/home/jiangtao/cnfgen')

def draw_graph_and_save(G, filepath):
    """
    将图 G 绘制并保存到 filepath (例如 'my_graph.png').
    """
    plt.figure(figsize=(8, 6))
    nx.draw(G, with_labels=False, node_size=30, alpha=0.8)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

def generate_even_true_charges(num_nodes):
    charges = [False] * num_nodes
    num_true = random.randrange(0, num_nodes // 2) * 2
    true_indices = random.sample(range(num_nodes), num_true)
    for index in true_indices:
        charges[index] = True
    return charges

def generate_linear_block_graph(n, d=4, seed=1):
    G = nx.Graph()
    def block_node_label(i_block, local_index):
        return i_block * n + local_index
    for i in range(n):
        block_graph = nx.random_regular_graph(d, n, seed=n)
        mapping = {old: block_node_label(i, old) for old in range(n)}
        block_graph = nx.relabel_nodes(block_graph, mapping)
        G.add_nodes_from(block_graph.nodes())
        G.add_edges_from(block_graph.edges())
    for i in range(n-1):
        anchor_i = block_node_label(i, 0)
        anchor_i1 = block_node_label(i+1, 0)
        path_new_nodes = [n*n + i*(n-1) + (j-1) for j in range(1, n)]
        path_vertex_list = [anchor_i] + path_new_nodes + [anchor_i1]
        for v in path_vertex_list:
            G.add_node(v)
        for idx in range(len(path_vertex_list) - 1):
            G.add_edge(path_vertex_list[idx], path_vertex_list[idx + 1])
    return G

def save_formula_to_file(dimacs_str, directory, filename):
    Path(directory).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(directory, f"{filename}.cnf")
    with open(filepath, 'w') as file:
        file.write(dimacs_str)

def generate_graph_and_formula(graph_type, n):
    G = generate_graph(n, graph_type)
    charges = generate_even_true_charges(len(G.nodes()))
    formula = TseitinFormula(G, charges=charges)
    return formula, G

BASE_OUTPUT_DIR = "/home/jiangtao/separation/328/formulas"

def generate_graphs_and_save_formulas(graph_type, start_nodes, max_nodes, step, instances_per_size):
    for n in range(start_nodes, max_nodes + 1, step):
        for instance in range(1, instances_per_size + 1):
            formula, G = generate_graph_and_formula(graph_type, n)
            dimacs_str = formula.to_dimacs()
            directory_name = os.path.join(BASE_OUTPUT_DIR, graph_type)
            filename = f"{graph_type}_{n}_{instance}"
            save_formula_to_file(dimacs_str, directory_name, filename)

def generate_graph(n, graph_type):
    while True:
        if graph_type == 'tree':
            G = nx.random_tree(n)
        elif graph_type == 'grid':
            dim = int(n**0.5)
            if dim > 1:
                G = nx.grid_2d_graph(dim, dim)
            else:
                continue
        elif graph_type == 'random':
            p = 0.5
            G = nx.erdos_renyi_graph(n, p)
        elif graph_type == 'regular':
            degree_sequence = [4] * n
            G = nx.random_degree_sequence_graph(degree_sequence)
        elif graph_type == 'L_n':
            G = generate_linear_block_graph(n, d=4, seed=None)
        else:
            raise ValueError(f"Unknown graph_type: {graph_type}")

        if nx.is_connected(G):
            return G
        else: 
            del G
            gc.collect()

# 设置命令行参数
def main():
    parser = argparse.ArgumentParser(description='Generate and save graph formulas.')
    parser.add_argument('graph_type', type=str, help='Type of the graph (e.g., tree, grid, regular, L_n)')
    parser.add_argument('start_nodes', type=int, help='Starting number of nodes')
    parser.add_argument('max_nodes', type=int, help='Maximum number of nodes')
    parser.add_argument('step', type=int, help='Step size for number of nodes')
    parser.add_argument('instances_per_size', type=int, help='Number of instances per graph size')

    args = parser.parse_args()

    generate_graphs_and_save_formulas(args.graph_type, args.start_nodes, args.max_nodes, args.step, args.instances_per_size)

if __name__ == '__main__':
    main()

# %%
# kind_list = ['tree', 'grid']
# for kind in kind_list:
#     generate_graphs_and_save_formulas(kind, 10, 10000, 10, 5)
