"""Tablica 4: vrijeme CLONALG-a. Čita results/table4_timing/*.csv, piše paper_tables/table4_timing.csv.
Vrijeme po iteraciji = prosjek omjera time_total_s / iterations_total po pokretanjima.

    uv run python tables/table4_timing.py
"""
from _common import mean_std, paper_names, read_rows, write_table

ORDER = ['pravokutni_pravokutnik_A', 'pravokutni_trokut_B', 'trokut_3', 'pravokutnik_2', 'trokut_4', 'trokut_2', 'trokut_21700']


def main():
    rows, names = read_rows('results/table4_timing'), paper_names()
    packs = [p for p in ORDER if any(r['pack'] == p for r in rows)]
    usable = {}
    if any('Nu' not in r for r in rows):  # stari CSV-ovi nemaju Nu: izračunaj iz definicije paketa
        from kod.BatteryPack import load_packs
        usable = {n: p['pack'].usable_cells for n, p in load_packs('data/packages.json', names=packs).items()}
    out = []
    for pack in packs:
        sel = [r for r in rows if r['pack'] == pack]
        per_iter = [float(r['time_total_s']) / int(r['iterations_total']) for r in sel]
        out.append([names[pack], f"{sel[0]['S']} x {sel[0]['P']}", sel[0].get('Nu') or usable[pack], len(sel),
                    f'{sum(per_iter) / len(per_iter):.2f}',
                    mean_std([float(r['time_to_best_s']) for r in sel], '{:.0f}'),
                    mean_std([float(r['time_total_s']) for r in sel], '{:.1f}')])
    write_table('paper_tables/table4_timing.csv', ['Pack', 'S x P', 'Nu', 'n', 'Time per iter. (s)', 'Time to best (s)', 'Total time (s)'], out)


if __name__ == '__main__':
    main()
