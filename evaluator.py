from main import load_battery_solution
from src.kod.bridges import all_bridges, solve, print_result
from src.kod.visuals import draw_bridges
import numpy as np
import matplotlib

import glob
import os
import pickle
import sys
matplotlib.use('Agg')  # crta u datoteke, bez prozora

from src.kod.bridges import all_bridges, solve
from src.kod.visuals import draw_bridges
from src.kod.evaluation import R_CELL, R_PER_LENGTH
# sol, inputs = load_battery_solution('/home/mcvetkovic/Documents/diplomski/kod/rjesenja/baterija_saćasti_triangle_A36,0_B26,0_C28,0_2026-11-04_16-01-32_it1_id0.pkl')
# bridges = all_bridges(sol.pack, sol.cell_to_group)
# result = solve(sol.cell_to_group, bridges, r_cell=0.05, r_per_length=0.00003328, I=8)

# nom = result['nominal_current']
# print_result(result, bridges)

# draw_bridges(sol, bridges, currents=[c / nom for c in result['bridge_currents']], label='struja mosta / nazivna struja ćelije (I/P)', save=False, show=True)

# input("\nProgram je završio i prikazao rezultate. Za izlaz i zatvaranje svih prozora pritisnite ENTER... ")

from src.kod.evaluation import baseline_table, load_packs
# #baseline_table('rjesenja/paketi.json', clonalg_seeds=(0,), csv_path='baseline.csv', save_dir='rjesenja_baseline')

# baseline_table('rjesenja/paketi copy.json', clonalg_seeds=(0,15,100),
#                 w_split_values=(1000,0), csv_path='baseline_rect.csv', save_dir='rjesenja_baseline/rect')



def draw_all(folder, vmax=3):
    for path in sorted(glob.glob(os.path.join(folder, '*.pkl'))):
        with open(path, 'rb') as f:
            sol = pickle.load(f)['solution']
        base = path[:-4]
        sol.display(save=True, show=False, name=base + '.png')  # raspored ćelija po grupama
        bridges = all_bridges(sol.pack, sol.cell_to_group)  # svi mogući mostovi, kao u main.py
        res = solve(sol.cell_to_group, bridges, R_CELL, R_PER_LENGTH, sol.pack.no_cells_per_group)
        nom = res['nominal_current']
        draw_bridges(sol, bridges, currents=[c / nom for c in res['bridge_currents']], vmax=vmax,
                    label='struja mosta / nazivna struja ćelije (I/P)', save=True, name=base + '_mostovi.png', show=False)
        print('nacrtano:', os.path.basename(base))


# if __name__ == '__main__':
#     draw_all(sys.argv[1] if len(sys.argv) > 1 else 'rjesenja_baseline/rect')



"""
Pokreće usporedbu s baselineovima po planu: skupine paketa s različitim brojem pokretanja.
Iz korijena projekta:  python main_evaluacija.py            (cijeli plan)
                       python main_evaluacija.py 1 2        (samo skupine 1 i 2)
                       python main_evaluacija.py probno     (1 pokretanje, 3 iteracije, populacija 10: samo provjera da sve radi)
Rezultati po paketu: rezultati/<paket>.csv (jedan redak po metodi, omjeru i pokretanju) i rezultati/<paket>_sazetak.csv (prosjek ± std).
Paket čiji CSV već postoji se preskače, pa prekinut run možeš nastaviti ponovnim pokretanjem (obriši CSV da ga ponoviš).
"""
import os
import sys
import traceback

HEX_JSON = 'rjesenja/paketi.json'              # saćaste rešetke
ORTH_JSON = 'rjesenja/paketi copy.json'  # pravokutne (ortogonalne) rešetke
RATIOS = None
OUT_DIR = 'rezultati'
PICKLE_DIR = 'rjesenja_baseline/novo'

# (naziv skupine, JSON, imena paketa, broj pokretanja, vrijednosti w_split)
PLAN = [
    ('1_hex', HEX_JSON, ['trokut_2', 'trokut_4', 'pravokutnik_2'], 10, (0, 1000)),
    ('1_orth', ORTH_JSON, ['pravokutni_trokut_A', 'pravokutni_trokut_C_bms'], 10, (0,)),
    ('2_hex', HEX_JSON, ['trokut_3', 'trokut_5', 'pravokutnik_3'], 5, (0, 1000)),
    ('3_hex', HEX_JSON, ['pravokutnik_1'], 3, (0,)),
    ('3_orth', ORTH_JSON, ['pravokutni_pravokutnik_A', 'pravokutni_pravokutnik_B_bms', 'pravokutni_pravokutnik_C', 'pravokutni_trokut_B'], 3, (0,)),
]


def run(groups=None, probno=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    for group, json_path, names, runs, w_splits in PLAN:
        if groups and group.split('_')[0] not in groups:
            continue
        available = {p['name']: p for p in load_packs(json_path)}
        for name in names:
            if name not in available:
                print(f'[{group}] paket {name} ne postoji u {json_path}, preskačem', flush=True)
                continue
            csv_path = os.path.join(OUT_DIR, f'{name}.csv')
            if os.path.exists(csv_path):
                print(f'[{group}] {name}: {csv_path} već postoji, preskačem', flush=True)
                continue
            print(f'\n[{group}] {name}: {runs} pokretanja, w_split = {w_splits}', flush=True)
            kwargs = dict(runs=1, iterations=3, population_size=10, d_new_individuals=3, clones_per_antibody=3) if probno else dict(runs=runs)
            try:
                baseline_table([available[name]], csv_path=csv_path, summary_csv_path=os.path.join(OUT_DIR, f'{name}_sazetak.csv'),
                               save_dir=os.path.join(PICKLE_DIR, name), ratios=RATIOS, w_split_values=w_splits, **kwargs)
            except Exception:
                traceback.print_exc()
                print(f'[{group}] {name}: greška, nastavljam s idućim paketom', flush=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    run(groups={a for a in args if a != 'probno'} or None, probno='probno' in args)