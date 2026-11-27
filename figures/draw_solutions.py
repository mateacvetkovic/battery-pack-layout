"""Crta sva rješenja jednog paketa iz Tablice 2 (raspored grupa).

    uv run python figures/draw_solutions.py pravokutnik_3
Slike idu u results/table2_table3_baseline/solutions/<paket>/*.png
"""
import glob
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from kod.storage import load_solution

folder = f'results/table2_table3_baseline/solutions/{sys.argv[1]}'
for path in sorted(glob.glob(f'{folder}/*.pkl')):
    sol, _ = load_solution(path)
    sol.display(save=False, show=False)
    plt.savefig(path[:-4] + '.png', bbox_inches='tight')
    plt.close('all')
    print('nacrtano', path[:-4] + '.png')