"""Figure 2: an ideal layout, where every cell has exactly one bridge to the next group (b_k = P for all k)."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from kod import visuals
from kod.circuit import all_bridges
from kod.storage import load_solution
from kod.visuals import draw_bridges, save_legend

SOL = 'results/fig2_perfect_layout/rectangle_9_14.pkl'
OUT = 'paper_figures'
N_SEG = 0  # number of strongest currents to show


def main():
    visuals.FONT.update(axis=16, label=12, bms=8, ticks=12)
    sol, _ = load_solution(SOL)
    sol.display(save=False, show=False)


    sol.calculate_total_fitness()   # fills sol.bridge_results
    cells = sol.pack.grid.cells
    dist = lambda a, b: float(np.hypot(cells[a].x - cells[b].x, cells[a].y - cells[b].y))
    bridges = [b for b in all_bridges(sol.pack, sol.cell_to_group) if b['a'][1] == b['b'][1]]   # within a group
    for r in sol.bridge_results:
        for c1, c2 in r['best_bridges']:
            bridges.append({'a': [c1, 'n'], 'b': [c2, 'p'], 'length': dist(c1, c2)})
    for face in ('top', 'bottom'):
        draw_bridges(sol, bridges, face=face, save=False, show=False)
        ax = plt.gca()
        ax.get_legend().remove()
        ax.set_title('')
        plt.savefig(f'{OUT}/fig2_perfect_layout_{face}.pdf', bbox_inches='tight')
        plt.close('all')
    save_legend(sol.pack.no_groups, f'{OUT}/fig2_perfect_layout_legend.pdf', bridges=True, bms=False, n_segments=N_SEG, ncol=4)

if __name__ == '__main__':
    main()