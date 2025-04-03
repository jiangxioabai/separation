# CNF Formula Generator

This repository contains a script for generating CNF formulas based on various graph types using the Tseitin transformation. It supports graph types such as trees, grids, bipartite graphs, and more, and outputs them in the DIMACS CNF format.

## Requirements

Ensure the following Python dependencies are installed:

- `networkx`
- `matplotlib`
- `cnfgen` ([local module](https://github.com/MassimoLauria/cnfgen))

## Usage

The script `generatetseitin.py` generates CNF formulas for different graph types. To run the script, use the following command:

```bash
python3 generatetseitin.py <graph_type> <start_nodes> <max_nodes> <step> <instances_per_size>
   ```

## Arguments:
<graph_type>: Specifies the type of graph to generate. Possible values are:
  - tree: Random tree
  - grid: 2D grid graph
  - regular: Random regular graph with degree 4
  - L_n: Defined in the referenced paper

<start_nodes>: The starting number of nodes for the graph.
<max_nodes>: The maximum number of nodes for the graph.
<step>: The step size for generating graphs with increasing node numbers.
<instances_per_size>: The number of instances to generate for each graph size.




# DPLL with Restarts

本项目包含一个基于 DPLL 的 SAT 求解器，并支持以下 4 种重启策略：
- **none**：无重启  
- **fixed**：固定间隔重启  
- **exponential**：指数间隔重启  
- **luby**：Luby 序列重启  

## 使用方法

以下是常见的命令行示例：

1. **无重启**  
   ```bash
   python3 solver_with_restarts.py test.cnf 42 --restart none
   ```

2. **固定间隔重启** (例如每 100 次决策重启一次)  
   ```bash
   python3 solver_with_restarts.py test.cnf 42 --restart fixed --interval 100
   ```

3. **指数间隔重启** (例如初始间隔 10，每次重启后乘以因子 2)  
   ```bash
   python3 solver_with_restarts.py test.cnf 42 --restart exponential --init 10 --factor 2
   ```

4. **Luby 重启** (生成长度为 1000 的 Luby 序列)  
   ```bash
   python3 solver_with_restarts.py test.cnf 42 --restart luby --luby-limit 1000
   ```

> 注意：若需要限制最大决策次数，可以加上 `--max-decisions` 参数，例如：
> ```bash
> python3 solver_with_restarts.py test.cnf 42 --restart fixed --interval 100 --max-decisions 100000
> ```

## 参数说明

- **`cnf_file`**: 输入的 DIMACS 格式 CNF 文件路径。  
- **`seed`**: 随机种子 (用于控制随机变量选择)。  
- **`--restart`**: 重启策略，可取 `none|fixed|exponential|luby`：  
  - `none`：不进行任何重启。  
  - `fixed`：每隔固定间隔（由 `--interval` 指定）重启一次。  
  - `exponential`：使用指数增长间隔重启，起始值由 `--init` 指定，每次重启后乘以 `--factor`。  
  - `luby`：使用 Luby 重启策略，序列长度由 `--luby-limit` 控制。  
- **`--interval`**: 固定间隔重启时，每隔多少“决策次数”进行一次重启。(默认：100)  
- **`--init`**: 指数间隔重启的初始间隔。(默认：10)  
- **`--factor`**: 指数间隔重启的倍增因子。(默认：2)  
- **`--luby-limit`**: 生成的 Luby 序列最大长度。(默认：1000)  
- **`--max-decisions`**: 若决策次数超过此值还没找到解，则停止并返回 `UNSAT`。(默认：100000)

示例：  
```bash
python3 solver_with_restarts.py test.cnf 42 --restart exponential --init 10 --factor 2 --max-decisions 50000
```
上面表示：对于文件 `test.cnf`，随机种子为 42，使用 **指数重启**，初始间隔是 10，每次重启后间隔乘以 2，最多允许 50,000 次决策。

---

若需要进一步测试或查看策略的效果，可自行修改和观察运行结果、求解时间、重启次数等指标。

