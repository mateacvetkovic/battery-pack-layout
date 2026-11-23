"""Slika 3: prosječni fitness populacije po iteraciji, 3 pokretanja, samo prva faza (w_far = 0), stagnacija 100.

    uv run python experiments/run_convergence.py

Izlaz: results/fig3_convergence/convergence.csv i meta.json.
"""
import random
import sys
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')

from kod.BatteryPack import load_packs
from kod.clonalg import ClonalgOptimizer
from kod.config import CLONALG_CONVERGENCE, SEED_BASE
from kod.storage import write_meta, write_rows

OUT = 'results/fig3_convergence'
PACKS = ['trokut_5', 'pravokutni_trokut_B']   # Triangle 4 i Triangle 6
RUNS = 3


def main():
    names = sys.argv[1:] or PACKS
    write_meta(OUT, clonalg=CLONALG_CONVERGENCE, seed_base=SEED_BASE, runs=RUNS, packs=names, w_far=0)
    packs = load_packs('data/packages.json', names=names)
    rows = []
    for name in names:
        for run in range(RUNS):
            seed = SEED_BASE + run
            random.seed(seed); np.random.seed(seed)
            opt = ClonalgOptimizer(packs[name]['pack'], **CLONALG_CONVERGENCE)
            t0 = time.time()
            best = opt.run(w_far=0)
            seconds = time.time() - t0
            # history je prazan ako je idealan broj mostova nađen već u prvoj iteraciji
            history = opt.history or [{'iteration': 0, 'best_population_fitness': best[0].fitness}]
            # avg_fitness se dopunjuje dvaput po iteraciji; drugi zapis je prosjek nove populacije
            means = opt.avg_fitness[1::2] or [float('nan')]
            for i, h in enumerate(history):
                rows.append({'pack': name, 'run': run, 'seed': seed, 'iteration': h['iteration'],
                             'best_fitness': h['best_population_fitness'], 'mean_fitness': means[min(i, len(means) - 1)],
                             'iterations_total': len(opt.history), 'time_s': round(seconds, 1),
                             'fitness_std': h.get('fitness_std'), 'diversity': h.get('diversity')})
            print(f'{name} run {run}: {len(opt.history)} iteracija, {seconds:.0f} s', file=sys.stderr, flush=True)
    write_rows(f'{OUT}/convergence.csv', rows)


if __name__ == '__main__':
    main()
