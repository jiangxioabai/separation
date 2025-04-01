#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

TIME_LIMIT = 3600  # 1小时
NUM_SEEDS = 10     # 每个CNF文件跑10次，随机种子 1~10
MAX_WORKERS = 124 # 可以指定进程数，如 4；None 表示用系统默认(通常是CPU核心数)

def run_one_experiment(solver_script, cnf_path, seed):
    """
    在一个独立进程里运行一次实验：
    - 调用 solver_script (如 solver.py) 进行求解
    - 限时 TIME_LIMIT 秒
    - 返回 (seed, result, runtime, var_select_count)
    """
    cmd = ["python3", solver_script, cnf_path, str(seed)]
    start_time = time.time()
    solver_result = "UNKNOWN"
    var_select_count = -1
    runtime = 0.0

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIME_LIMIT
        )
        runtime = time.time() - start_time
        # 解析 solver.py 输出
        stdout_lines = completed.stdout.splitlines()
        for line in stdout_lines:
            line = line.strip()
            if line.startswith("s "):
                # e.g. "s SATISFIABLE" or "s UNSATISFIABLE"
                # line.split() => ["s", "SATISFIABLE"]
                solver_result = line.split()[1]
            if "variable_selection was called" in line:
                # e.g. "variable_selection was called 123 times."
                parts = line.split()
                var_select_count = int(parts[-2])

    except subprocess.TimeoutExpired:
        runtime = TIME_LIMIT
        solver_result = "TIMEOUT"
    except Exception as e:
        # 如果 solver 出现其它错误
        solver_result = f"ERROR-{type(e).__name__}"

    return (seed, solver_result, runtime, var_select_count)

def main():
    # 命令行：python3 experiment.py <solver_script> <cnf_folder> <results_folder>
    # 或者你也可以把 solver_script 固定写死，比如 "solver.py"
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <solver_script> <cnf_folder> <results_folder>")
        sys.exit(1)

    solver_script = sys.argv[1]
    cnf_folder = sys.argv[2]
    results_folder = sys.argv[3]

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    # 收集所有 .cnf 文件
    cnf_files = [f for f in os.listdir(cnf_folder) if f.endswith('.cnf')]
    cnf_files.sort()

    # 准备所有任务 (cnf_file, seed)
    tasks = []
    for cnf_file in cnf_files:
        full_cnf_path = os.path.join(cnf_folder, cnf_file)
        for seed in range(1, NUM_SEEDS+1):
            tasks.append((cnf_file, full_cnf_path, seed))

    # 并行执行
    # 每个任务（cnf_file, cnf_path, seed）会交给 run_one_experiment
    results_dict = {}  # key: cnf_file, value: list of (seed, result, runtime, var_select_count)

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 构造 future -> (cnf_file, seed) 的映射
        future_to_task = {}
        for (cnf_file, cnf_path, seed) in tasks:
            future = executor.submit(run_one_experiment, solver_script, cnf_path, seed)
            future_to_task[future] = (cnf_file, seed)

        # as_completed 可以让我们迭代已完成的任务
        for future in as_completed(future_to_task):
            cnf_file, seed = future_to_task[future]
            try:
                (the_seed, solver_result, runtime, var_select_count) = future.result()
            except Exception as exc:
                # 如果在 run_one_experiment 内部未处理的异常
                print(f"Task {cnf_file}, seed={seed} generated an exception: {exc}")
                the_seed, solver_result, runtime, var_select_count = seed, "ERROR", -1, -1

            # 把结果放入 results_dict
            if cnf_file not in results_dict:
                results_dict[cnf_file] = []
            results_dict[cnf_file].append((the_seed, solver_result, runtime, var_select_count))

    # 全部任务都完成后，把结果写到 results_folder 下的 CSV
    for cnf_file in cnf_files:
        # 文件名: <basename>_results.csv
        base_name = os.path.splitext(cnf_file)[0]
        result_csv_name = base_name + "_results.csv"
        result_csv_path = os.path.join(results_folder, result_csv_name)

        # 如果这个 cnf_file 在 results_dict 里没有，说明没有任务
        if cnf_file not in results_dict:
            continue

        # 写结果到 CSV
        with open(result_csv_path, 'w') as rf:
            rf.write("seed,result,runtime,variable_selection_count\n")
            # 排序一下seed, 让 1..10 的顺序输出
            results_for_this_cnf = sorted(results_dict[cnf_file], key=lambda x: x[0])
            for (seed, solver_result, runtime, var_select_count) in results_for_this_cnf:
                rf.write(f"{seed},{solver_result},{runtime:.4f},{var_select_count}\n")

        print(f"[Done] {cnf_file} => {result_csv_path}")

if __name__ == "__main__":
    main()
