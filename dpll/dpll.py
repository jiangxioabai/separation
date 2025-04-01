#!/usr/bin/env python3
"""
    SAT solver based on DPLL
    Course in Advanced Programming in Artificial Intelligence - UdL
"""

import sys
import random

# 在这里定义一个全局变量，用来统计 variable_selection 的调用次数
variable_selection_count = 0
def parse(filename):
    clauses = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                # 跳过注释行和空行
                continue
            if line.startswith('p'):
                # 例如: p cnf 3 2
                # 取第3,4个元素分别是nvars, nclauses
                parts = line.split()
                nvars, nclauses = parts[2], parts[3]
                continue
            # 假设每行子句末尾会有一个 0，比如 "1 -2 0"
            # line[:-2] 是为了去掉 ' 0'，然后做 split
            # 如果不放心，可以用更通用的处理：
            # parts = [int(x) for x in line.split() if x != '0']
            clause = [int(x) for x in line[:-2].split()]
            clauses.append(clause)
    return clauses, int(nvars)

def bcp(formula, unit):
    """
    BCP (Boolean Constraint Propagation):
    给定公式 formula 和单元文字 unit，化简 formula 中包含 unit 的子句，
    并从包含 -unit 的子句中去掉 -unit。
    """
    modified = []
    for clause in formula:
        # 若子句包含 unit，整条子句为真，可直接跳过
        if unit in clause:
            continue
        # 若子句包含 -unit，需要去掉 -unit
        if -unit in clause:
            c = [x for x in clause if x != -unit]
            # 如果 c 为空，说明子句变成了空子句 -> 冲突返回 -1
            if len(c) == 0:
                return -1
            modified.append(c)
        else:
            modified.append(clause)
    return modified

def get_counter(formula):
    """
    统计 formula 中每个文字出现的次数
    """
    counter = {}
    for clause in formula:
        for literal in clause:
            if literal in counter:
                counter[literal] += 1
            else:
                counter[literal] = 1
    return counter

def pure_literal(formula):
    """
    纯文字消元：
    只要一个文字从未出现过相反符号，那么它是纯文字，可以将它赋为真
    并从公式里删除所有包含它的子句。
    """
    counter = get_counter(formula)
    assignment = []
    pures = []
    # 找出所有纯文字
    for literal, times in counter.items():
        if -literal not in counter:
            pures.append(literal)

    # 对每个纯文字执行 BCP
    for pure in pures:
        formula = bcp(formula, pure)

    assignment += pures
    return formula, assignment

def unit_propagation(formula):
    """
    单子句传播：
    如果公式中出现单子句，则其文字必须为真。
    """
    assignment = []
    # 找出所有单子句
    unit_clauses = [c for c in formula if len(c) == 1]
    while len(unit_clauses) > 0:
        unit = unit_clauses[0]
        formula = bcp(formula, unit[0])
        assignment.append(unit[0])
        if formula == -1:
            return -1, []
        if not formula:
            # 已经化简为空，说明可满足
            return formula, assignment
        unit_clauses = [c for c in formula if len(c) == 1]
    return formula, assignment

def variable_selection(formula):
    """
    随机选取尚未赋值的文字（Heuristic可以自行改进）
    """
    
    global variable_selection_count
    variable_selection_count += 1
    counter = get_counter(formula)
    # 在 Python 3 中，需要将 dict_keys 转成列表再给 random.choice
    return random.choice(list(counter.keys()))

def backtracking(formula, assignment):
    """
    主递归求解过程：
    1. 纯文字消元
    2. 单子句传播
    3. 递归尝试给下一个变量 True 或 False
    """
    formula, pure_assignment = pure_literal(formula)
    formula, unit_assignment = unit_propagation(formula)

    assignment = assignment + pure_assignment + unit_assignment
    if formula == -1:
        # 冲突 -> 回溯
        return []
    if not formula:
        # 空公式 -> 找到可行解
        return assignment

    # 选一个变量赋值
    variable = variable_selection(formula)

    # 先随机决定是给 variable 还是 -variable 赋值
    if random.random() < 0.5:
        first_choice, second_choice = variable, -variable
    else:
        first_choice, second_choice = -variable, variable

    solution = backtracking(bcp(formula, first_choice), assignment + [first_choice])
    if not solution:
        solution = backtracking(bcp(formula, second_choice), assignment + [second_choice])
    return solution


def main():
    # 命令行参数：python3 solver.py <input.cnf> [seed]
    if len(sys.argv) < 2:
        print("Usage: python3 solver.py <input.cnf> [<seed>]")
        sys.exit(1)

    filename = sys.argv[1]
    # 如果指定了种子，就设置随机种子
    if len(sys.argv) > 2:
        seed = int(sys.argv[2])
        random.seed(seed)

    clauses, nvars = parse(filename)
    solution = backtracking(clauses, [])

    if solution:
        # 补全所有没有出现的变量：如果没有出现在解中，就默认赋真
        solution += [x for x in range(1, nvars + 1) if x not in solution and -x not in solution]
        solution.sort(key=lambda x: abs(x))
        print("s SATISFIABLE")
        print("v " + " ".join([str(x) for x in solution]) + " 0")
    else:
        print("s UNSATISFIABLE")

    # 运行结束后，打印出 variable_selection 的调用次数
    global variable_selection_count
    print(f"variable_selection was called {variable_selection_count} times.")

if __name__ == "__main__":
    main()
