#!/usr/bin/env bash

# usage: ./solve.sh puzzle.txt 1
#        ./solve.sh puzzle.txt 2   # next run, etc.

run="$1"          # e.g. 1, 2, 3...

./sud2sat < "input/${run}sudoko.in" > "input/${run}.cnf"
minisat "input/${run}.cnf" "input/${run}assign.txt" > "input/${run}stat.txt"
./sat2sud < "input/${run}assign.txt" > "input/${run}solution.txt"
cat "input/${run}solution.txt"
