"""Tablica 3: CLONALG s dopuštenim (w_split=0) i zabranjenim (w_split=1000) razdvajanjem grupa.

    uv run python tables/table3_split.py
"""
from _common import PAPER_ORDER, mean_std, paper_names, read_rows, write_table

VARIANTS = [('CLONALG w_split=1000', 'no'), ('CLONALG w_split=0', 'yes')]


def main():
    rows, names = read_rows('results/table2_table3_baseline'), paper_names()
    out = []
    for pack in PAPER_ORDER:
        if not any(r['pack'] == pack and r['metoda'] == 'CLONALG w_split=1000' for r in rows):
            continue
        for key, split in VARIANTS:
            sel = [r for r in rows if r['pack'] == pack and r['metoda'] == key]
            out.append([names[pack], split, len(sel), mean_std([(float(r['cell_max']) - 1) * 100 for r in sel], '{:.2f}'),
                        mean_std([float(r['bridge_max']) for r in sel], '{:.2f}'), mean_std([float(r['extra_comp']) for r in sel], '{:.1f}')])
    write_table('paper_tables/table3_split.csv', ['Pack', 'Split', 'n', 'dIc_max (%)', 'Is_max', 'N_split'], out)


if __name__ == '__main__':
    main()
