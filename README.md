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
Every stochastic run uses seed `100 + k` for run `k` (`src/kod/config.py`), and the seed is stored in every row.
`results/<experiment>/meta.json` records the git commit, library versions and settings of the run.

| Paper | Experiment (slow) | Table / figure (seconds) |
|---|---|---|
| Table 2, Table 3 | `experiments/run_baseline.py` | `tables/table2_baseline.py`, `tables/table3_split.py` |
| Table 4 | `experiments/run_timing.py` | `tables/table4_timing.py` |
| Fig. 2 | (uses Table 2 solutions) | `figures/fig2_layouts.py` |
| Fig. 3 | `experiments/run_convergence.py` | `figures/fig3_convergence.py` |
| Fig. 4, Table 5 (model column) | `experiments/run_assembled_packs.py` | `figures/fig4_layouts.py` |

Example:

    uv run python experiments/run_baseline.py --quick trokut_4   # check that everything runs (seconds)
    uv run python experiments/run_baseline.py                    # full Table 2 and 3 (hours)
    uv run python tables/table2_baseline.py                      # -> paper_tables/table2_baseline.csv

Table and figure scripts read every `*.csv` in the experiment folder, so move old results away before re-running an experiment.
Pack definitions are in `data/packages.json`; code names and paper names (e.g. `trokut_2` = Triangle 1) are in `data/pack_names.csv`.
Timings in Table 4 depend on the machine; iteration counts and solutions do not.

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
    figures/        one script per figure
    examples/       small standalone examples
    data/           pack definitions
    results/        raw results used in the paper (see results/README.md)
    paper_figures/  figures as used in the paper
    main.py         interactive program (cell removal for BMS, voltage selection, optimization)
