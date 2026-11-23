"""Tablica 2 i Tablica 3: snake (1 i 2 reda), početna heuristika i CLONALG na 14 paketa iz članka.

    uv run python experiments/run_baseline.py                 # svi paketi iz PLAN-a
    uv run python experiments/run_baseline.py trokut_4        # samo jedan paket
    uv run python experiments/run_baseline.py --quick trokut_4   # 1 pokretanje, 3 iteracije: samo provjera da radi

Izlaz u results/table2_table3_baseline/:
  <paket>.csv                 jedan redak po metodi i pokretanju (sirovi podaci; prosjeke računa tables/table2_baseline.py)
  solutions/<paket>/*.pkl|json  rješenje svakog retka
  meta.json                   git commit, verzije, postavke
Paket čiji CSV već postoji se preskače (prekinuti run se nastavlja ponovnim pokretanjem).
Pokretanje k koristi seed SEED_BASE + k, isti za početnu heuristiku i za CLONALG.
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

# paket: (broj pokretanja n iz Tablice 2, vrijednosti w_split). w_split=1000 su retci "Split = no" u Tablici 3.
PLAN = {
    'trokut_2': (10, (0, 1000)), 'trokut_3': (5, (0, 1000)), 'trokut_4': (10, (0, 1000)), 'trokut_5': (5, (0, 1000)),
    'pravokutnik_1': (3, (0,)), 'pravokutnik_2': (10, (0, 1000)), 'pravokutnik_3': (5, (0, 1000)),
    'pravokutni_trokut_A': (10, (0,)), 'pravokutni_trokut_B': (3, (0,)), 'pravokutni_trokut_C_bms': (10, (0,)),
    'pravokutni_pravokutnik_A': (3, (0,)), 'pravokutni_pravokutnik_B_bms': (3, (0,)), 'pravokutni_pravokutnik_C': (3, (0,)),
    'trokut_21700': (5, (0,)),
}

# naziv metode u CSV-u -> ime datoteke rješenja (ASCII)
SLUG = {'snake 1 red': 'snake_1_row', 'snake 2 reda': 'snake_2_rows', 'početna heuristika': 'initial_heuristics',
        'CLONALG w_split=0': 'clonalg_split_allowed', 'CLONALG w_split=1000': 'clonalg_split_penalized'}


def nearest_bridge_length(pack):
    """Duljina mosta između dviju susjednih ćelija (u mm, kao r_per_length)."""
    cells = pack.grid.cells
    return min(float(np.hypot(cells[c].x - cells[m].x, cells[c].y - cells[m].y))
               for c in range(min(len(cells), 60)) for m in pack.get_neighbours_ids(c))


def run_pack(p, runs, w_splits, opt):
    """Sva rješenja za jedan paket: {(metoda, pokretanje): (rješenje, seed)}."""
    pk = p['pack']
    sols = {}
    for h, key in ((1, 'snake 1 red'), (2, 'snake 2 reda')):
        sol, _ = snake_baseline(pk, h)
        if sol:
            sols[(key, 0)] = (sol, None)
    for k in range(runs):
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
        print(f"[{p['name']}] pokretanje {k + 1}/{runs} gotovo", file=sys.stderr, flush=True)
    return sols


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('packs', nargs='*', help='imena paketa (zadano: svi iz PLAN-a)')
    ap.add_argument('--quick', action='store_true', help='1 pokretanje, 3 iteracije, populacija 10')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()

    names = a.packs or list(PLAN)
    opt = dict(CLONALG_PAPER, max_iterations=3, population_size=10, d_new_individuals=3, clones_per_antibody=3) if a.quick else CLONALG_PAPER
    write_meta(a.out, clonalg=opt, seed_base=SEED_BASE, plan={n: PLAN[n] for n in names}, quick=a.quick)
    packs = load_packs(PACKS_JSON, names=names)
    for name in names:
        csv_path = os.path.join(a.out, f'{name}.csv')
        if os.path.exists(csv_path):
            print(f'{name}: {csv_path} već postoji, preskačem')
            continue
        runs, w_splits = PLAN[name]
        if a.quick:
            runs = 1
        p = packs[name]
        with contextlib.redirect_stdout(io.StringIO()):  # optimizer puno ispisuje
            sols = run_pack(p, runs, w_splits, opt)
        omjer = p['r_per_length'] * nearest_bridge_length(p['pack']) / p['r_cell']
        rows = []
        for (method, k), (sol, seed) in sols.items():
            suffix = '' if method.startswith('snake') else f'_run{k}'
            save_solution(os.path.join(a.out, 'solutions', name, f'{name}_{SLUG[method]}{suffix}'),
                          sol, p['inputs'], method=method, run=k, seed=seed)
            r = evaluate(sol, p['r_cell'], p['r_per_length'], selected=False)
            if r:
                rows.append({'pack': name, 'metoda': method, 'run': k, 'seed': seed, 'omjer_R': omjer,
                             'r_cell': p['r_cell'], 'r_per_length': p['r_per_length'], **r})
        write_rows(csv_path, rows)
        print(f'{name}: {len(rows)} redaka -> {csv_path}', flush=True)


if __name__ == '__main__':
    main()
