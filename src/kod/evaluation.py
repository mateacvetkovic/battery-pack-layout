"""
Usporedba tvog rješenja s baselineovima po paketima iz JSON-a: snake s jednim redom, snake s dva reda, početna heuristika
(generate_initial_population) i konačno CLONALG rješenje. Struje se računaju solverom (bridges.py) sa SVIM mogućim mostovima
(zadano) ili samo s odabranima; omjeri su struja / nazivna struja ćelije (I/P), idealno = 1.

    from evaluation import baseline_table
    baseline_table('paketi.json', runs=10, csv_path='baseline.csv', summary_csv_path='baseline_sazetak.csv',
                   save_dir='rjesenja_baseline', ratios=(0.01, 0.05, 0.10), w_split_values=(0,))
"""
import csv
import random

import numpy as np

try:  # u projektu
    from src.kod.BatterySolution import BatterySolution
    from src.kod import IALG
    from src.kod.bridges import all_bridges, solve, junction_estimate
except ImportError:  # samostalno
    from BatterySolution import BatterySolution
    import IALG
    from bridges import all_bridges, solve, junction_estimate

R_CELL = 0.05            # Ω
R_PER_LENGTH = 3.328e-5  # Ω po jedinici duljine (duljine mostova su u mm)


def real_metrics(sol, r_cell=R_CELL, r_per_length=R_PER_LENGTH, selected=True, cell_limit=1.02, I=None):
    """Stvarne mjere dizajna iz solvera.
    selected=True: granični mostovi koje je heuristika odabrala (sol.bridge_results, treba izračunat fitness) + mostovi unutar grupe.
    selected=False: izgrađeni su SVI mogući mostovi (all_bridges), bridge_results se ne koristi."""
    pack, ctg = sol.pack, sol.cell_to_group
    if I is None:
        I = pack.no_cells_per_group
    cells = pack.grid.cells
    dist = lambda c, m: float(np.hypot(cells[c].x - cells[m].x, cells[c].y - cells[m].y))
    if selected:
        bridges = [b for b in all_bridges(pack, ctg) if b['a'][1] == b['b'][1]]  # mostovi unutar grupe
        for r in sol.bridge_results:  # granični mostovi koje je heuristika odabrala
            for c1, c2 in r['best_bridges']:
                bridges.append({'a': [c1, 'n'], 'b': [c2, 'p'], 'length': dist(c1, c2)})
    else:
        bridges = all_bridges(pack, ctg)
    res = solve(ctg, bridges, r_cell, r_per_length, I )  # I = P, pa je nazivna struja 1
    nom = res['nominal_current']
    skip = set(res['shorted_bridges'])  # idealni krajevi paketa nose 0 po pretpostavci
    cells_r = np.array(list(res['cell_currents'].values())) / nom
    all_r = [res['bridge_currents'][i] / nom for i in range(len(bridges)) if i not in skip]
    border_r = [res['bridge_currents'][i] / nom for i, b in enumerate(bridges) if i not in skip and b['a'][1] != b['b'][1]]
    worst_cell = max(res['cell_currents'], key=res['cell_currents'].get)
    je = junction_estimate(bridges, ctg, r_per_length)  # tvoja procjena otpora spoja po paru grupa
    return {'cell_max': float(cells_r.max()), 'cell_std': float(cells_r.std()), 'bridge_max': max(all_r),
            'border_max': max(border_r), 'R_total': res['R_total'], 'worst_cell': int(worst_cell),
            'junction_max': max(j['total'] for j in je.values()), 'cells_over': float((cells_r > cell_limit).mean()), 'cell_p95': float(np.percentile(cells_r, 95))}


def terms(sol):
    """Članovi fitnessa (iz zadnjeg calculate_total_fitness)."""
    d = sol.fitness_details
    return {'min_bridges': d['min_bridges'], 'total_bridges': d['total_bridges'], 'mean_bridge_score': float(d['mean_bridge_score']),
            'bridge_var': float(d['bridge_variance']), 'far_total': sol.far_total,
            'extra_comp': sum(sol.count_components(g) - 1 for g in range(sol.pack.no_groups)), 'fitness': float(sol.fitness)}


def evaluate(sol, r_cell=R_CELL, r_per_length=R_PER_LENGTH, selected=True):
    """Članovi fitnessa + stvarne mjere za jedno rješenje; None ako je nevaljano. selected: vidi real_metrics."""
    if not sol.is_valid():
        return None
    sol.calculate_total_fitness()
    if sol.fitness == -float('inf'):
        return None
    return {**terms(sol), **real_metrics(sol, r_cell, r_per_length, selected)}


def load_packs(path):
    """Učitava pakete iz JSON-a (isti format kao primjeri.json za batch_run.py): lista objekata s ključevima
    name, cell_type, cell_distance, net_type, shape_type, dimensions_cm, voltage, a neobavezno bms_ids, r_cell, r_per_length
    (r_cell i r_per_length zadaju omjer otpora za taj paket; zadano su R_CELL i R_PER_LENGTH).
    Vraća listu rječnika {'name', 'pack', 'r_cell', 'r_per_length'}."""
    import json
    try:
        from src.kod.main import setup_battery_pack, CELL_SPECS
    except ImportError:
        from main import setup_battery_pack, CELL_SPECS
    with open(path, encoding='utf-8') as f:
        examples = json.load(f)
    packs = []
    for i, ex in enumerate(examples):
        name = ex.get('name', f'paket{i + 1}')
        missing = [k for k in ('cell_type', 'cell_distance', 'net_type', 'shape_type', 'dimensions_cm', 'voltage') if k not in ex]
        if missing:
            raise ValueError(f'{name}: nedostaju ključevi {missing}')
        pack = setup_battery_pack({k: ex[k] for k in ('cell_type', 'cell_distance', 'net_type', 'shape_type', 'dimensions_cm')})
        if ex.get('bms_ids'):  # isti redoslijed kao u main.py: prvo BMS, pa napon
            pack.set_bms_cells(ex['bms_ids'])
        pack.set_voltage(ex['voltage'], CELL_SPECS[ex['cell_type']]['nominal_voltage'])
        packs.append({'name': name, 'pack': pack, 'inputs': dict(ex), 'r_cell': ex.get('r_cell', R_CELL), 'r_per_length': ex.get('r_per_length', R_PER_LENGTH)})
    return packs


def snake_baseline(pack, height=1):
    """Snake za bilo koji oblik paketa: ćelije (bez BMS) poredane u trake visine `height` redova (1 ili 2) ili stupaca, unutar
    trake po položaju, svaka druga traka obrnuta; prvih S*P ćelija na tom putu dijeli se redom u grupe po P.
    Isprobava redove/stupce i oba smjera početka i vraća (najbolje valjano rješenje po fitnessu, opis) ili (None, None)."""
    from itertools import product
    try:
        BS = BatterySolution
    except NameError:
        BS = None
    cells = [c for c in pack.grid.cells if c.id not in pack.bms_cell_ids]
    need = pack.no_groups * pack.no_cells_per_group
    best, best_desc = None, None
    for axis, flip_strips, flip_in in product(('redovi', 'stupci'), (False, True), (False, True)):
        line = (lambda c: c.row) if axis == 'redovi' else (lambda c: c.col)
        along = (lambda c: (c.x, c.y)) if axis == 'redovi' else (lambda c: (c.y, c.x))
        lines = sorted({line(c) for c in cells}, reverse=flip_strips)
        order = []
        for k in range(0, len(lines), height):
            strip_lines = set(lines[k:k + height])
            strip = sorted((c for c in cells if line(c) in strip_lines), key=along)
            if (k // height) % 2 == 1:
                strip.reverse()
            order += strip
        if flip_in:
            order = order[::-1]
        sol = BatterySolution(pack)
        for idx, c in enumerate(order[:need]):
            sol.assign_cell_to_group(c.id, idx // pack.no_cells_per_group)
        if not sol.is_valid():
            continue
        sol.calculate_total_fitness()
        if sol.fitness == -float('inf'):
            continue
        if best is None or sol.fitness > best.fitness:
            best, best_desc = sol, f'{axis}, {height} red(a)'
    return best, best_desc


def _nearest_bridge_length(pack):
    """Duljina mosta između dviju susjednih ćelija (najkraća udaljenost susjeda), u istim jedinicama kao r_per_length."""
    cells = pack.grid.cells
    return min(float(np.hypot(cells[c].x - cells[m].x, cells[c].y - cells[m].y))
               for c in range(min(len(cells), 60)) for m in pack.get_neighbours_ids(c))


def baseline_table(packs, runs=10, iterations=200, population_size=50, clones_per_antibody=5, d_new_individuals=12,
                   csv_path=None, summary_csv_path=None, all_bridges_built=True, save_dir=None, ratios=None,
                   w_split_values=(0.0,), stag_iter=50):
    """Po paketu: snake s jednim i s dva reda (deterministički, jedno pokretanje), početna heuristika (najbolje rješenje iz
    generate_initial_population bez zmija) i CLONALG (najbolje rješenje iz optimizer.run()). Početna heuristika i CLONALG ponavljaju se
    `runs` puta, svaki put s drugim seedom (100 + broj pokretanja), pa se za njih ispisuje prosjek +- standardna devijacija (n - 1).
    Zadane postavke su iz main.py (500 iteracija, populacija 50) pa 10 pokretanja traje dugo: prvo isprobaj jedan paket i malo pokretanja.

    csv_path: jedan redak po paketu, metodi, omjeru i pokretanju (stupac 'run'); upisuje se nakon svakog paketa, pa se ne gubi ako prekineš.
    summary_csv_path: prosjek i standardna devijacija po paketu, omjeru i metodi.
    ratios: npr. (0.01, 0.05, 0.10) = omjer otpora mosta između dvije susjedne ćelije i otpora ćelije (r_per_length * duljina / r_cell).
      Fitness ne ovisi o otporima, pa se optimizacija vrti jednom, a ista rješenja se za svaki omjer samo ponovno izračunaju solverom.
      None = koristi se r_per_length iz paketa (JSON ili zadano).
    w_split_values: npr. (0, 1000) = CLONALG se vrti zasebno za svaku težinu kazne za razdvojene grupe; fitness stupac se uvijek računa
      sa zadanim težinama. Stupac 'split' = ukupno dodatnih komponenti u grupama (0 = sve grupe kompaktne).
    all_bridges_built=True: struje sa SVIM mogućim mostovima (kao u main.py); False: samo odabrani mostovi.
    save_dir: svako rješenje sprema se kao <paket>_<metoda>[_run<k>].pkl ({'solution', 'inputs'} kao save_battery_solution).
    packs: putanja do JSON-a ili lista iz load_packs. Vraća listu redaka."""
    import inspect, os, pickle
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    if isinstance(packs, str):
        packs = load_packs(packs)
    extra = {'stag_iter': stag_iter} if 'stag_iter' in inspect.signature(IALG.ClonalgOptimizer).parameters else {}
    cols = [('fitness', 'fitness', '{:.1f}'), ('total_bridges', 'mostova', '{:.1f}'), ('extra_comp', 'split', '{:.1f}'),
            ('cell_max', 'cell_max', '{:.3f}'), ('cell_std', 'cell_std', '{:.4f}'), ('bridge_max', 'bridge_max', '{:.2f}'),
            ('junction_max', 'junction_max', '{:.5f}'), ('R_total', 'R_total', '{:.4f}'), ('cells_over', 'cells>1.02', '{:.0%}')]
    out, summary = [], []
    csv_file, writer = None, None
    try:
        for p in packs:
            pk = p['pack']
            sols = {}  # (metoda, pokretanje) -> rješenje
            for h, key in ((1, 'snake 1 red'), (2, 'snake 2 reda')):
                sol, _ = snake_baseline(pk, h)
                if sol:
                    sols[(key, 0)] = sol
            old = BatterySolution.calculate_total_fitness.__defaults__
            try:
                for k in range(runs):
                    seed = 100 + k
                    random.seed(seed); np.random.seed(seed)
                    init = [x for x in IALG.generate_initial_population(pk, population_size, snakes=False) if x.fitness > -float('inf')]
                    if init:
                        sols[('početna heuristika', k)] = max(init, key=lambda x: x.fitness)
                    for w in w_split_values:
                        d = list(old); d[4] = w  # redoslijed: w_score, w_min_bridges, w_total_bridges, w_bridge_balance, w_split, w_far
                        BatterySolution.calculate_total_fitness.__defaults__ = tuple(d)
                        random.seed(seed); np.random.seed(seed)
                        o = IALG.ClonalgOptimizer(pk, max_iterations=iterations, population_size=population_size,
                                                  clones_per_antibody=clones_per_antibody, d_new_individuals=d_new_individuals, **extra)
                        found = o.run()  # ista lista koju main.py ispisuje kao "pronađena rješenja"
                        if found:
                            sols[(f"CLONALG w_split={w:g}", k)] = max(found, key=lambda x: x.fitness)
                    BatterySolution.calculate_total_fitness.__defaults__ = old
                    print(f"[{p['name']}] pokretanje {k + 1}/{runs} gotovo", flush=True)
            finally:
                BatterySolution.calculate_total_fitness.__defaults__ = old
            if save_dir:
                for (name, k), sol in sols.items():
                    suffix = '' if name.startswith('snake') else f'_run{k}'
                    with open(os.path.join(save_dir, f"{p['name']}_{name.replace(' ', '_')}{suffix}.pkl"), 'wb') as f:
                        pickle.dump({'solution': sol, 'inputs': p['inputs']}, f)

            d0 = _nearest_bridge_length(pk)
            pack_rows = []
            for ratio in (ratios if ratios else [None]):
                rpl = p['r_per_length'] if ratio is None else ratio * p['r_cell'] / d0
                omjer = rpl * d0 / p['r_cell']
                by_method = {}
                for (name, k), sol in sols.items():
                    r = evaluate(sol, p['r_cell'], rpl, selected=not all_bridges_built)
                    if r:
                        by_method.setdefault(name, []).append(r)
                        pack_rows.append({'pack': p['name'], 'metoda': name, 'run': k, 'omjer_R': omjer, 'r_per_length': rpl, **r})
                print(f"\n{p['name']} ({pk.no_groups}S {pk.no_cells_per_group}P), R_most/R_ćelije = {omjer:.1%}, r_per_length = {rpl:.4g}, "
                      f"r_cell = {p['r_cell']}  (prosjek ± std preko pokretanja; n = broj valjanih)")
                print(f"  {'metoda':22}{'n':>3}" + ''.join(f"{c[1]:>20}" for c in cols))
                for name, rs in by_method.items():
                    cells = []
                    srow = {'pack': p['name'], 'metoda': name, 'omjer_R': omjer, 'n': len(rs)}
                    for key, _, fmt in cols:
                        v = np.array([r[key] for r in rs], dtype=float)
                        sd = v.std(ddof=1) if len(v) > 1 else float('nan')
                        srow[key + '_mean'], srow[key + '_std'] = float(v.mean()), float(sd)
                        cells.append(f"{fmt.format(v.mean())} ± {fmt.format(sd) if len(v) > 1 else '-'}".rjust(20))
                    summary.append(srow)
                    print(f"  {name:22}{len(rs):>3}" + ''.join(cells))
            out += pack_rows
            if csv_path and pack_rows:
                if writer is None:
                    csv_file = open(csv_path, 'w', newline='')
                    writer = csv.DictWriter(csv_file, fieldnames=list(pack_rows[0])); writer.writeheader()
                writer.writerows(pack_rows); csv_file.flush()
    finally:
        if csv_file:
            csv_file.close()
    if summary_csv_path and summary:
        with open(summary_csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
    return out