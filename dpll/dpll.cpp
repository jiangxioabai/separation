#include <random>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
#include <cstdlib> // 用于atoi

using namespace std;

// 全局未赋值变量列表
vector<int> unassigned_vars;

/*
 * enum for different types of return flags defined
 */
enum Cat {
  satisfied,   // when a satisfying assignment has been found
  unsatisfied, // when no satisfying assignment has been found after exhaustive searching
  normal,      // when DPLL has exited normally
  completed    // when the DPLL algorithm has completed execution
};

/*
 * class to represent a boolean formula
 */
class Formula {
public:
  vector<int> literals;        // 存储每个变量的赋值
  vector<vector<int>> clauses; // 存储子句

  Formula() {}

  Formula(const Formula &f) {
    literals = f.literals;
    clauses = f.clauses;
  }
};

/*
 * class to represent the structure and functions of the SAT Solver
 */
class SATSolverDPLL {
private:
  Formula formula;               // the initial formula given as input
  int literal_count;             // the number of variables in the formula
  int clause_count;              // the number of clauses in the formula
  unsigned int rand_seed;        // 存储随机种子
  mt19937 gen;                   // 随机数生成器
  int unit_propagate(Formula &); // performs unit propagation
  int DPLL(Formula &);           // performs DPLL recursively
  int apply_transform(Formula &, int); // applies the value of the literal in every clause
  void show_result(Formula &, int);    // displays the result

public:
  int select_count;              // 统计select_random_literal调用的次数
  SATSolverDPLL() : rand_seed(0), gen(rand_seed) {}
  void initialize(); // Initializes the values
  void solve();      // Calls the solver
  void set_seed(unsigned int seed) { rand_seed = seed; gen = mt19937(rand_seed); } // 设置随机种子
  int select_random_literal(Formula &f);
  void assign_random_value(Formula &f, int literal_index);
};

/*
 * function that accepts the inputs from the user and initializes the attributes
 * in the solver
 */
void SATSolverDPLL::initialize() {
  select_count = 0;
  char c;   // store first character
  string s; // dummy string

  while (true) {
    cin >> c;
    if (c == 'c') { // if comment
      getline(cin, s); // ignore
    } else { // else, if would be a p
      cin >> s; // this would be cnf
      break;
    }
  }
  cin >> literal_count;
  cin >> clause_count;

  // set the vectors to their appropriate sizes and initial values
  formula.literals.clear();
  formula.literals.resize(literal_count, -1);
  formula.clauses.clear();
  formula.clauses.resize(clause_count);

  int literal; // store the incoming literal value
  // iterate over the clauses
  for (int i = 0; i < clause_count; i++) {
    while (true) { // while the ith clause gets more literals
      cin >> literal;
      if (literal > 0) { // if the variable has positive polarity
        formula.clauses[i].push_back(2 * (literal - 1)); // store it in the form 2n
      } else if (literal < 0) { // if the variable has negative polarity
        formula.clauses[i].push_back(2 * ((-1) * literal - 1) + 1); // store it in the form 2n+1
      } else {
        break; // read 0, so move to next clause
      }
    }
  }

  // 将所有变量加入 unassigned_vars
  unassigned_vars.clear(); // 清空之前的数据
  for (int i = 0; i < literal_count; i++) {
    unassigned_vars.push_back(i); // 将所有变量编号添加进 unassigned_vars
  }
}

/*
 * function to perform unit resolution in a given formula
 * arguments: f - the formula to perform unit resolution on
 * return value: int - the status of the solver after unit resolution, a member
 * of the Cat enum
 *               Cat::satisfied - the formula has been satisfied
 *               Cat::unsatisfied - the formula can no longer be satisfied
 *               Cat::normal - normal exit
 */
int SATSolverDPLL::unit_propagate(Formula &f) {
  bool unit_clause_found = false;
  if (f.clauses.size() == 0) { // if the formula contains no clauses
    return Cat::satisfied; // it is vacuously satisfied
  }

  do {
    unit_clause_found = false;
    // iterate over the clauses in f
    for (int i = 0; i < f.clauses.size(); i++) {
      if (f.clauses[i].size() == 1) { // if the size of a clause is 1, it is a unit clause
        unit_clause_found = true;
        f.literals[f.clauses[i][0] / 2] = f.clauses[i][0] % 2; // 0 - if true, 1 - if false, set the literal
        // Remove from unassigned_vars
        unassigned_vars.erase(remove(unassigned_vars.begin(), unassigned_vars.end(), f.clauses[i][0] / 2), unassigned_vars.end());
        int result = apply_transform(f, f.clauses[i][0] / 2); // apply this change through f
        // if this caused the formula to be either satisfied or unsatisfied,
        // return the result flag
        if (result == Cat::satisfied || result == Cat::unsatisfied) {
          return result;
        }
        break; // exit the loop to check for another unit clause from the start
      } else if (f.clauses[i].size() == 0) { // if a given clause is empty
        return Cat::unsatisfied; // the formula is unsatisfiable in this branch
      }
    }
  } while (unit_clause_found);

  return Cat::normal; // if reached here, the unit resolution ended normally
}

/*
 * applies a value of a literal to all clauses in a given formula
 * arguments: f - the formula to apply on
 *            literal_to_apply - the literal which has just been set
 * return value: int - the return status flag, a member of the Cat enum
 *               Cat::satisfied - the formula has been satisfied
 *               Cat::unsatisfied - the formula can no longer be satisfied
 *               Cat::normal - normal exit
 */
int SATSolverDPLL::apply_transform(Formula &f, int literal_to_apply) {
  int value_to_apply = f.literals[literal_to_apply]; // 获取文字的值
  for (int i = 0; i < f.clauses.size(); i++) {
    for (int j = 0; j < f.clauses[i].size(); j++) {
      if ((2 * literal_to_apply + value_to_apply) == f.clauses[i][j]) {
        f.clauses.erase(f.clauses.begin() + i); // 删除子句
        i--;
        if (f.clauses.size() == 0) {
          return Cat::satisfied;
        }
        break;
      } else if (f.clauses[i][j] / 2 == literal_to_apply) {
        f.clauses[i].erase(f.clauses[i].begin() + j); // 删除文字
        j--;
        if (f.clauses[i].size() == 0) {
          return Cat::unsatisfied;
        }
        break;
      }
    }
  }
  return Cat::normal; // 如果没有满足或冲突，返回正常状态
}

/*
 * function to perform the recursive DPLL on a given formula
 * argument: f - the formula to perform DPLL on
 * return value: int - the return status flag, a member of the Cat enum
 *               Cat::normal - exited normally
 *               Cat::completed - result has been found, exit recursion all the way
 */
int SATSolverDPLL::select_random_literal(Formula &f) {
  // 如果 unassigned_vars 为空，表示所有变量已被赋值
  if (unassigned_vars.empty()) {
    return -1; // 没有可选变量
  }

  // 使用用户提供的随机种子来初始化随机数生成器
  uniform_int_distribution<> dis(0, unassigned_vars.size() - 1);
  int random_index = dis(gen);
  select_count++;
  int selected_literal = unassigned_vars[random_index];

  // 从列表中删除选中的变量
  unassigned_vars.erase(unassigned_vars.begin() + random_index);

  return selected_literal; // 返回选中的变量
}

// 给选中的变量随机赋值
void SATSolverDPLL::assign_random_value(Formula &f, int literal_index) {
  // 使用用户提供的随机种子来初始化随机数生成器
  uniform_int_distribution<> dis(0, 1); // 随机选择 true 或 false

  // 随机赋值
  int random_value = dis(gen);
  f.literals[literal_index] = random_value; // 赋值
}

int SATSolverDPLL::DPLL(Formula &f) {
  int result = unit_propagate(f); // 执行单位传播
  if (result == Cat::satisfied) {
    show_result(f, result);
    return Cat::completed;
  } else if (result == Cat::unsatisfied) {
    return Cat::normal;
  }

  // 随机选择一个未赋值的变量
  int i = select_random_literal(f);
  if (i == -1) {
    return Cat::normal; // 没有可选的变量，结束
  }

  // 随机赋值：0 为 true，1 为 false
  for (int j = 0; j < 2; j++) {
    Formula new_f = f; // 复制公式
    assign_random_value(new_f, i); // 给选中的变量赋随机值

    // 更新子句
    int transform_result = apply_transform(new_f, i); // 应用赋值到公式
    if (transform_result == Cat::satisfied) {
      show_result(new_f, transform_result);
      return Cat::completed;
    } else if (transform_result == Cat::unsatisfied) {
      continue;
    }

    // 递归调用DPLL
    int dpll_result = DPLL(new_f);
    if (dpll_result == Cat::completed) {
      return dpll_result;
    }
  }

  // 回溯时，将变量重新加入未赋值列表
  unassigned_vars.push_back(i);

  return Cat::normal;
}

/*
 * function to display the result of the solver
 * arguments: f - the formula when it was satisfied or shown to be unsatisfiable
 *            result


/*
 * function to display the result of the solver
 * arguments: f - the formula when it was satisfied or shown to be unsatisfiable
 *            result - the result flag, a member of the Cat enum
 */
void SATSolverDPLL::show_result(Formula &f, int result) {
  if (result == Cat::satisfied) {
    cout << "SAT" << endl;
    for (int i = 0; i < f.literals.size(); i++) {
      if (i != 0) {
        cout << " ";
      }
      if (f.literals[i] != -1) {
        cout << pow(-1, f.literals[i]) * (i + 1);
      } else {
        cout << (i + 1);
      }
    }
    cout << " 0";
  } else {
    cout << "UNSAT";
  }
}

/*
 * function to call the solver
 */
void SATSolverDPLL::solve() {
  int result = DPLL(formula); // final result of DPLL on the original formula
  // if normal return till the end, then the formula could not be satisfied in
  // any branch, so it is unsatisfiable
  if (result == Cat::normal) {
    show_result(formula, Cat::unsatisfied); // the argument formula is a dummy
                                             // here, the result is UNSAT
  }
}



int main(int argc, char *argv[]) {
  SATSolverDPLL solver; // 创建求解器

  // 检查命令行参数，如果提供了随机种子
  if (argc > 1) {
    unsigned int seed = atoi(argv[1]);  // 获取第一个命令行参数作为种子
    solver.set_seed(seed);  // 设置随机种子
  } else {
    cout << "No seed provided. Using default seed." << endl;
  }

  solver.initialize();  // 初始化
  solver.solve();       // 求解

  // 打印 select_random_literal 被调用的次数
  cout << "\nselect_random_literal called " 
       << solver.select_count // 直接访问 public 的成员变量
       << " times." << endl;

  return 0;
}
