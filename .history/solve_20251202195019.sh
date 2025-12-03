#!/bin/bash

# usage: ./solve.sh 1
#        ./solve.sh 2   # next run, etc.

run="$1"          # e.g. 1, 2, 3...

./sud2sat < "input/${run}sudoku.in" > "input/${run}.cnf"

