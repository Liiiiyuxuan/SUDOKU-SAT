#!/usr/bin/env bash

# usage: ./solve.sh puzzle.txt 1
#        ./solve.sh puzzle.txt 2   # next run, etc.

puzzle="$1"
run="$2"          # e.g. 1, 2, 3...

if [ -z "$puzzle" ] || [ -z "$run" ]; then
    echo "Usage: $0 puzzle.txt run_number"
    exit 1
fi

./sud2sat < "sudoko$" > "sudoku${run}.cnf"
minisat "sudoku${run}.cnf" "assign_${run}.txt" > "stat_${run}.txt"
./sat2sud < "assign_${run}.txt" > "solution_${run}.txt"
cat "solution_${run}.txt"
