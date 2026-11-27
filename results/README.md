# Results used in the paper

Pack names in the code differ from the paper: see `data/pack_names.csv` (e.g. Triangle 1 = `trokut_2`).
Every solution is stored as `.pkl` (full object, for plotting) and `.json` (inputs and cell-to-group assignment,
readable without this code). Each folder also contains `meta.json` (git commit, library versions, settings).

| Folder | Paper | Produced by |
|---|---|---|
| `fig2_perfect_layout/` | Fig. 2 | stored layout (input); drawn by `figures/fig2_perfect_layout.py` |
| `table2_table3_baseline/<pack>.csv` | Table 2; rows `CLONALG w_split=1000` are Table 3 ("Split = no") | `experiments/run_baseline.py` |
| `table2_table3_baseline/solutions/<pack>/` | layout of every row; Fig. 7 = `trokut_4/` (`snake_1_row`, `clonalg_split_allowed_run3`) | same |
| `table4_timing/` | Table 4 | `experiments/run_timing.py` |
| `fig8_convergence/` | Fig. 8 (`trokut_5` = Triangle 4, `pravokutni_trokut_B` = Triangle 6) | `experiments/run_convergence.py` |
| `fig9_experiment/` | Fig. 9 and the "Model" column of Table 5 | layouts are inputs (the assembled packs); `experiments/run_assembled_packs.py` |

## Method names in `table2_table3_baseline/*.csv`

The method column (`metoda`) uses the original names:

| CSV value | Paper | Solution file suffix |
|---|---|---|
| `snake 1 red` | snake, 1 row | `snake_1_row` |
| `snake 2 reda` | snake, 2 rows | `snake_2_rows` |
| `početna heuristika` | initial heuristics | `initial_heuristics_run<k>` |
| `CLONALG w_split=0` | CLONALG (split allowed) | `clonalg_split_allowed_run<k>` |
| `CLONALG w_split=1000` | CLONALG, "Split = no" (Table 3) | `clonalg_split_penalized_run<k>` |

Snake rows are deterministic and have `run = 0` and no seed.

## Notes

- The 7S3P snake pack (`fig9_experiment/snake_7S3P`) is the plain row-wise snake (`heuristics.snake_pattern_rows`),
  not the oriented snake of Table 2.
- The CLONALG 7S3P layout (`fig9_experiment/clonalg_7S3P`) was produced by `main.py` without a recorded seed.
- The model resistances of Fig. 9 / Table 5 use `config.ASSEMBLED` (0.15 mm strip, R_cell = 45 mOhm);
  all other results use `config.PAPER`.
