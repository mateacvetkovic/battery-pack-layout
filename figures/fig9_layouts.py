"""Figures 9a and 9c: layouts of the assembled 7S3P packs, mirrored to match the photographs (9b, 9d).

    uv run python figures/fig9_layouts.py
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from kod.storage import load_solution
from kod.visuals import save_legend


IN = 'results/fig9_experiment'
OUT = 'paper_figures'
# (solution, output file, mirroring axis)
PANELS = [('snake_7S3P', 'fig9a_snake_layout.pdf', 'y'), ('clonalg_7S3P', 'fig9c_clonalg_layout.pdf', 'x')]


def main():
    for name, out, flip in PANELS:
        sol, _ = load_solution(f'{IN}/{name}.pkl')
        sol.display(save=False, show=False)
        ax = plt.gca()
        ax.get_legend().remove()
        ax.invert_xaxis() if flip == 'x' else ax.invert_yaxis()
        plt.savefig(f'{OUT}/{out}', bbox_inches='tight')
        plt.close('all')
    save_legend(sol.pack.no_groups, f'{OUT}/fig9_legend.pdf', ncol=4)


if __name__ == '__main__':
    main()