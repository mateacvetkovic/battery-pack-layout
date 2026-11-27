"""Slika 4a i 4c: rasporedi sastavljenih paketa 7S3P, zrcaljeni tako da odgovaraju fotografijama (4b, 4d).

    uv run python figures/fig4_layouts.py
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from kod.storage import load_solution
from kod.visuals import save_legend


IN = 'results/fig4_experiment'
OUT = 'paper_figures'
# (rješenje, izlaz, zrcaljenje)
PANELS = [('snake_7S3P', 'fig4a_snake_layout.pdf', 'y'), ('clonalg_7S3P', 'fig4c_clonalg_layout.pdf', 'x')]


def main():
    for name, out, flip in PANELS:
        sol, _ = load_solution(f'{IN}/{name}.pkl')
        sol.display(save=False, show=False)
        ax = plt.gca()
        ax.get_legend().remove()
        ax.invert_xaxis() if flip == 'x' else ax.invert_yaxis()
        plt.savefig(f'{OUT}/{out}', bbox_inches='tight')
        plt.close('all')
    save_legend(sol.pack.no_groups, f'{OUT}/fig4_legend.pdf', ncol=4)


if __name__ == '__main__':
    main()
