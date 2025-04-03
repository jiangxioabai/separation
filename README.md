# Separation between Walksat and DPLL

This repository contains three part:
1. **CNF Generator**
2. **DPLL SAT Solver**
3. **Walksat SAT Solver**

## CNF Generator

This repository contains a script for generating CNF formulas based on various graph types using the Tseitin transformation. It supports graph types such as trees, grids, bipartite graphs, and more, and outputs them in the DIMACS CNF format.

### Requirements

Ensure the following Python dependencies are installed:

- `networkx`
- `matplotlib`
- `cnfgen` ([local module](https://github.com/MassimoLauria/cnfgen))

### Usage

The script `generatetseitin.py` generates CNF formulas for different graph types. To run the script, use the following command:

```bash
python3 generatetseitin.py <graph_type> <start_nodes> <max_nodes> <step> <instances_per_size>

   ```

### Arguments:
<graph_type>: Specifies the type of graph to generate. Possible values are:
  - tree: Random tree
  - grid: 2D grid graph
  - regular: Random regular graph with degree 4
  - L_n: Defined in the referenced paper

<start_nodes>: The starting number of nodes for the graph.
<max_nodes>: The maximum number of nodes for the graph.
<step>: The step size for generating graphs with increasing node numbers.
<instances_per_size>: The number of instances to generate for each graph size.




## DPLL SAT Solver
This project implements a SAT solver based on the DPLL algorithm, supporting four different restart strategies:

-none: No restarts

-fixed: Fixed interval restarts

-exponential: Exponential interval restarts

-luby: Luby sequence restarts

### Usage


1. **No restart**  
   ```bash
   python3 solver_with_restarts.py test.cnf 42 --restart none
   ```

2. **ixed interval restart** (e.g., restart every 100000 decisions)
   ```bash
   python3 solver_with_restarts.py test.cnf 42 --restart fixed --interval 100000
   ```

3. **Exponential interval restart** 
   ```bash
   python3 solver_with_restarts.py test.cnf 42 --restart exponential --init 10 --factor 2
   ```

4. **Luby restart**
   ```bash
   python3 solver_with_restarts.py test.cnf 42 --restart luby
   ```

> Note: To limit the maximum number of decisions, add the `--max-decisions` argument, for example:
> ```bash
> python3 solver_with_restarts.py test.cnf 42 --restart fixed --interval 100 --max-decisions 100000
> ```

## Parameters

- **`cnf_file`**: Input DIMACS format CNF file path.
- **`seed`**: Random seed (used for variable selection).
- **`--restart`**: Restart strategy, which can be `none|fixed|exponential|luby`:
  - `none`: No restart.
  - `fixed`: Restart every fixed interval (specified by `--interval`).
  - `exponential`: Restart at exponentially increasing intervals, starting from `--init` and multiplying by `--factor` each time.
  - `luby`: Use Luby restart strategy.
- **`--interval`**: Interval for fixed restart (default: 100).
- **`--init`**: Initial interval for exponential restart (default: 10).
- **`--factor`**: Multiplication factor for exponential restart (default: 2).
- **`--max-decisions`**: Stop if the number of decisions exceeds this value without finding a solution (default: 1000000).


Example：  
```bash
python3 solver_with_restarts.py test.cnf 42 --restart exponential --init 10 --factor 2 --max-decisions 50000
```
This command will solve the `test.cnf` file with seed 42, using exponential restarts, starting with an interval of 10, doubling each time, and allowing up to 50,000 decisions.

## Walksat

This part implements a CNF solver that uses random assignments to solve SAT problems. The solver performs flips on variables until it either finds a satisfying assignment or exceeds the maximum allowed flips or timeout.

## Requirements

- Python 3
- `bitarray` module (install via `pip install bitarray`)

## Usage

You can run the script to solve a single CNF file with a specified timeout and seed.

### Command-Line Usage

```bash
python3 solve_cnf.py <cnf_file> <result_folder> [--timeout <timeout>] [--seed <seed>]

