"""Zajedničko za skripte u tables/: imena iz članka, čitanje sirovih CSV-ova, prosjek ± std uzorka (n - 1)."""
import csv
import glob
import os
import statistics

# redoslijed kao u Tablici 1
PAPER_ORDER = ['trokut_2', 'trokut_3', 'trokut_4', 'trokut_5', 'pravokutnik_1', 'pravokutnik_2', 'pravokutnik_3',
               'pravokutni_trokut_A', 'pravokutni_trokut_B', 'pravokutni_trokut_C_bms',
               'pravokutni_pravokutnik_A', 'pravokutni_pravokutnik_B_bms', 'pravokutni_pravokutnik_C', 'trokut_21700']


def paper_names(path='data/pack_names.csv'):
    with open(path, encoding='utf-8') as f:
        return {r['code_name']: r['paper_name'] for r in csv.DictReader(f)}


def read_rows(folder):
    """Svi retci iz svih *.csv u mapi (osim *_sazetak*)."""
    rows = []
    for path in sorted(glob.glob(os.path.join(folder, '*.csv'))):
        if 'sazetak' in os.path.basename(path):
            continue
        with open(path, encoding='utf-8') as f:
            rows += list(csv.DictReader(f))
    return rows


def mean_std(values, fmt):
    """'m ± s' sa std uzorka (n - 1); jedna vrijednost bez ±."""
    if len(values) == 1:
        return fmt.format(values[0])
    return f'{fmt.format(statistics.mean(values))} ± {fmt.format(statistics.stdev(values))}'


def write_table(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    widths = [max(len(str(x)) for x in col) for col in zip(header, *rows)]
    for r in [header] + rows:
        print('  '.join(str(x).ljust(wd) for x, wd in zip(r, widths)))
    print(f'-> {path}')
