#!/usr/bin/env python3
"""
SAT solver with DPLL, random assignment order, multiple restart strategies, and time measurement:
- none:        无重启
- fixed:       固定间隔重启
- exponential: 指数间隔重启
- luby:        动态 Luby 重启(无限扩展)

特点:
1. 变量选择随机（使用 get_counter(formula) 后随机选）
2. 对选定变量的赋值先后顺序也随机 (先 True / 再 False 或相反)
3. 当选择 Luby 重启时, 动态生成 Luby 序列, 不会用尽
4. 统计并输出 **全局单调递增** 的决策次数（global_decision_id）
5. 统计并输出求解时间
"""

import sys
import random
import argparse
import time

sys.setrecursionlimit(10**7)

# ---------------------------
# 全局流水号计数器
# ---------------------------
global_decision_id = 0  # 每次做变量赋值决策时递增

def parse_dimacs(filename):
    """
    读取 DIMACS CNF 文件, 返回子句列表 (formula) 和变量个数 nvars
    """
    clauses = []
    nvars = 0
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            if line.startswith('p'):
                # e.g. p cnf <nvars> <nclauses>
                parts = line.split()
                nvars = int(parts[2])
                continue
            parts = line.split()
            if parts[-1] == '0':
                parts = parts[:-1]
            clause = [int(x) for x in parts]
            clauses.append(clause)
    return clauses, nvars


def bcp(formula, unit):
    """
    Boolean Constraint Propagation:
    - 若子句含 unit, 该子句为真 -> 跳过
    - 若子句含 -unit, 则删除 -unit
    - 若删除后子句为空 -> 冲突(返回 -1)
    """
    modified = []
    for clause in formula:
        if unit in clause:
            continue  # 已满足
        if -unit in clause:
            new_clause = [x for x in clause if x != -unit]
            if len(new_clause) == 0:
                return -1  # 冲突
            modified.append(new_clause)
        else:
            modified.append(clause)
    return modified


def get_counter(formula):
    """
    统计公式中每个文字出现的次数, 用于收集随机选择的候选.
    """
    counter = {}
    for clause in formula:
        for lit in clause:
            counter[lit] = counter.get(lit, 0) + 1
    return counter


def pure_literal(formula):
    """
    纯文字消元:
    - 若一个文字从未出现相反文字, 则直接赋值为真.
    """
    if not formula:
        return formula, []

    assignment = []
    counter = get_counter(formula)
    pures = []
    for lit in counter:
        if -lit not in counter:
            pures.append(lit)

    for pure in pures:
        formula = bcp(formula, pure)
        if formula == -1:
            return -1, []
        assignment.append(pure)

    return formula, assignment


def unit_propagation(formula):
    """
    单子句传播:
    - 若某子句仅剩一个文字, 则该文字必须为真.
    """
    if not formula:
        return formula, []

    assignment = []
    unit_clauses = [c for c in formula if len(c) == 1]
    while unit_clauses:
        unit_lit = unit_clauses[0][0]
        formula = bcp(formula, unit_lit)
        if formula == -1:
            return -1, []
        assignment.append(unit_lit)
        if not formula:
            return formula, assignment
        unit_clauses = [c for c in formula if len(c) == 1]
    return formula, assignment


def variable_selection(formula):
    """
    随机选取尚未赋值的文字 (用 get_counter 再随机挑)
    """
    counter = get_counter(formula)
    return random.choice(list(counter.keys()))


class LubyGenerator:
    """
    动态生成 Luby 序列, 不设固定上限.
    Luby序列: 1,1,2,1,1,2,4,1,1,2,4,8, ...
    用于重启间隔.
    """
    def __init__(self):
        self.seq = []
        self.partial_sums = [0]
        self.k = 1

    def _extend_sequence(self):
        """
        生成下一个 2^(k-1) 的块, 并更新 partial_sums
        """
        block_size = 1 << (self.k - 1)
        for _ in range(block_size):
            self.seq.append(block_size)
            self.partial_sums.append(self.partial_sums[-1] + block_size)
        self.k += 1

    def get_threshold(self, restart_count):
        """
        第 restart_count 次重启(从0开始), 所需阈值 = sum(seq[: restart_count+1])
        若序列不够长, 动态扩展.
        """
        needed_length = restart_count + 1
        while len(self.partial_sums) <= needed_length:
            self._extend_sequence()
        return self.partial_sums[restart_count + 1]


def backtracking_with_strategy(
    formula,
    assignment,
    strategy="none",
    fixed_interval=100000,
    exp_init=10,
    exp_factor=2,
    luby_gen=None,
    restart_count=0,
    max_decisions=1000000  # 添加 max_decisions 参数
):
    """
    DPLL 主递归函数:
    - 随机变量选择
    - 对选中变量, 随机决定先赋 True 还是先 False
    - 根据不同策略判断是否重启
    - 返回 (solution, final_decisions)

    注意:
    我们用全局变量 global_decision_id 来记录“已做多少次决策”。
    每次选出一个变量时, global_decision_id += 1, 并输出日志。
    """
    global global_decision_id

    # 如果达到了最大决策数，返回超时
    if global_decision_id >= max_decisions:
        print("c TIMEOUT: Max decision limit reached.")
        return ([], global_decision_id)

    # 纯文字消元
    formula, pure_assign = pure_literal(formula)
    if formula == -1:
        return ([], global_decision_id)
    if not formula:
        return (assignment + pure_assign, global_decision_id)

    # 单子句传播
    formula, unit_assign = unit_propagation(formula)
    if formula == -1:
        return ([], global_decision_id)
    if not formula:
        return (assignment + pure_assign + unit_assign, global_decision_id)

    # 更新 assignment
    assignment = assignment + pure_assign + unit_assign

    # 随机选取变量
    variable = variable_selection(formula)
    # 计一次决策
    global_decision_id += 1

    # -------------------------------------------------
    # 重启判断
    # -------------------------------------------------
    if strategy == "none":
        pass
    elif strategy == "fixed":
        # 每 fixed_interval 次决策 => 重启
        if global_decision_id % fixed_interval == 0:
            restart_count += 1
            # 清空 assignment，返回回溯起点
            return backtracking_with_strategy(
                formula, [],
                strategy=strategy,
                fixed_interval=fixed_interval,
                exp_init=exp_init,
                exp_factor=exp_factor,
                luby_gen=luby_gen,
                restart_count=restart_count,
                max_decisions=max_decisions  # 传递 max_decisions
            )

    elif strategy == "exponential":
        # 第 restart_count 次重启的阈值 => exp_init*(exp_factor^restart_count)
        current_interval = exp_init * (exp_factor ** restart_count)
        if global_decision_id >= current_interval:
            restart_count += 1
            return backtracking_with_strategy(
                formula, [],
                strategy=strategy,
                fixed_interval=fixed_interval,
                exp_init=exp_init,
                exp_factor=exp_factor,
                luby_gen=luby_gen,
                restart_count=restart_count,
                max_decisions=max_decisions  # 传递 max_decisions
            )

    elif strategy == "luby":
        if luby_gen is None:
            luby_gen = LubyGenerator()
        threshold = luby_gen.get_threshold(restart_count)
        if global_decision_id >= threshold:
            restart_count += 1
            return backtracking_with_strategy(
                formula, [],
                strategy=strategy,
                fixed_interval=fixed_interval,
                exp_init=exp_init,
                exp_factor=exp_factor,
                luby_gen=luby_gen,
                restart_count=restart_count,
                max_decisions=max_decisions  # 传递 max_decisions
            )

    # 随机决定先尝试 True 或 False
    if random.random() < 0.5:
        first_choice, second_choice = variable, -variable
    else:
        first_choice, second_choice = -variable, variable

    # 尝试 first_choice
    fc_formula = bcp(formula, first_choice)
    if fc_formula != -1:
        sol, decs = backtracking_with_strategy(
            fc_formula, assignment + [first_choice],
            strategy=strategy,
            fixed_interval=fixed_interval,
            exp_init=exp_init,
            exp_factor=exp_factor,
            luby_gen=luby_gen,
            restart_count=restart_count,
            max_decisions=max_decisions  # 传递 max_decisions
        )
        if sol:
            return (sol, decs)

    # 尝试 second_choice
    sc_formula = bcp(formula, second_choice)
    if sc_formula != -1:
        sol, decs = backtracking_with_strategy(
            sc_formula, assignment + [second_choice],
            strategy=strategy,
            fixed_interval=fixed_interval,
            exp_init=exp_init,
            exp_factor=exp_factor,
            luby_gen=luby_gen,
            restart_count=restart_count,
            max_decisions=max_decisions  # 传递 max_decisions
        )
        if sol:
            return (sol, decs)

    # 都失败 => 回溯
    return ([], global_decision_id)


def main():
    parser = argparse.ArgumentParser(description="SAT solver with random assignment & multiple restart strategies, time measure.")
    parser.add_argument("cnf_file", help="Input CNF file")
    parser.add_argument("seed", type=int, help="Random seed")
    parser.add_argument("--restart", choices=["none","fixed","exponential","luby"], default="none",
                        help="Restart strategy (default=none)")
    parser.add_argument("--interval", type=int, default=100000,
                        help="Interval for fixed restart (default=100)")
    parser.add_argument("--init", type=int, default=10,
                        help="Initial interval for exponential restart (default=10)")
    parser.add_argument("--factor", type=int, default=2,
                        help="Exponent factor for exponential restart (default=2)")
    parser.add_argument("--max-decisions", type=int, default=1000000,
                        help="Max number of decisions before giving up (default=1000000)")
    args = parser.parse_args()

    random.seed(args.seed)

    start_time = time.time()

    clauses, nvars = parse_dimacs(args.cnf_file)

    solution, final_decisions = backtracking_with_strategy(
        formula=clauses,
        assignment=[],
        strategy=args.restart,
        fixed_interval=args.interval,
        exp_init=args.init,
        exp_factor=args.factor,
        max_decisions=args.max_decisions  # 传递 max_decisions
    )

    end_time = time.time()
    total_time = end_time - start_time

    # 输出结果
    if solution:
        assigned_vars = set(abs(x) for x in solution)
        for v in range(1, nvars+1):
            if v not in assigned_vars:
                solution.append(v)
        solution.sort(key=lambda x: abs(x))
        print("s SATISFIABLE")
        # print("v " + " ".join(map(str, solution)) + " 0")
    else:
        print("s UNSATISFIABLE")

    # 输出决策次数
    print(f"variable_selection was called {final_decisions} times.")
    print(f"c Time: {total_time:.4f} seconds")


if __name__ == "__main__":
    main()
