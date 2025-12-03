#!/usr/bin/env python3
"""
Test harness for SAT-based Sudoku solver.

Usage (example):

    python3 test_harness.py \
        --puzzles p096_sudoku.txt \
        --minimal-encoder "./sud2sat" \
        --extended-encoder "./sud2sat1" \
        --minisat "minisat"

Assumptions
----------
* Each encoder reads a single Sudoku from stdin as 9 lines of 9 digits (0 for blank) and writes a DIMACS CNF to stdout.
* MiniSAT is called as: minisat <cnf-file> <result-file>
* MiniSAT prints its statistics to stdout; this harness captures that output exactly as if it had been redirected to stat.txt.
"""

import argparse
import os
import re
import shlex
import statistics
import subprocess
import tempfile
from typing import Dict, List, Tuple


# ---------- input parsing ----------

def read_puzzles(path: str) -> List[Tuple[str, List[str]]]:
    """
    Read puzzles from p096_sudoku.txt-style file.

    Returns a list of (grid_name, rows) where rows is a list of 9 strings.
    """
    puzzles = []
    with open(path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    i = 0
    while i < len(lines):
        if lines[i].startswith("Grid"):
            grid_name = lines[i]
            rows = lines[i + 1:i + 10]
            if len(rows) != 9:
                raise ValueError(f"{grid_name}: expected 9 rows, got {len(rows)}")
            puzzles.append((grid_name, rows))
            i += 10
        else:
            i += 1
    return puzzles


def sudoku_rows_to_text(rows: List[str]) -> str:
    """Convert 9 string rows to the text format expected by the encoder."""
    return "\n".join(rows) + "\n"


# ---------- MiniSAT stats parsing ----------

STAT_NUMBER_RE = re.compile(r"[\d.]+")  # integer or float


def parse_minisat_stats(stat_text: str) -> Dict[str, float]:
    """
    Parse MiniSAT's stats from its text output.

    For each line of the form
        key .... : values
    we store key -> first numeric value on that line.

    This gives useful keys such as:
        "restarts", "conflicts", "decisions",
        "propagations", "conflict literals",
        "Memory used", "CPU time"
    """
    stats: Dict[str, float] = {}
    for line in stat_text.splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        key = key.strip()
        nums = STAT_NUMBER_RE.findall(rest)
        if not nums:
            continue
        stats[key] = float(nums[0])
    return stats


# ---------- running encoder + minisat ----------

def run_encoding_and_minisat(
    encoder_cmd: str,
    minisat_cmd: str,
    rows: List[str],
) -> Tuple[bool, Dict[str, float]]:
    """
    Run one puzzle through an encoder + MiniSAT.

    Returns:
        (is_sat, stats_dict)
    """
    puzzle_text = sudoku_rows_to_text(rows)

    # 1) Run encoder, get CNF on stdout.
    encode_proc = subprocess.run(
        shlex.split(encoder_cmd),
        input=puzzle_text.encode("ascii"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,  # if encoder fails, raise immediately
    )
    cnf_text = encode_proc.stdout.decode("ascii")

    # 2) Write CNF to a temporary file (MiniSAT wants a file).
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as cnf_file:
        cnf_file.write(cnf_text)
        cnf_path = cnf_file.name

    # 3) Prepare temporary output and stat files.
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as result_file:
        result_path = result_file.name

    # We'll simulate "minisat input.cnf result.txt > stat.txt"
    stat_fd, stat_path = tempfile.mkstemp(prefix="stat_", suffix=".txt")
    os.close(stat_fd)

    try:
        minisat_args = shlex.split(minisat_cmd) + [cnf_path, result_path]
        with open(stat_path, "w") as stat_f:
            minisat_proc = subprocess.run(
                minisat_args,
                stdout=stat_f,
                stderr=subprocess.STDOUT,
                check=False,  # MiniSAT uses exit codes 10/20
            )

        # 4) Read stat.txt-like output and parse it.
        with open(stat_path, "r") as f:
            stat_text = f.read()

        stats = parse_minisat_stats(stat_text)

        # SAT/UNSAT (MiniSAT prints one of these words)
        is_sat = "UNSATISFIABLE" not in stat_text

        return is_sat, stats

    finally:
        # Clean up temporary files.
        for path in (cnf_path, result_path, stat_path):
            try:
                os.remove(path)
            except OSError:
                pass


# ---------- summarizing results ----------

def summarize_encoding(
    name: str,
    results: List[Tuple[str, bool, Dict[str, float]]],
) -> None:
    """
    Print average and worst-case stats for a given encoding.

    results: list of (grid_name, is_sat, stats_dict)
    """
    print(f"\n==== Encoding: {name} ====")
    all_sat = all(ok for _, ok, _ in results)
    print(f"All puzzles SAT? {'yes' if all_sat else 'NO (some unsat or failed)'}")
    print(f"Number of puzzles: {len(results)}")

    # Collect union of all metric names.
    metric_names = sorted(
        {k for _, _, stats in results for k in stats.keys()}
    )

    for metric in metric_names:
        values = [(grid, stats[metric])
                  for grid, _, stats in results
                  if metric in stats]

        if not values:
            continue

        grids, nums = zip(*values)
        avg = statistics.mean(nums)
        worst_val = max(nums)
        worst_idx = nums.index(worst_val)
        worst_grid = grids[worst_idx]

        print(f"\nMetric: {metric}")
        print(f"  average     : {avg:.3f}")
        print(f"  worst case  : {worst_val:.3f}  (puzzle {worst_grid})")


# ---------- CLI ----------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test harness for SAT-based Sudoku solver using MiniSAT."
    )
    parser.add_argument(
        "--puzzles",
        default="p096_sudoku.txt",
        help="Path to p096_sudoku.txt (Project Euler puzzles).",
    )
    parser.add_argument(
        "--minimal-encoder",
        required=True,
        help="Command to run the minimal encoding encoder (e.g. './sud2sat').",
    )
    parser.add_argument(
        "--extended-encoder",
        required=True,
        help="Command to run the extended encoding encoder (e.g. './sud2sat1').",
    )
    parser.add_argument(
        "--minisat",
        default="minisat",
        help="MiniSAT executable (default: minisat).",
    )

    args = parser.parse_args()

    puzzles = read_puzzles(args.puzzles)
    print(f"Loaded {len(puzzles)} puzzles from {args.puzzles}")

    encodings = [
        ("minimal", args.minimal_encoder),
        ("extended", args.extended_encoder),
    ]

    for enc_name, enc_cmd in encodings:
        enc_results: List[Tuple[str, bool, Dict[str, float]]] = []

        for grid_name, rows in puzzles:
            is_sat, stats = run_encoding_and_minisat(
                enc_cmd, args.minisat, rows
            )
            enc_results.append((grid_name, is_sat, stats))

        summarize_encoding(enc_name, enc_results)


if __name__ == "__main__":
    main()
