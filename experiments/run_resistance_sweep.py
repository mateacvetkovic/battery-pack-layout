"""Nije u članku: ista rješenja iz Tablice 2 ponovno izračunata za 4 kombinacije trake i ćelije (optimizacija se ne ponavlja).
Podupire tvrdnju iz §3.1 da poredak metoda ne ovisi o otporima.

    uv run python experiments/run_resistance_sweep.py

Izlaz: results/extra_resistance_sweep/resistance_sweep.csv
"""
import glob
import os

import matplotlib
matplotlib.use('Agg')

from kod.config import strip_r_per_length
from kod.metrics import real_metrics
from kod.storage import load_solution, write_rows

SOLUTIONS = 'results/table2_table3_baseline/solutions'
OUT = 'results/extra_resistance_sweep/resistance_sweep.csv'
SCENARIOS = [(0.3, 0.05), (0.3, 0.03), (0.15, 0.05), (0.15, 0.03)]  # (debljina trake mm, R_cell Ohm)


def main():
    rows = []
    for path in sorted(glob.glob(os.path.join(SOLUTIONS, '**', '*.pkl'), recursive=True)):
        sol, _ = load_solution(path)
        sol.calculate_total_fitness()
        for thickness, r_cell in SCENARIOS:
            rpl = strip_r_per_length(thickness)
            m = real_metrics(sol, r_cell=r_cell, r_per_length=rpl, selected=False)
            rows.append({'file': os.path.basename(path)[:-4], 'strip_mm': thickness, 'r_cell': r_cell,
                         'ratio': rpl * sol.pack.d / r_cell, 'cell_overcurrent_pct': (m['cell_max'] - 1) * 100,
                         'cell_std': m['cell_std'], 'segment_max': m['bridge_max'], 'R_total': m['R_total']})
    write_rows(OUT, rows)
    print(f'{len(rows)} redaka -> {OUT}')


if __name__ == '__main__':
    main()
