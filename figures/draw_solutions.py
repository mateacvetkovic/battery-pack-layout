"""Draw all solutions of one pack from Table 2 (group layout).

    uv run python figures/draw_solutions.py pravokutnik_3
Images are written to results/table2_table3_baseline/solutions/<pack>/*.png
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
    print('drawn', path[:-4] + '.png')