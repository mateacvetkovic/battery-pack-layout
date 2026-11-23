"""Slika 3: prosječni fitness populacije u 3 pokretanja za Triangle 4 i Triangle 6.

    uv run python figures/fig3_convergence.py
"""
import csv
import glob
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PACKS = [('trokut_5', 'Triangle 4'), ('pravokutni_trokut_B', 'Triangle 6')]
COLORS = ['#2a78d6', '#eb6834', '#1baf7a']


def main():
    runs = defaultdict(list)   # (paket, pokretanje) -> [(iteracija, prosječni fitness)]
    for path in sorted(glob.glob('results/fig3_convergence/*.csv')):
        with open(path, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                runs[(r['pack'], int(r['run']))].append((int(r['iteration']), float(r['mean_fitness'])))

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.4))
    for ax, (name, label) in zip(axes, PACKS):
        xmax = 0
        for run in range(len(COLORS)):
            pts = runs.get((name, run))
            if pts:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], color=COLORS[run], lw=1.5, drawstyle='steps-post')
                xmax = max(xmax, max(p[0] for p in pts))
        ax.set_title(label, fontsize=9)
        ax.set_xlabel('Iteration', fontsize=8)
        ax.set_xlim(0, xmax)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3, lw=0.5)
    axes[0].set_ylabel('Average population fitness', fontsize=8)
    handles = [plt.Line2D([], [], color=c, lw=1.5) for c in COLORS]
    fig.legend(handles, ['Run 1', 'Run 2', 'Run 3'], loc='upper center', ncol=5, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig('paper_figures/fig3_convergence.pdf')


if __name__ == '__main__':
    main()
