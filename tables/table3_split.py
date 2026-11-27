"""Tablica 3: CLONALG s dopuštenim (w_split=0) i zabranjenim (w_split=1000) razdvajanjem grupa.
Piše paper_tables/table3_split.csv i paper_tables/table3_extremes.csv (po varijanti i mjeri najmanja i najveća srednja vrijednost).

    uv run python tables/table3_split.py
"""
import statistics

from _common import PAPER_ORDER, mean_std, paper_names, read_rows, write_extremes, write_table

# (naslov, pretvorba retka, format)
METRICS = [('dIc_max (%)', lambda r: (float(r['cell_max']) - 1) * 100, '{:.2f}'),
           ('Is_max', lambda r: float(r['bridge_max']), '{:.2f}'), ('N_split', lambda r: float(r['extra_comp']), '{:.1f}')]

VARIANTS = [('CLONALG w_split=1000', 'no'), ('CLONALG w_split=0', 'yes')]


def main():
    rows, names = read_rows('results/table2_table3_baseline'), paper_names()
    out, extremes = [], []
    for pack in PAPER_ORDER:
        if not any(r['pack'] == pack and r['metoda'] == 'CLONALG w_split=1000' for r in rows):
            continue
        for key, split in VARIANTS:
            sel = [r for r in rows if r['pack'] == pack and r['metoda'] == key]
            out.append([names[pack], split, len(sel)] + [mean_std([f(r) for r in sel], fmt) for _, f, fmt in METRICS])
            for title, f, fmt in METRICS:   # srednja vrijednost zaokružena kao u tablici
                extremes.append((f'Split = {split}', names[pack], title, float(fmt.format(statistics.mean(f(r) for r in sel)))))
    write_table('paper_tables/table3_split.csv', ['Pack', 'Split', 'n'] + [m[0] for m in METRICS], out)
    write_extremes('paper_tables/table3_extremes.csv', extremes, {title: fmt for title, _, fmt in METRICS})


if __name__ == '__main__':
    main()