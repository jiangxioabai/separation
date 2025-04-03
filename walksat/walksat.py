import os
import time
from bitarray import bitarray
import random
import argparse

# 读取DIMACS文件
def read_dimacs(filename):
    clauses = []
    variable_to_clauses = {}
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
                variable_to_clauses[var].add(len(clauses) - 1)
    return clauses, variable_to_clauses

# 随机赋值，使用位向量存储赋值
def random_assignment(clauses, num_variables):
    assignment = bitarray(num_variables)
    assignment.setall(False)
    for i in range(num_variables):
        assignment[i] = random.choice([True, False])
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
    var = abs(literal) - 1
    assignment[var] = not assignment[var]

# 求解CNF公式，设置超时限制和随机种子
def solve_cnf(filename, max_flips=1000000, timeout=36000, seed=None):
    if seed is not None:
        random.seed(seed)
    
    clauses, variable_to_clauses = read_dimacs(filename)
    num_variables = max(abs(literal) for clause in clauses for literal in clause)
    assignment = random_assignment(clauses, num_variables)
    
    unsatisfied_clauses = get_unsatisfied_clauses(clauses, assignment)
    
    start_time = time.time()
    flip_count = 0
    for _ in range(max_flips):
        if not unsatisfied_clauses:
            return assignment, flip_count
        
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            print(f"Timeout reached for {filename} after {elapsed_time:.2f} seconds.")
            return None, flip_count
        
        random_clause_idx = random.choice(list(unsatisfied_clauses))
        random_clause = clauses[random_clause_idx]
        flip_random_variable(random_clause, assignment)
        flip_count += 1
        unsatisfied_clauses = get_unsatisfied_clauses(clauses, assignment)
    
    return None, flip_count

# 将求解结果保存到文件
def save_result(filename, solution, elapsed_time, flip_count, result_folder, seed):
    result_file = os.path.join(result_folder, os.path.basename(filename) + f"_seed{seed}_result.txt")
    with open(result_file, 'w') as f:
        f.write(f"File: {filename}\n")
        f.write(f"Time taken: {elapsed_time:.2f} seconds\n")
        f.write(f"Flip count: {flip_count}\n")
        
        if solution:
            f.write("Satisfying assignment found:\n")
        else:
            f.write("No satisfying assignment found.\n")

# 执行单个种子求解并保存结果
def run_single_seed(filename, result_folder, timeout, seed):
    start_time = time.time()
    solution, flip_count = solve_cnf(filename, timeout=timeout, seed=seed)
    elapsed_time = time.time() - start_time
    save_result(filename, solution, elapsed_time, flip_count, result_folder, seed)
    print(f"Finished processing {filename} with seed {seed} in {elapsed_time:.2f} seconds.")

# 通过命令行传入参数
def main():
    parser = argparse.ArgumentParser(description="Solve a single CNF file using random assignments.")
    parser.add_argument("cnf_file", help="The CNF file to solve.")
    parser.add_argument("result_folder", help="Folder to save the result.")
    parser.add_argument("--timeout", type=int, default=3600, help="Timeout for solving the CNF file (default: 3600 seconds).")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for the solver (optional).")
    args = parser.parse_args()

    run_single_seed(args.cnf_file, args.result_folder, timeout=args.timeout, seed=args.seed)

if __name__ == "__main__":
    main()

