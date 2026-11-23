"""Tablica 2: usporedba s baselineovima. Čita results/table2_table3_baseline/*.csv, piše paper_tables/table2_baseline.csv.

    uv run python tables/table2_baseline.py
"""
from _common import PAPER_ORDER, mean_std, paper_names, read_rows, write_table

METHODS = [('snake 1 red', 'Snake, 1 row'), ('snake 2 reda', 'Snake, 2 rows'),
           ('početna heuristika', 'Initial heuristics'), ('CLONALG w_split=0', 'CLONALG')]
# (stupac u CSV-u, naslov, pretvorba, format)
COLS = [('cell_max', 'dIc_max (%)', lambda v: (v - 1) * 100, '{:.2f}'), ('cell_std', 'sigma_c', lambda v: v, '{:.4f}'),
        ('bridge_max', 'Is_max', lambda v: v, '{:.2f}'), ('R_total', 'R_total (mOhm)', lambda v: v * 1000, '{:.1f}'),
        ('extra_comp', 'N_split', lambda v: v, '{:.1f}')]


def main():
    rows, names = read_rows('results/table2_table3_baseline'), paper_names()
    out = []
    for pack in PAPER_ORDER:
        for key, label in METHODS:
            sel = [r for r in rows if r['pack'] == pack and r['metoda'] == key]
            if key.startswith('snake'):
                sel = sel[:1]   # snake je deterministički; ako je paket pokrenut više puta, isti redak se ponavlja
            if not sel:
                out.append([names[pack], label, '–'] + ['–'] * len(COLS))
                continue
            out.append([names[pack], label, len(sel)] + [mean_std([f(float(r[c])) for r in sel], fmt) for c, _, f, fmt in COLS])
    write_table('paper_tables/table2_baseline.csv', ['Pack', 'Method', 'n'] + [c[1] for c in COLS], out)


if __name__ == '__main__':
    main()
