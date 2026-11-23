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

## Known issues of the current files (to be fixed by re-running)

- The CSVs in `table2_table3_baseline/`, `table4_timing/` and `fig3_convergence/` were produced before seeding was made
  deterministic (DTAA iterated over a set of objects, whose order depends on memory addresses). Snake rows are deterministic
  and reproduce exactly; initial heuristics and CLONALG rows cannot be reproduced exactly. Their seeds are unknown.
- Triangle 8 (`trokut_21700_part1*.csv`, `_part2*.csv`) is two separate runs merged into n = 5; runs 0 and 1 appear in both.
- `table2_table3_baseline/*_sazetak.csv` are old summaries; the paper tables are now computed by `tables/*.py`.
- `extra_resistance_sweep/resistance_sweep.csv` was computed before Triangle 8 was re-run; its Triangle 8 rows refer to older layouts.
- Table 2 was computed with T = 200 iterations; the paper states T = 500 (`config.CLONALG_PAPER` now uses 500).
- The 7S3P snake pack (`fig4_experiment/snake_7S3P`) is the plain row-wise snake (`heuristics.snake_pattern_rows`), not the
  oriented snake of Table 2. The CLONALG 7S3P layout was produced by `main.py` without a recorded seed.
- Measured data for Table 5 (folders with `log_ir.csv`) and the photographs for Fig. 4b, 4d are not in the repository yet.
