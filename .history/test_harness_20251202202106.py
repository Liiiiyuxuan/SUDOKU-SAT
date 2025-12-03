#!/usr/bin/env python3
"""
Test harness for SAT-based Sudoku encodings using MiniSAT.

Encodings:
  - minimal  : ./sud2sat
  - extended : ./sud2sat1
Model -> Sudoku (optional check):
  - ./sat2sud

It:
  * reads puzzles from p096_sudoku.txt
  * for each puzzle and encoding:
      - calls sud2sat / sud2sat1
      - calls minisat on the CNF, capturing stats in stat.txt
      - parses those stats
  * prints average and worst-case statistics per encoding.

You can run:

    python3 run_sudoku_sat_tests.py

and then use the printed summary in your report.
"""

import os
import re
import statistics
import subprocess
import tempfile
from typing import Dict, List, Tuple

# ----------------------------------------------------------------------
# CONFIG – change paths/command names here if needed
# ----------------------------------------------------------------------

PUZZLE_FILE = "p096_sudoku.txt"

MINISAT_CMD = "minisat"    # or full path, e.g. "/usr/bin/minisat"
MINIMAL_ENCODER = "./sud2sat"
EXTENDED_ENCODER = "./sud2sat1"
SAT2SUD = "./sat2sud"       # not actually used for stats; only if you want to verify


# ----------------------------------------------------------------------
# Reading the puzzles
# ----------------------------------------------------------------------

def read_puzzles(path: str) -> List[Tuple[str, List[str]]]:
    """
    Reads puzzles from Project Euler p096_sudoku.txt-style file.

    Returns: list of (grid_name, rows) where rows is a list of 9 strings.
    """
    puzzles: List[Tuple[str, List[str]]] = []
    with open(path, "r") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]

    i = 0
    while i < len(lines):
        if lines[i].startswith("Grid"):
            name = lines[i].strip()
            rows = lines[i + 1:i + 10]
            if len(rows) != 9:
                raise ValueError(f"{name}: expected 9 puzzle rows, got {len(rows)}")
            puzzles.append((name, rows))
            i += 10
        else:
            i += 1

    return puzzles


def rows_to_stdin_text(rows: List[str]) -> str:
    """Convert 9 lines of 9 digits into stdin text for sud2sat/sud2sat1."""
    return "\n".join(rows) + "\n"


# ----------------------------------------------------------------------
# Parsing MiniSAT statistics
# ----------------------------------------------------------------------

STAT_NUMBER_RE = re.compile(r"[\d.]+")  # integer or float


def parse_minisat_stats(stat_text: str) -> Dict[str, float]:
    """
    Parse MiniSAT stats from the text of stat.txt.

    For each line of the form:
        KEY .... : some numbers
    we store KEY -> first numeric value.

    Typical keys:
        "restarts", "conflicts", "decisions", "propagations",
        "conflict literals", "Memory used", "CPU time"
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


# ----------------------------------------------------------------------
# Running encoder + MiniSAT for one puzzle
# ----------------------------------------------------------------------

def run_one(
    grid_name: str,
    rows: List[str],
    encoder_cmd: str,
) -> Tuple[bool, Dict[str, float]]:
    """
    Run a single puzzle through one encoder and MiniSAT.

    Returns:
        (is_sat, stats_dict)
    """
    puzzle_text = rows_to_stdin_text(rows)

    # 1) Run encoder (sud2sat or sud2sat1). It reads puzzle on stdin,
    #    writes DIMACS CNF on stdout.
    enc_proc = subprocess.run(
        encoder_cmd,
        input=puzzle_text.encode("ascii"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,  # since encoder_cmd is a simple string like "./sud2sat"
        check=True,  # crash if encoder fails
    )
    cnf_text = enc_proc.stdout.decode("ascii")

    # 2) Write CNF to a temporary file for MiniSAT.
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as cnf_file:
        cnf_file.write(cnf_text)
        cnf_path = cnf_file.name

    # 3) Temporary model file.
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as model_file:
        model_path = model_file.name

    # 4) Run MiniSAT, capturing stats to stat.txt (like: minisat cnf model > stat.txt)
    stat_path = "stat.txt"  # will be overwritten each run, which is fine
    minisat_cmd = f"{MINISAT_CMD} {cnf_path} {model_path}"
    with open(stat_path, "w") as stat_f:
        minisat_proc = subprocess.run(
            minisat_cmd,
            stdout=stat_f,
            stderr=subprocess.STDOUT,
            shell=True,
        )

    # 5) Read stat.txt and parse it.
    with open(stat_path, "r") as f:
        stat_text = f.read()
    stats = parse_minisat_stats(stat_text)

    # Decide SAT / UNSAT from text (MiniSAT prints these words).
    is_sat = "UNSATISFIABLE" not in stat_text

    # OPTIONAL: if you want to check that sat2sud reconstructs a valid Sudoku,
    # you can call it here using `model_path` and the original puzzle.
    # I don't do this because the exact interface for sat2sud may differ.

    # Clean up temp CNF + model.
    try:
        os.remove(cnf_path)
        os.remove(model_path)
    except OSError:
        pass

    return is_sat, stats


# ----------------------------------------------------------------------
# Summarizing stats into a “report”
# ----------------------------------------------------------------------

def summarize_encoding(
    encoding_name: str,
    results: List[Tuple[str, bool, Dict[str, float]]],
) -> None:
    """
    Print a report section for one encoding.

    results: list of (grid_name, is_sat, stats_dict)
    """
    print(f"\n==================== {encoding_name} encoding ====================")
    print(f"Number of puzzles: {len(results)}")
    all_sat = all(ok for _, ok, _ in results)
    print(f"All puzzles SAT? {'YES' if all_sat else 'NO (some UNSAT or failed)'}")

    # Union of all metric names we actually saw.
    metric_names = sorted({k for _, _, stats in results for k in stats.keys()})

    for metric in metric_names:
        values: List[Tuple[str, float]] = [
            (grid, stats[metric])
            for grid, _, stats in results
            if metric in stats
        ]
        if not values:
            continue

        grids, nums = zip(*values)
        avg = statistics.mean(nums)
        worst_val = max(nums)
        worst_idx = nums.index(worst_val)
        worst_grid = grids[worst_idx]

        print(f"\nMetric: {metric}")
        print(f"  Average over 50 puzzles : {avg:.3f}")
        print(f"  Worst case              : {worst_val:.3f} (on {worst_grid})")


# ----------------------------------------------------------------------
# Main driver
# --------------------------------------------------------------
