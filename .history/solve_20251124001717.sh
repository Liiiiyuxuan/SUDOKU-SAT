#!/usr/bin/env bash

# usage: ./solve.sh puzzle.txt 1
#        ./solve.sh puzzle.txt 2   # next run, etc.

puzzle="$1"
run="$2"          # e.g. 1, 2, 3...

if [ -z "$puzzle" ] || [ -z "$run" ]; then
    echo "Usage: $0 puzzle.txt run_number"
    exit 1
fi

./sud2sat < "input/${run}sudoko.in" > "input/${run}.cnf"
minisat "input/${run}.cnf" "input/${run}assign.txt" > "input/${run}stat.txt"
./sat2sud < "input/${run}assign.txt" > "input/${run}solution.txt"
cat "input/${run}solution.txt"
