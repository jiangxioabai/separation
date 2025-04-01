# %% [markdown]
# 这个代码是walksat的实验设计

# %%
import os
os.chdir('/home/jiangtao/separation/328')  # 设定脚本的工作目录
import networkx as nx
import matplotlib.pyplot as plt
import sys
sys.path.append('/home/jiangtao/cnfgen')
from cnfgen import TseitinFormula, CNF
from pathlib import Path
import os
import random
import gc  # 导入垃圾回收库


def draw_graph_and_save(G, filepath):
    """
    将图 G 绘制并保存到 filepath (例如 'my_graph.png').
    注意：对于节点非常多的图，画出来可能会很拥挤且加载慢。
    """
    # 创建一个画布
    plt.figure(figsize=(8, 6))  # 可以根据需要修改尺寸

    # 使用 networkx 画图
    # with_labels=True 表示显示节点编号；节点多时可以去掉以防信息太乱
    nx.draw(G, with_labels=False, node_size=30, alpha=0.8)
    
    # 保存并关闭
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

# %%
def generate_even_true_charges(num_nodes):
    charges = [False] * num_nodes  # 初始全为False
    num_true = random.randrange(0, num_nodes // 2) * 2  # 确保生成的True的数量为偶数

    true_indices = random.sample(range(num_nodes), num_true)  # 随机选择位置设为True
    for index in true_indices:
        charges[index] = True

    return charges

# %%
def generate_linear_block_graph(n, d=4, seed=1):
    """
    构造线性连接的 n 个块，每个块 b^{(i)} 都是一个随机 d-正则连通子图
    （含 n 个顶点），并在相邻块之间插入一个长度为 n+1 的路径 p^{(i)}。
    注意：此函数返回的图节点数 ~= n^2 + (n-1)*(n+1)，
         其中有一些节点会被当作连接点（共享在块和路径之间）。
    参数:
        n:   表示块的数量，也表示每个块 b^{(i)} 的顶点数量
        d:   每个块的度数 (default=4)
        seed: 随机种子
    返回:
        G: 一个包含 n 个子图 + (n-1) 条路径的巨大连通图
    """
    if seed is not None:
        random.seed(seed)
    
    # 大图 G，用于容纳所有块和路径
    G = nx.Graph()
    
    # 下面给每个块分配一个独立的“节点范围”，再把它们加入 G
    # 例如：第 i 个块（i从0开始计）节点编号范围 [ i*n, (i+1)*n - 1 ]
    # 这样不会和别的块或路径冲突
    def block_node_label(i_block, local_index):
        """块 b^{(i_block)} 的第 local_index 个顶点的全局标号"""
        return i_block * n + local_index
    
    # 先逐块生成 b^{(i)}
    for i in range(n):
        # 生成一个 d-正则图(含 n 个节点)
        # 这里使用 networkx 内置的 random_regular_graph(d, n)
        # 返回的节点标号是 0~(n-1)，我们随后要做一个重命名
        block_graph = nx.random_regular_graph(d, n, seed=n)
        
        # 把 block_graph 的每个节点 x 都映射到全局节点 block_node_label(i, x)
        # edges 也相应重定名
        mapping = {old: block_node_label(i, old) for old in range(n)}
        block_graph = nx.relabel_nodes(block_graph, mapping)
        
        # 将这个块并入到大图 G
        G.add_nodes_from(block_graph.nodes())
        G.add_edges_from(block_graph.edges())
    
    # 再在相邻块之间插入 (n-1) 条路径，每条路径含 (n+1) 个“新”节点。
    #  - 该路径的一端与块 b^{(i)} 的某个节点重合，
    #    另一端与块 b^{(i+1)} 的某个节点重合，
    #  - 其余节点是全新的。
    
    # 我们在每个块 b^{(i)} 中，选一个“锚点”用于连接路径。
    # 例如，可以选块 b^{(i)} 中编号最小的那个节点( i*n ) 作为锚点。
    # 你也可以随机选一个节点作锚点。
    
    for i in range(n-1):
        # 块 b^{(i)} 的锚点
        anchor_i = block_node_label(i, 0)
        # 块 b^{(i+1)} 的锚点
        anchor_i1 = block_node_label(i+1, 0)
        
        # 生成路径上 n-1 个“新”节点的全局编号
        # 这里简单做法：给它们用一段连续编号
        # 例如: path_i_j = n*n + (i*(n+1) + j)   (偏移 n*n，保证不和前面冲突)
        path_new_nodes = []
        for j in range(1, n):  
            new_node_label = n*n + i*(n-1) + (j-1)
            path_new_nodes.append(new_node_label)
        
        # 组合成“完整路径顶点序列”
        # endpoints = [anchor_i, ...中间n-1个新节点..., anchor_i1]
        path_vertex_list = [anchor_i] + path_new_nodes + [anchor_i1]
        
        # 添加到 G，并把它们连成一条 path
        for v in path_vertex_list:
            G.add_node(v)
        
        for idx in range(len(path_vertex_list) - 1):
            G.add_edge(path_vertex_list[idx], path_vertex_list[idx + 1])
    
    return G

def save_formula_to_file(dimacs_str, directory, filename):
    """Save the DIMACS CNF string to a file in the specified directory."""
    Path(directory).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(directory, f"{filename}.cnf")
    with open(filepath, 'w') as file:
        file.write(dimacs_str)

def generate_graph_and_formula(graph_type, n):
    G = generate_graph(n, graph_type)  # 使用之前定义的函数生成图
    charges = generate_even_true_charges(len(G.nodes()))  # 为图的每个节点生成电荷序列

    formula = TseitinFormula(G, charges=charges)  # 使用自定义的电荷序列生成Tseitin公式
    return formula, G
def generate_graphs_and_save_formulas(graph_type, start_nodes, max_nodes, step, instances_per_size):
    for n in range(start_nodes, max_nodes + 1, step):
        for instance in range(1, instances_per_size + 1):
            # Generate the graph based on type
            formula, G = generate_graph_and_formula(graph_type, n)
            dimacs_str = formula.to_dimacs()  # Assuming `to_dimacs()` is the method generating the DIMACS string.

            # Save the formula to a file
            directory_name = f"/home/jiangtao/separation/328/LN"
            filename = f"{graph_type}_{n}_{instance}"
            save_formula_to_file(dimacs_str, directory_name, filename)
            
            # ========== 2) 画图并保存 PNG 文件 ==========
            # 如果你想把网络图也放在同一个文件夹下，可以这样:
            graph_image_filepath = os.path.join(directory_name, f"{filename}.png")
            # draw_graph_and_save(G, graph_image_filepath)

def generate_graph(n, graph_type):
    while True:
        if graph_type == 'tree':
            G = nx.random_tree(n)
        elif graph_type == 'grid':
            dim = int(n**0.5)
            # 确保维度至少为2x2以避免非联通情况
            if dim > 1:
                G = nx.grid_2d_graph(dim, dim)
            else:
                continue
        elif graph_type == 'bipartite':
            nodes_per_part = n // 2
            # 保证每一部分至少有一个节点
            if nodes_per_part > 0:
                G = nx.complete_bipartite_graph(nodes_per_part, n - nodes_per_part)
            else:
                continue
        elif graph_type == 'random':
            p = 0.5
            G = nx.erdos_renyi_graph(n, p)
        elif graph_type == 'high_connectivity':
            G = nx.complete_graph(n)
        elif graph_type == 'regular1':
            print(n)
            degree_sequence = [4] * n
            G = nx.random_degree_sequence_graph(degree_sequence)
        elif graph_type == 'linear_block':
            # 这里调用我们新写的函数
            # n 表示“块”数目 & 每个块的顶点数
            # d=3 作为演示，也可做成可配置
            G = generate_linear_block_graph(n, d=4, seed=None)
        else:
            raise ValueError(f"Unknown graph_type: {graph_type}")

        #检查生成的图是否联通
        if nx.is_connected(G):
            return G
        else: 
            del G
            gc.collect()



# %%
# Example usage
# kind_list = ['tree', "grid"]
# for kind in kind_list:
#     generate_graphs_and_save_formulas(kind, 10, 10000, 10, 5)


# kind_list = ['high_connectivity']
# for kind in kind_list:
#     generate_graphs_and_save_formulas(kind, 5, 100, 1, 5)

# 生成从 n=2 到 n=5 的若干个“linear_block”图，并各实例化2次
generate_graphs_and_save_formulas("linear_block", 51, 59, 1, 1)

# generate_graphs_and_save_formulas("bipartite", 10, 50, 1, 5)

# %%
# kind_list = ['tree', 'grid']
# for kind in kind_list:
#     generate_graphs_and_save_formulas(kind, 10, 10000, 10, 5)
