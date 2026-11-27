"""Table 2 and Table 3: snake (1 and 2 rows), initial heuristics and CLONALG on the 14 packs from the paper.

    uv run python experiments/run_baseline.py                 # all packs in PLAN
    uv run python experiments/run_baseline.py trokut_4        # a single pack
    uv run python experiments/run_baseline.py --quick trokut_4   # 1 run, 3 iterations: smoke test only

Output in results/table2_table3_baseline/:
  <pack>.csv                  one row per method and run (raw data; averages are computed by tables/table2_baseline.py)
  solutions/<pack>/*.pkl|json   the solution of each row
  meta.json                   git commit, versions, settings
A pack whose CSV already exists is skipped (an interrupted run is resumed by running the script again).
Run k uses seed SEED_BASE + k, the same for the initial heuristics and for CLONALG.
"""
import argparse
import contextlib
import io
import os
import random
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')

from kod import clonalg
from kod.BatteryPack import load_packs
from kod.clonalg import fitness_weights
from kod.config import CLONALG_PAPER, SEED_BASE
from kod.heuristics import snake_baseline
from kod.metrics import evaluate
from kod.storage import save_solution, write_meta, write_rows

PACKS_JSON = 'data/packages.json'
OUT = 'results/table2_table3_baseline'

# pack: (number of runs n from Table 2, w_split values). w_split=1000 gives the "Split = no" rows of Table 3.
PLAN = {
    'trokut_2': (10, (0, 1000)), 'trokut_3': (5, (0, 1000)), 'trokut_4': (10, (0, 1000)), 'trokut_5': (5, (0, 1000)),
    'pravokutnik_1': (3, (0,)), 'pravokutnik_2': (10, (0, 1000)), 'pravokutnik_3': (5, (0, 1000)),
    'pravokutni_trokut_A': (10, (0,)), 'pravokutni_trokut_B': (10, (0,)), 'pravokutni_trokut_C_bms': (10, (0,)),
    'pravokutni_pravokutnik_A': (3, (0,)), 'pravokutni_pravokutnik_B_bms': (3, (0,)), 'pravokutni_pravokutnik_C': (3, (0,)),
    'trokut_21700': (5, (0,)),
}

# method name in the CSV -> solution file name (ASCII)
SLUG = {'snake 1 red': 'snake_1_row', 'snake 2 reda': 'snake_2_rows', 'početna heuristika': 'initial_heuristics',
        'CLONALG w_split=0': 'clonalg_split_allowed', 'CLONALG w_split=1000': 'clonalg_split_penalized'}

def run_pack(p, runs, w_splits, opt):
    """All solutions for one pack: {(method, run): (solution, seed)}."""
    pk = p['pack']
    sols = {}
    for h, key in ((1, 'snake 1 red'), (2, 'snake 2 reda')):
        sol, _ = snake_baseline(pk, h)
        if sol:
            sols[(key, 0)] = (sol, None)
    for k in range(runs):
        print(f"Starting run {k}/{runs}.")
        seed = SEED_BASE + k
        random.seed(seed); np.random.seed(seed)
        init = [x for x in clonalg.generate_initial_population(pk, opt['population_size'], snakes=False) if x.fitness > -float('inf')]
        if init:
            sols[('početna heuristika', k)] = (max(init, key=lambda x: x.fitness), seed)
        for w in w_splits:
            with fitness_weights(w_split=w):
                random.seed(seed); np.random.seed(seed)
                found = clonalg.ClonalgOptimizer(pk, **opt).run()
            if found:
                sols[(f'CLONALG w_split={w:g}', k)] = (max(found, key=lambda x: x.fitness), seed)
        print(f"[{p['name']}] run {k + 1}/{runs} done", file=sys.stderr, flush=True)
    return sols


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('packs', nargs='*', help='pack names (default: all packs in PLAN)')
    ap.add_argument('--quick', action='store_true', help='1 run, 3 iterations, population 10')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()

    names = a.packs or list(PLAN)
    opt = dict(CLONALG_PAPER, max_iterations=3, population_size=10, d_new_individuals=3, clones_per_antibody=3) if a.quick else CLONALG_PAPER
    write_meta(a.out, clonalg=opt, seed_base=SEED_BASE, plan={n: PLAN[n] for n in names}, quick=a.quick)
    packs = load_packs(PACKS_JSON, names=names)
    for name in names:
        csv_path = os.path.join(a.out, f'{name}.csv')
        if os.path.exists(csv_path):
            print(f'{name}: {csv_path} already exists, skipping')
            continue
        runs, w_splits = PLAN[name]
        if a.quick:
            runs = 1
        p = packs[name]
        with contextlib.redirect_stdout(io.StringIO()):  # the optimizer prints a lot
            sols = run_pack(p, runs, w_splits, opt)
        rows = []
        for (method, k), (sol, seed) in sols.items():
            suffix = '' if method.startswith('snake') else f'_run{k}'
            save_solution(os.path.join(a.out, 'solutions', name, f'{name}_{SLUG[method]}{suffix}'),
                          sol, p['inputs'], method=method, run=k, seed=seed)
            r = evaluate(sol, p['r_cell'], p['r_per_length'], selected=False)
            if r:
                rows.append({'pack': name, 'metoda': method, 'run': k, 'seed': seed,
                             'r_cell': p['r_cell'], 'r_per_length': p['r_per_length'], **r})
        write_rows(csv_path, rows)
        print(f'{name}: {len(rows)} rows -> {csv_path}', flush=True)


if __name__ == '__main__':
    main()