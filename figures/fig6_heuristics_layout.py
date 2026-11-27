"""Figure 6: example layouts of the initial heuristics (§2.7.3) on the assembled 7S3P pack (the same pack as in Figure 9).
The snake layout on the same pack is Figure 9a.

    uv run python figures/fig6_heuristics_layout.py

Skewed sweep: the first seed from SEED onwards that gives a valid layout without the ideal number of bridges
is used (so that irregular group boundaries are visible). The seed used is printed; the result is reproducible.
"""
import random

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from kod.clonalg import generate_initial_population
from kod.heuristics import skewed_sweep
from kod.storage import load_solution

PACK_FROM = 'results/fig9_experiment/snake_7S3P.pkl'   # used only for the pack (grid, S, P); the layout is not used
OUT = 'paper_figures'
SEED = 100
SWEEP = dict(axis='x', reverse=False, amp=0.5, noise=0.0)   # amp from the set {0.5, 1, 1.5, 2} used by the initial population


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
        raise RuntimeError('no suitable skewed sweep layout in 200 seeds')
    sweep.display(save=False, show=False)
    plt.gca().get_legend().remove()   # the legend is the same as in Figure 9 (fig9_legend.pdf)
    plt.savefig(f"{OUT}/fig6_heuristic_skewed_sweep.pdf", bbox_inches='tight')
    print(f"skewed sweep: seed {seed}, {sweep.eval_info['total_bridges']}/{ideal} bridges, {SWEEP}")

    random.seed(SEED); np.random.seed(SEED)
    population = generate_initial_population(pack, 100, False)
    for idx,sol in enumerate(population):
        sol.display(save=False, show=False)
        sol.evaluate_solution()
        if sol.eval_info['min_bridges']==2:
            plt.gca().get_legend().remove()
            plt.gca().invert_xaxis()
            plt.savefig(f"{OUT}/fig6_heuristic_dtaa_{sol.eval_info['min_bridges']}.pdf", bbox_inches='tight')




if __name__ == '__main__':
    main()