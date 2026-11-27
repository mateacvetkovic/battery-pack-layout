"""Slika 3: prosječni (puna crta) i najbolji (isprekidano) fitness populacije u 3 pokretanja za Triangle 4 i Triangle 6.

    uv run python figures/fig3_convergence.py
"""
import csv
import glob
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

PACKS = [('trokut_5', 'Triangle 4'), ('pravokutni_trokut_B', 'Triangle 6')]
COLORS = ['#2a78d6', '#eb6834', '#1baf7a']
OUT = 'paper_figures/fig3_convergence.pdf'
UPPER = {'trokut_5': 65.0}

def main():
    runs = defaultdict(list)   # (paket, pokretanje) -> [(iteracija, prosječni, najbolji)]
    for path in sorted(glob.glob('results/fig3_convergence/*.csv')):
        with open(path, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                runs[(r['pack'], int(r['run']))].append((int(r['iteration']), float(r['mean_fitness']), float(r['best_fitness'])))

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.3))
    for ax, (name, label) in zip(axes, PACKS):
        xmax = 0
        for run, c in enumerate(COLORS):
            pts = runs.get((name, run))
            if not pts:
                continue
            it = [p[0] for p in pts]
            ax.plot(it, [p[1] for p in pts], color=c, lw=1.3, drawstyle='steps-post')
            ax.plot(it, [p[2] for p in pts], color=c, lw=1.0, ls='--', drawstyle='steps-post')
            ax.plot(it[-1], pts[-1][2], 'o', color=c, ms=3.5)
            xmax = max(xmax, max(it))
        ax.set_title(label, fontsize=9)
        ax.set_xlabel('Iteration', fontsize=8)
        ax.set_xlim(0, xmax)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3, lw=0.5)
        ax.set_xlim(0, xmax * 1.03)
    axes[0].set_ylabel('Fitness', fontsize=8)
    if name in UPPER:
          ax.axhline(UPPER[name], color='0.5', lw=0.8, ls=':')
          ax.text(1, UPPER[name], ' upper bound', fontsize=6, va='bottom', color='0.4')
    handles = [Line2D([], [], color=c, lw=1.3, label=f'Run {k + 1}') for k, c in enumerate(COLORS)]
    handles += [Line2D([], [], color='0.3', lw=1.3, label='Population average'),
                Line2D([], [], color='0.3', lw=1.0, ls='--', label='Best')]
    fig.legend(handles=handles, loc='upper center', ncol=5, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(OUT, bbox_inches='tight', pad_inches=0.05)


if __name__ == '__main__':
    main()