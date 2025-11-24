// sat2sud.cpp
#include <bits/stdc++.h>
using namespace std;

static const int NUM_ROWS = 9;
static const int NUM_COLS = 9;
static const int NUM_DIGITS = 9;
static const int NUM_VARS = NUM_ROWS * NUM_COLS * NUM_DIGITS; // 729

tuple<int,int,int> inv_varnum(int v) {
    // inverse of varnum: v in [1..729]
    v -= 1;
    int r = v / 81 + 1;
    int rem = v % 81;
    int c = rem / 9 + 1;
    int d = rem % 9 + 1;
    return make_tuple(r, c, d);
}

int main(int argc, char *argv[]) {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    istream *in = &cin;
    if (argc > 1) {
        static ifstream fin;
        fin.open(argv[1]);
        if (!fin) {
            cerr << "Error: cannot open assignment file\n";
            return 1;
        }
        in = &fin;
    }

    vector<int> ints;
    string line;

    while (std::getline(*in, line)) {
        if (line.empty()) continue;
        if (line[0] == 'c' || line[0] == 's') {
            // comment/status line, ignore
            continue;
        }

        stringstream ss(line);
        string tok;
        while (ss >> tok) {
            if (tok == "SAT" || tok == "UNSAT" || tok == "UNKNOWN" || tok == "v")
                continue;
            int val;
            try {
                val = stoi(tok);
            } catch (...) {
                continue;
            }
            if (val == 0) {
                // end of this line's assignment list, but maybe more lines follow
                continue;
            }
            ints.push_back(val);
        }
    }

    // val[i] = true/false for variable i; index 0 unused
    vector<int> val(NUM_VARS + 1, 0); // 0=unset, 1=true, -1=false
    for (int x : ints) {
        if (x > 0 && x <= NUM_VARS) {
            val[x] = 1;
        } else if (x < 0 && -x <= NUM_VARS) {
            val[-x] = -1;
        }
    }

    int grid[9][9];
    memset(grid, 0, sizeof(grid));

    for (int v = 1; v <= NUM_VARS; ++v) {
        if (val[v] == 1) {
            int r, c, d;
            tie(r, c, d) = inv_varnum(v);
            grid[r-1][c-1] = d;
        }
    }

    // print solved Sudoku: 9 lines of 9 digits
    for (int r = 0; r < 9; ++r) {
        for (int c = 0; c < 9; ++c) {
            cout << grid[r][c];
        }
        cout << "\n";
    }

    return 0;
}
