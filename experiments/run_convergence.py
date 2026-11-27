"""Figure 8: mean and best population fitness per iteration, first phase only (w_far = 0), stagnation limit 100.
Seeds per pack are in SEEDS.

    uv run python experiments/run_convergence.py

Output: results/fig8_convergence/convergence.csv and meta.json.
"""
import random
import sys
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')

from kod.BatteryPack import load_packs
from kod.clonalg import ClonalgOptimizer
from kod.config import CLONALG_CONVERGENCE
from kod.storage import write_meta, write_rows

OUT = 'results/fig8_convergence'
# Triangle 4 and Triangle 6; run k uses SEEDS[pack][k]
SEEDS = {'trokut_5': [100, 101, 99998], 'pravokutni_trokut_B': [100, 101, 102]}
#SEEDS = {'trokut_5': [102]}


def main():
    names = sys.argv[1:] or list(SEEDS)
    write_meta(OUT, clonalg=CLONALG_CONVERGENCE, seeds={n: SEEDS[n] for n in names}, packs=names, w_far=0)
    packs = load_packs('data/packages.json', names=names)
    rows = []
    for name in names:
        for run, seed in enumerate(SEEDS[name]):
            random.seed(seed); np.random.seed(seed)
            opt = ClonalgOptimizer(packs[name]['pack'], **CLONALG_CONVERGENCE)
            t0 = time.time()
            best = opt.run(w_far=0)
            seconds = time.time() - t0
            # history is empty if the ideal number of bridges is already found in the first iteration
            history = opt.history or [{'iteration': 0, 'best_population_fitness': best[0].fitness}]
            # avg_fitness is appended twice per iteration; the second entry is the mean of the new population
            means = opt.avg_fitness[1::2] or [float('nan')]
            for i, h in enumerate(history):
                rows.append({'pack': name, 'run': run, 'seed': seed, 'iteration': h['iteration'],
                             'best_fitness': h['best_population_fitness'], 'mean_fitness': means[min(i, len(means) - 1)],
                             'iterations_total': len(opt.history), 'time_s': round(seconds, 1),
                             'fitness_std': h.get('fitness_std'), 'diversity': h.get('diversity')})
            print(f'{name} run {run} (seed {seed}): {len(opt.history)} iterations, {seconds:.0f} s', file=sys.stderr, flush=True)
    write_rows(f'{OUT}/convergence.csv', rows)


if __name__ == '__main__':
    main()