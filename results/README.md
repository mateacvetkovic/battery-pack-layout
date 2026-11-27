# Results used in the paper

Pack names in the code differ from the paper: see `data/pack_names.csv` (e.g. Triangle 1 = `trokut_2`).
Every solution is stored as `.pkl` (full object, for plotting) and `.json` (inputs and cell-to-group assignment,
readable without this code).

| Folder | Paper | Produced by |
|---|---|---|
| `table2_table3_baseline/<pack>.csv` | Table 2; rows `CLONALG w_split=1000` are Table 3 ("Split = no") | `experiments/run_baseline.py` |
| `table2_table3_baseline/solutions/<pack>/` | layout of every row; Fig. 7 = `trokut_4/` (`snake_1_row`, `clonalg_split_allowed_run0`) | same |
| `table4_timing/` | Table 4 | `experiments/run_timing.py` |
| `fig8_convergence/` | Fig. 8 (`trokut_5` = Triangle 4, `pravokutni_trokut_B` = Triangle 6) | `experiments/run_convergence.py` |
| `fig_experiment/` | Fig. 9 and the "Model" column of Table 5 | layouts are inputs (the assembled packs); `experiments/run_assembled_packs.py` |

