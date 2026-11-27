# Results used in the paper

Pack names in the code differ from the paper: see `data/pack_names.csv` (e.g. Triangle 1 = `trokut_2`).
Every solution is stored as `.pkl` (full object, for plotting) and `.json` (inputs and cell-to-group assignment,
readable without this code).

| Folder | Paper | Produced by |
|---|---|---|
| `table2_table3_baseline/<pack>.csv` | Table 2; rows `CLONALG w_split=1000` are Table 3 ("Split = no") | `experiments/run_baseline.py` |
| `table2_table3_baseline/solutions/<pack>/` | layout of every row; Fig. 2 = `trokut_4/` (`snake_1_row`, `clonalg_split_allowed_run0`) | same |
| `table4_timing/` | Table 4 | `experiments/run_timing.py` |
| `fig3_convergence/` | Fig. 3 (`trokut_5` = Triangle 4, `pravokutni_trokut_B` = Triangle 6) | `experiments/run_convergence.py` |
| `fig4_experiment/` | Fig. 4 and the "Model" column of Table 5 | layouts are inputs (the assembled packs); `experiments/run_assembled_packs.py` |
| `extra_resistance_sweep/` | not in the paper; supports the claim that the ranking does not depend on the resistances | `experiments/run_resistance_sweep.py` |
| `extra_population/` | not in the paper | removed function `population_snapshot` (see git history) |

