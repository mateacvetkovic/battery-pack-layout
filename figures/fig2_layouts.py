"""Slika 2: Triangle 3 (trokut_4), snake i CLONALG (pokretanje 0), s preopterećenim ćelijama i 4 najjača segmenta.

    uv run python figures/fig2_layouts.py
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from kod.config import PAPER
from kod.storage import load_solution
from kod import visuals
from kod.visuals import draw_layout_currents, save_colorbar, save_legend
from kod.metrics import real_metrics
from kod.visuals import solve_all_bridges

SOL = 'results/table2_table3_baseline/solutions/trokut_4/trokut_4_{}.pkl'
OUT = 'paper_figures'
N_SEG = 4
PANELS = [('snake_1_row', 'fig2a_triangle3_snake.pdf'), ('clonalg_split_allowed_run3', 'fig2b_triangle3_clonalg3.pdf')]


def main():
    visuals.FONT.update(axis=16, label=12, bms=8, ticks=12)   # kao u članku (Slika 2)
    for method, out in PANELS:
        sol, _ = load_solution(SOL.format(method))
        sol.display(save=False, show=False)
        ax = plt.gca()
        ax.get_legend().remove()  # legenda grupa ide u zasebnu sliku
        vals = draw_layout_currents(ax, sol, PAPER['r_cell'], PAPER['r_per_length'], n_segments=N_SEG)
        print(method, 'najjači segmenti:', [round(v, 2) for v in vals])
        m = real_metrics(sol, PAPER['r_cell'], PAPER['r_per_length'], selected=False)
        print(f"{method}: dIc_max = {(m['cell_max'] - 1) * 100:.2f} %, sigma_c = {m['cell_std']:.4f}, "
              f"Is_max = {m['bridge_max']:.2f}, R_total = {m['R_total'] * 1000:.1f} mOhm")
        _, res = solve_all_bridges(sol, PAPER['r_cell'], PAPER['r_per_length'])
        nom = res['nominal_current']
        top = sorted(res['cell_currents'].items(), key=lambda kv: -kv[1])[:5]
        print(method, 'najopterećenije ćelije (id, I/Inom):', [(c, round(I / nom, 3)) for c, I in top])
        print(method, 'ćelija iznad 1.03:', sum(I / nom > 1.03 for I in res['cell_currents'].values()))
        # plt.savefig(f'{OUT}/{out}', bbox_inches='tight')
        # plt.close('all')
    save_legend(sol.pack.no_groups, f'{OUT}/fig2_legend.pdf', bms=True, n_segments=N_SEG, ncol=6)
    # save_colorbar(f'{OUT}/fig2_colorbar.pdf')


if __name__ == '__main__':
    main()
