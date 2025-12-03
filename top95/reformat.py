#!/usr/bin/env python3
import sys

def main():
    puzzles = []
    idx = 1

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        # Keep only proper 81-char puzzles made of digits + dots
        if len(line) != 81:
            continue
        if not all(ch.isdigit() or ch == '.' for ch in line):
            continue

        puzzles.append((idx, line))
        idx += 1

    out = sys.stdout
    for idx, line in puzzles:
        out.write(f"Grid {idx:02d}\n")
        # Break into 9 rows of 9, convert '.' -> '0'
        for j in range(0, 81, 9):
            row = line[j:j+9].replace('.', '0')
            out.write(row + "\n")


if __name__ == "__main__":
    main()
