import os
import time
from bitarray import bitarray
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
seed_range = 10
# 读取DIMACS文件
def read_dimacs(filename):
    clauses = []
    variable_to_clauses = {}  # 字典，映射每个变量到它所在的子句
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith('c') or line.startswith('p'):
                continue
            clause = [int(x) for x in line.strip().split()[:-1]]
            clauses.append(clause)
            for literal in clause:
                var = abs(literal)
                if var not in variable_to_clauses:
                    variable_to_clauses[var] = set()
                variable_to_clauses[var].add(len(clauses) - 1)  # 记录该变量出现在当前子句中
    return clauses, variable_to_clauses

# 随机赋值，使用位向量存储赋值
def random_assignment(clauses, num_variables):
    assignment = bitarray(num_variables)
    assignment.setall(False)  # 默认赋值为 False
    for i in range(num_variables):
        assignment[i] = random.choice([True, False])  # 随机赋值
    return assignment

# 评估子句是否被满足
def evaluate_clause(clause, assignment):
    for literal in clause:
        if (literal > 0 and assignment[abs(literal) - 1]) or (literal < 0 and not assignment[abs(literal) - 1]):
            return True
    return False

# 获取未满足的子句
def get_unsatisfied_clauses(clauses, assignment):
    unsatisfied_clauses = set()
    for idx, clause in enumerate(clauses):
        if not evaluate_clause(clause, assignment):
            unsatisfied_clauses.add(idx)
    return unsatisfied_clauses

# 翻转一个字面值所对应的变量
def flip_random_variable(clause, assignment):
    literal = random.choice(clause)
    var = abs(literal) - 1  # 变量的索引是从 0 开始的
    assignment[var] = not assignment[var]

# 求解CNF公式，设置超时限制和随机种子
def solve_cnf(filename, max_flips=1000000, timeout=3600, seed=None):
    if seed is not None:
        random.seed(seed)  # 设置随机种子
    
    clauses, variable_to_clauses = read_dimacs(filename)
    num_variables = max(abs(literal) for clause in clauses for literal in clause)
    assignment = random_assignment(clauses, num_variables)
    
    unsatisfied_clauses = get_unsatisfied_clauses(clauses, assignment)
    
    start_time = time.time()  # 记录开始时间
    
    for _ in range(max_flips):
        if not unsatisfied_clauses:
            return assignment
        
        # 检查超时
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            print(f"Timeout reached for {filename} after {elapsed_time:.2f} seconds.")
            return None
        
        # 随机选择一个未满足的子句
        random_clause_idx = random.choice(list(unsatisfied_clauses))
        random_clause = clauses[random_clause_idx]
        
        # 翻转一个变量
        flip_random_variable(random_clause, assignment)
        
        # 更新未满足子句集合
        unsatisfied_clauses = get_unsatisfied_clauses(clauses, assignment)
    
    return None

# 将求解结果保存到文件
def save_result(filename, solution, elapsed_time, result_folder, seed):
    result_file = os.path.join(result_folder, os.path.basename(filename) + f"_seed{seed}_result.txt")
    with open(result_file, 'w') as f:
        f.write(f"File: {filename}\n")
        f.write(f"Time taken: {elapsed_time:.2f} seconds\n")
        if solution:
            f.write("Satisfying assignment found:\n")
            for var in range(len(solution)):
                f.write(f"Variable {var + 1}: {'True' if solution[var] else 'False'}\n")
        else:
            f.write("No satisfying assignment found.\n")

# # 处理单个CNF文件并保存结果（确保并行执行每个种子）
# def process_cnf_file(filename, result_folder, timeout, seed_range=10):
#     # 使用 ProcessPoolExecutor 并行执行每个种子的求解
#     with ProcessPoolExecutor() as executor:
#         futures = []
#         for seed in range(1, seed_range + 1):  # 重复多次，种子从1到10
#             futures.append(executor.submit(run_single_seed, filename, result_folder, timeout, seed))
        
#         # 等待所有任务完成
#         for future in futures:
#             future.result()  # 阻塞等待每个进程的结果

# 执行单次种子求解并保存结果
def run_single_seed(filename, result_folder, timeout, seed):
    start_time = time.time()
    solution = solve_cnf(filename, timeout=timeout, seed=seed)
    elapsed_time = time.time() - start_time
    save_result(filename, solution, elapsed_time, result_folder, seed)
    print(f"Finished processing {filename} with seed {seed} in {elapsed_time:.2f} seconds.")

# 遍历文件夹并求解每个.cnf文件
def solve_all_cnf_in_directory(directory, result_folder, timeout=3600, max_workers=32):
    os.makedirs(result_folder, exist_ok=True)  # 创建结果文件夹，如果不存在
    
    # 使用 ProcessPoolExecutor 来限制进程数
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for filename in os.listdir(directory):
            if filename.endswith('.cnf'):
                file_path = os.path.join(directory, filename)
                for seed in range(1, seed_range + 1):  # 重复多次，种子从1到10
                    futures.append(executor.submit(run_single_seed, file_path, result_folder, timeout, seed))


        # 等待所有任务完成
        for future in futures:
            future.result()  # 阻塞等待每个任务的结果

if __name__ == "__main__":
    directory = "/home/jiangtao/separation/328/LN"  # 设置文件夹路径
    result_folder = "/home/jiangtao/separation/328/walksatresult5"  # 结果保存路径
    max_workers = 120  # 设置最大工作进程数（与你的 CPU 核心数接近）
    solve_all_cnf_in_directory(directory, result_folder, timeout=3600, max_workers=max_workers)
