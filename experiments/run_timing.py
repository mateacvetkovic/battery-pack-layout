"""Table 4: CLONALG run time with the Table 2 settings (both phases), 3 runs per pack.

    uv run python experiments/run_timing.py

Output: results/table4_timing/timing.csv (one row per run) and meta.json (processor, versions).
Times depend on the machine; the number of iterations and the solutions are reproducible, the seconds are not.
"""
import random
import sys
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')

from kod.BatteryPack import load_packs
from kod.clonalg import ClonalgOptimizer
from kod.config import CLONALG_PAPER, SEED_BASE
from kod.storage import write_meta, write_rows

OUT = 'results/table4_timing'
PACKS = ['pravokutni_pravokutnik_A', 'pravokutni_trokut_B', 'trokut_3', 'pravokutnik_2', 'trokut_4', 'trokut_2', 'trokut_21700']
RUNS = 3


def time_run(pack, seed):
    """A single run. Time to best = the last improvement in the phase that produced the final solution."""
    random.seed(seed); np.random.seed(seed)
    opt = ClonalgOptimizer(pack, **CLONALG_PAPER)
    t0 = time.time()
    opt.run()
    total = time.time() - t0
    h = opt.history
    # split into phases: the iteration counter restarts in the second phase
    start = max([i for i in range(len(h)) if h[i]['iteration'] == 1] or [0])
    phases = [(0, h[:start]), (start, h[start:])] if start > 0 else [(0, h)]
    k_best = 0
    for ph_start, ph in phases:
        for i in range(1, len(ph)):
            if ph[i]['best_population_fitness'] > ph[i - 1]['best_population_fitness'] + 1e-9:
                k_best = ph_start + i
    return {'iterations_to_best': k_best + 1 if h else 0, 'iterations_total': len(h),
            'time_to_best_s': round(h[k_best]['time'] - t0, 1) if h else 0.0,
            'time_total_s': round(total, 1), 'phase2': len(phases) == 2}


def main():
    names = sys.argv[1:] or PACKS
    write_meta(OUT, clonalg=CLONALG_PAPER, seed_base=SEED_BASE, runs=RUNS, packs=names)
    packs = load_packs('data/packages.json', names=names)
    rows = []
    for name in names:
        pk = packs[name]['pack']
        for run in range(RUNS):
            seed = SEED_BASE + run
            rows.append({'pack': name, 'run': run, 'seed': seed, 'S': pk.no_groups, 'P': pk.no_cells_per_group,
                         'Nu': pk.usable_cells, **time_run(pk, seed)})
            print(rows[-1], file=sys.stderr, flush=True)
            write_rows(f'{OUT}/timing.csv', rows)  # after every run


if __name__ == '__main__':
    main()