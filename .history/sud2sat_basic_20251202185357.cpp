// sud2sat.cpp
#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <fstream>
#include <cstring>
#include <cctype>
#include <utility>

using namespace std;

static const int NUM_ROWS = 9;
static const int NUM_COLS = 9;
static const int NUM_DIGITS = 9;
static const int NUM_VARS = NUM_ROWS * NUM_COLS * NUM_DIGITS; // 729

// convert it to decimal representation
int varnum(int r, int c, int d) {
    // r,c,d in [1..9]
    return 81 * (r - 1) + 9 * (c - 1) + d;
}

vector<vector<int>> clauses;

// ---- Encoding builders ----

void add_cell_at_least_one() {
    // For each cell (r,c): (s_rc1 ∨ ... ∨ s_rc9)
    for (int r = 1; r <= NUM_ROWS; ++r) {
        for (int c = 1; c <= NUM_COLS; ++c) {
            vector<int> clause;
            clause.reserve(NUM_DIGITS);
            for (int d = 1; d <= NUM_DIGITS; ++d) {
                clause.push_back(varnum(r, c, d));
            }
            clauses.push_back(move(clause));
        }
    }
}

void add_row_at_most_one() {
    // For each row r, digit d, columns c1 < c2:
    // (¬s_r c1 d ∨ ¬s_r c2 d)
    for (int r = 1; r <= NUM_ROWS; ++r) {
        for (int d = 1; d <= NUM_DIGITS; ++d) {
            for (int c1 = 1; c1 < NUM_COLS; ++c1) {
                for (int c2 = c1 + 1; c2 <= NUM_COLS; ++c2) {
                    clauses.push_back({
                        -varnum(r, c1, d),
                        -varnum(r, c2, d)
                    });
                }
            }
        }
    }
}

void add_col_at_most_one() {
    // For each column c, digit d, rows r1 < r2:
    // (¬s_r1 c d ∨ ¬s_r2 c d)
    for (int c = 1; c <= NUM_COLS; ++c) {
        for (int d = 1; d <= NUM_DIGITS; ++d) {
            for (int r1 = 1; r1 < NUM_ROWS; ++r1) {
                for (int r2 = r1 + 1; r2 <= NUM_ROWS; ++r2) {
                    clauses.push_back({
                        -varnum(r1, c, d),
                        -varnum(r2, c, d)
                    });
                }
            }
        }
    }
}

void add_box_at_most_one() {
    // For each 3x3 box and digit d, for each pair of cells:
    // (¬s_r1 c1 d ∨ ¬s_r2 c2 d)
    for (int br = 0; br < 3; ++br) {
        for (int bc = 0; bc < 3; ++bc) {
            vector<pair<int,int>> cells;
            cells.reserve(9);
            for (int dr = 0; dr < 3; ++dr) {
                for (int dc = 0; dc < 3; ++dc) {
                    int r = 3 * br + dr + 1;
                    int c = 3 * bc + dc + 1;
                    cells.emplace_back(r, c);
                }
            }

            for (int d = 1; d <= NUM_DIGITS; ++d) {
                for (int i = 0; i < (int)cells.size(); ++i) {
                    for (int j = i + 1; j < (int)cells.size(); ++j) {
                        int r1 = cells[i].first;
                        int c1 = cells[i].second;
                        int r2 = cells[j].first;
                        int c2 = cells[j].second;
                        clauses.push_back({
                            -varnum(r1, c1, d),
                            -varnum(r2, c2, d)
                        });
                    }
                }
            }
        }
    }
}


void add_col_at_least_one() {
    // Extended: each number appears at least once in each column.
    for (int c = 1; c <= NUM_COLS; ++c) {
        for (int d = 1; d <= NUM_DIGITS; ++d) {
            vector<int> clause;
            clause.reserve(NUM_ROWS);
            for (int r = 1; r <= NUM_ROWS; ++r) {
                clause.push_back(varnum(r, c, d));
            }
            clauses.push_back(move(clause));
        }
    }
}

void add_box_at_least_one() {
    // Extended: each number appears at least once in each 3x3 box.
    for (int br = 0; br < 3; ++br) {
        for (int bc = 0; bc < 3; ++bc) {
            vector<pair<int,int>> cells;
            cells.reserve(9);
            for (int dr = 0; dr < 3; ++dr) {
                for (int dc = 0; dc < 3; ++dc) {
                    int r = 3 * br + dr + 1;
                    int c = 3 * bc + dc + 1;
                    cells.emplace_back(r, c);
                }
            }
            for (int d = 1; d <= NUM_DIGITS; ++d) {
                vector<int> clause;
                clause.reserve(9);
                for (auto &cell : cells) {
                    clause.push_back(varnum(cell.first, cell.second, d));
                }
                clauses.push_back(move(clause));
            }
        }
    }
}

void add_givens(const int grid[9][9]) {
    // Unit clauses for clues.
    for (int r = 1; r <= NUM_ROWS; ++r) {
        for (int c = 1; c <= NUM_COLS; ++c) {
            int d = grid[r-1][c-1];
            if (1 <= d && d <= 9) {
                clauses.push_back({ varnum(r, c, d) });
            }
        }
    }
}

// ---- IO helpers ----

bool read_grid(istream &in, int grid[9][9]) {
    int rowCount = 0;
    string line;
    while (getline(in, line)) {
        // strip spaces
        string filtered;
        for (char ch : line) {
            if (!isspace((unsigned char)ch))
                filtered.push_back(ch);
        }
        if (filtered.empty())
            continue;

        if (rowCount >= 9) break;

        if ((int)filtered.size() < 9) {
            cerr << "Error: each non-empty line must have at least 9 chars\n";
            return false;
        }

        for (int c = 0; c < 9; ++c) {
            char ch = filtered[c];
            if (ch == '.' || ch == '0') {
                grid[rowCount][c] = 0;
            } else if (ch >= '1' && ch <= '9') {
                grid[rowCount][c] = ch - '0';
            } else {
                // treat as blank
                grid[rowCount][c] = 0;
            }
        }
        rowCount++;
        if (rowCount == 9) break;
    }

    if (rowCount != 9) {
        cerr << "Error: expected 9 rows in puzzle\n";
        return false;
    }
    return true;
}

int main(int argc, char *argv[]) {
    bool extended = false;
    string filename;

    // Very light CLI: sud2sat [-e] [puzzlefile]
    int argi = 1;
    while (argi < argc) {
        string a = argv[argi];
        if (a == "-e" || a == "--extended") {
            extended = true;
            ++argi;
        } else {
            filename = a;
            ++argi;
        }
    }

    istream *in = &cin;
    if (!filename.empty()) {
        static ifstream fin;
        fin.open(filename.c_str());
        if (!fin) {
            cerr << "Error: cannot open puzzle file " << filename << "\n";
            return 1;
        }
        in = &fin;
    }

    int grid[9][9];
    if (!read_grid(*in, grid)) {
        return 1;
    }

    // Build clauses
    clauses.clear();

    // Minimal encoding
    add_cell_at_least_one();
    add_row_at_most_one();
    add_col_at_most_one();
    add_box_at_most_one();

    // Givens
    add_givens(grid);

    // Extended
    if (extended) {
        add_row_at_least_one();
        add_col_at_least_one();
        add_box_at_least_one();
    }

    // Output DIMACS
    int numClauses = (int)clauses.size();
    cout << "p cnf " << NUM_VARS << " " << numClauses << "\n";
    for (const auto &cl : clauses) {
        for (int lit : cl) {
            cout << lit << " ";
        }
        cout << "0\n";
    }

    return 0;
}
