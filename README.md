# Battery pack cell layout optimization

Code for the paper *Automated layout of cylindrical cells in battery packs of light electric vehicles*:
fits a hexagonal or orthogonal grid into a rectangular or triangular container, assigns cells to S series groups
of P parallel cells with construction heuristics (snake, skewed sweep, DTAA), refines the layout with a clonal
selection algorithm (CLONALG), and evaluates it with an electrical model of the pack.

## Installation

Requires [uv](https://docs.astral.sh/uv/) and Python ≥ 3.13.

    uv sync

All commands below are run from the repository root with `uv run`, which uses the locked environment (`uv.lock`).

## Reproducing the paper

Each experiment writes raw rows (one per run) to `results/`; each table or figure script only reads them.
Stochastic runs use seed `100 + k` for run `k` (`SEED_BASE` in `src/kod/config.py`), and the seed is stored in every row.
Exceptions: Fig. 8 uses the seeds listed in `SEEDS` in `experiments/run_convergence.py`; the CLONALG 7S3P layout
(Fig. 9) was produced with the interactive `main.py` without a recorded seed, so it is provided as a stored solution
(`results/fig9_experiment/clonalg_7S3P.pkl|json`) rather than regenerated.

| Paper | Experiment (slow) | Table / figure (seconds) |
|---|---|---|
| Fig. 2 | (stored layout `results/fig2_perfect_layout/rectangle_9_14.pkl`) | `figures/fig2_perfect_layout.py` |
| Fig. 6 | – | `figures/fig6_heuristics_layout.py` |
| Table 2, Table 3 | `experiments/run_baseline.py` | `tables/table2_baseline.py`, `tables/table3_split.py` |
| Table 4 | `experiments/run_timing.py` | `tables/table4_timing.py` |
| Fig. 7 | (uses Table 2 solutions) | `figures/fig7_layouts.py` |
| Fig. 8 | `experiments/run_convergence.py` | `figures/fig8_convergence.py` |
| Fig. 9, Table 5 (model column) | `experiments/run_assembled_packs.py` | `figures/fig9_layouts.py` |
| Table 5 (measured column) | measurement data in `data/measurements/` | `experiments/read_measurement.py <folder>` |

Example:

    uv run python experiments/run_baseline.py --quick trokut_4   # check that everything runs (seconds)
    uv run python experiments/run_baseline.py                    # full Table 2 and 3 (hours)
    uv run python tables/table2_baseline.py                      # -> paper_tables/table2_baseline.csv

Re-running: `run_baseline.py` skips packs whose CSV already exists (delete it to recompute);
`run_convergence.py` and `run_timing.py` overwrite their CSV, so run them without arguments to keep all packs.
Table and figure scripts read the CSV files in the experiment folder, so do not leave copies of old results there.

Pack definitions are in `data/packages.json`; code names and paper names (e.g. `trokut_2` = Triangle 1) are in `data/pack_names.csv`.
Timings in Table 4 depend on the machine; iteration counts and solutions do not.

Not included: photographs of the assembled packs (Fig. 9b, 9d).

## Layout

    src/kod/        library
      config.py         cell data, strip and cell resistances, CLONALG settings, seeds
      grids.py, containers.py, optimizers.py   grid models and fitting into the container (Sec. 2.2-2.3)
      BatteryPack.py    pack, BMS reservation, S x P configuration (Sec. 2.4); setup_battery_pack, load_packs
      BatterySolution.py  solution, validity conditions and fitness (Sec. 2.5-2.6)
      heuristics.py     snake, skewed sweep, DTAA (Sec. 2.7)
      clonalg.py, mutations.py  CLONALG (Sec. 2.8)
      circuit.py        electrical model (Sec. 2.9)
      metrics.py        evaluation metrics (Sec. 3.2)
      storage.py        saving solutions (.pkl and .json) and run metadata
      visuals.py        plotting
    experiments/    one script per experiment
    tables/         one script per table
    figures/        one script per figure; draw_solutions.py is a helper that draws all Table 2 solutions of one pack
    examples/       small standalone examples
    data/           pack definitions and measurement data
    results/        raw results used in the paper (see results/README.md)
    paper_tables/   tables as used in the paper
    paper_figures/  figures as used in the paper
    main.py         interactive program (cell removal for BMS, voltage selection, optimization)

## License and citation

MIT, see `LICENSE`. If you use this code, please cite the paper (reference will be added after publication).
