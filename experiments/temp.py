import csv, glob
IDEAL = {'trokut_2': 95, 'trokut_3': 52, 'trokut_4': 72, 'trokut_5': 48, 'pravokutnik_1': 52,
         'pravokutnik_2': 65, 'pravokutnik_3': 36, 'pravokutni_trokut_A': 45, 'pravokutni_trokut_B': 54,
         'pravokutni_trokut_C_bms': 45, 'pravokutni_pravokutnik_A': 35, 'pravokutni_pravokutnik_B_bms': 36,
         'pravokutni_pravokutnik_C': 36, 'trokut_21700': 100}   # (S - 1) * P iz Tablice 1
for path in sorted(glob.glob('results/table2_table3_baseline/*.csv')):
    for r in csv.DictReader(open(path, encoding='utf-8')):
        if r['metoda'].startswith('CLONALG') and int(r['total_bridges']) == IDEAL[r['pack']]:
            print(r['pack'], r['metoda'], 'run', r['run'], 'seed', r['seed'])
print('nista')