"""Primjer skewed sweep rasporeda (§2.7.3) na sastavljenom paketu 7S3P (isti kao na Slici 4).
Snake na istom paketu je Slika 4a.

    uv run python figures/fig_heuristics.py

Uzima se prvi seed od SEED nadalje koji daje valjan raspored bez idealnog broja mostova
(da se vide nepravilne granice). Upotrijebljeni seed se ispiše; rezultat je ponovljiv.
"""
import random

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from kod.clonalg import generate_initial_population
from kod.heuristics import skewed_sweep
from kod.storage import load_solution

PACK_FROM = 'results/fig4_experiment/snake_7S3P.pkl'   # samo za paket (rešetka, S, P), raspored se ne koristi
OUT = 'paper_figures'
SEED = 100
SWEEP = dict(axis='x', reverse=False, amp=0.5, noise=0.0)   # amp iz skupa {0.5, 1, 1.5, 2} koji koristi početna populacija


def main():
    pack = load_solution(PACK_FROM)[0].pack
    ideal = (pack.no_groups - 1) * pack.no_cells_per_group
    for seed in range(SEED, SEED + 200):
        random.seed(seed); np.random.seed(seed)
        sweep = skewed_sweep(pack, **SWEEP)
        if sweep is not None and sweep.is_valid():
            sweep.calculate_total_fitness(); sweep.evaluate_solution()
            if sweep.eval_info['total_bridges'] < ideal:
                break
    else:
        raise RuntimeError('nijedan odgovarajući skewed sweep u 200 seedova')
    sweep.display(save=False, show=False)
    plt.gca().get_legend().remove()   # legenda je ista kao na Slici 4 (fig4_legend.pdf)
    plt.savefig(f"{OUT}/fig_heuristic_skewed_sweep.pdf", bbox_inches='tight')
    print(f"skewed sweep: seed {seed}, {sweep.eval_info['total_bridges']}/{ideal} mostova, {SWEEP}")

    random.seed(SEED); np.random.seed(SEED)
    population = generate_initial_population(pack, 100, False)
    for idx,sol in enumerate(population):
        sol.display(save=False, show=False)
        sol.evaluate_solution()
        if sol.eval_info['min_bridges']>1:
            plt.gca().get_legend().remove()
            plt.gca().invert_xaxis()
            plt.savefig(f"{OUT}/fig_heuristic_dtaa_{sol.eval_info['min_bridges']}.pdf", bbox_inches='tight')


    

if __name__ == '__main__':
    main()