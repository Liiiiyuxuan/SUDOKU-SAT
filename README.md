# Mini Project – SAT-based Sudoku Solving

**Collaborators:** Eason Li (21069463) and Michael Mao (21070968)

## Overview

This project implements a SAT-based Sudoku solver that converts Sudoku puzzles into Boolean satisfiability (SAT) problems in DIMACS CNF format, solves them using MiniSAT, and converts the solutions back into Sudoku grids. The project compares two encoding strategies: a minimal encoding and an extended encoding that includes redundant constraints for better solver performance.

## Contents of Submission

### Core Programs

1. **`sud2sat_basic.cpp`** – Minimal encoding implementation

   - Converts Sudoku puzzles to DIMACS CNF format using a minimal set of constraints
   - Implements: cell-at-least-one, row/column/box at-most-one constraints
   - Compiles to executable: `sud2sat`

2. **`sud2sat_extended.cpp`** – Extended encoding implementation

   - Combines minimal encoding with additional redundant constraints
   - Adds: cell-at-most-one, row/column/box at-least-one constraints
   - Compiles to executable: `sud2sat1`
   - Provides stronger propagation, reducing solver search effort

3. **`sat2sud.cpp`** – Solution decoder
   - Converts MiniSAT assignment output back to a 9×9 Sudoku grid
   - Reads SAT/UNSAT status and variable assignments
   - Outputs solved puzzle in standard format (9 lines of 9 digits)

### Build Scripts

4. **`solve.sh`** – Main solving script

   - Usage: `./solve.sh <run_number>`
   - Pipeline: `sud2sat` -> `minisat` -> `sat2sud`
   - Processes puzzles from `input/<run>sudoku.in`

5. **`solve1.sh`** – Alternative solving script for extended encoding
   - Usage: `./solve1.sh <run_number>`
   - Uses `sud2sat1` (extended encoding) instead of `sud2sat`

## Encoding Strategies

### Minimal Encoding (`sud2sat`)

The minimal encoding uses the following constraints:

- **Cell-at-least-one**: Each cell must contain at least one digit (1-9)
- **Row-at-most-one**: Each digit appears at most once per row
- **Column-at-most-one**: Each digit appears at most once per column
- **Box-at-most-one**: Each digit appears at most once per 3×3 box

**Clause count:** ~8,829 clauses (for puzzles with givens)

### Extended Encoding (`sud2sat1`)

The extended encoding adds redundant constraints to the minimal encoding:

- All constraints from minimal encoding, plus:
- **Cell-at-most-one**: Each cell contains at most one digit (explicit pairwise constraints)
- **Row-at-least-one**: Each digit appears at least once per row
- **Column-at-least-one**: Each digit appears at least once per column
- **Box-at-least-one**: Each digit appears at least once per 3×3 box

**Clause count:** ~9,093-9,526 clauses (depending on puzzle)

**Performance benefits:**

- ~15-33× fewer conflicts
- ~11-12× fewer decisions
- ~28-80% fewer propagations
- Stronger unit propagation, reducing search space

### Compilation

```bash
# Compile minimal encoding
g++ -o sud2sat sud2sat_basic.cpp

# Compile extended encoding
g++ -o sud2sat1 sud2sat_extended.cpp

# Compile solution decoder
g++ -o sat2sud sat2sud.cpp
```

### Basic Usage

```bash
# Solve a puzzle using minimal encoding
./solve.sh 0

# Solve using extended encoding
./solve1.sh 0

# Manual pipeline for minimal encoding
./sud2sat < puzzle.in > puzzle.cnf
minisat puzzle.cnf puzzle.assign > puzzle.stat
./sat2sud < puzzle.assign > puzzle.solution

# Manual pipeline for extended encoding
./sud2sat1 < puzzle.in > puzzle.cnf
minisat puzzle.cnf puzzle.assign > puzzle.stat
./sat2sud < puzzle.assign > puzzle.solution
```

### Puzzle Format

Puzzles are read as 81 characters (9×9 grid) with:

- Digits `1-9` for given clues
- `0`, `.`, `*`, or `?` for empty cells
- Whitespace is ignored

Example:

```
003020600
900305001
001806400
003020600
900305001
001806400
003020600
900305001
001806400
...
```

## Evaluation Results

See summarize1.txt and summarize2.txt for details. 

### Variable Encoding

Each variable `v` represents: "Cell (r, c) contains digit d"

- Encoding: `v = 81 × (r-1) + 9 × (c-1) + d`
- Range: 1 to 729 (9×9×9 = 729 variables)

### Inverse Mapping

Given variable `v`, decode to (r, c, d):

```cpp
v -= 1;
r = v / 81 + 1;
c = (v % 81) / 9 + 1;
d = (v % 81) % 9 + 1;
```

## Dependencies

- **MiniSAT** – SAT solver (must be installed and in PATH)
- **g++** – C++ compiler (C++11 or later)
- **Python 3** – For test harness (requires `statistics` module)

## File Structure

```
SUDOKU-SAT/
├── sud2sat_basic.cpp      # Minimal encoding source
├── sud2sat_extended.cpp   # Extended encoding source
├── sat2sud.cpp            # Solution decoder source
├── solve.sh               # Main solving script
├── solve1.sh              # Extended encoding script
├── test_harness.py        # Testing framework
├── input/                 # Test puzzles and outputs
├── p096/                  # Project Euler puzzle set
├── top95/                 # Hard puzzle benchmark
└── README.md              # This file
```

## Notes

- Both encodings produce satisfiable CNF formulas for valid Sudoku puzzles
- The extended encoding trades a small increase in clause count (~3-8%) for dramatically reduced solver effort
- All programs read from stdin by default, with optional file arguments
- Output follows DIMACS CNF format for SAT solvers
- Solutions are verified to be valid Sudoku grids (9×9, digits 1-9)
