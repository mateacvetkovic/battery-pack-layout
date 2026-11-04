import json
import numpy as np


# ---------- 1. all possible bridges ----------
def all_bridges(pack, cell_to_group):
    """Svi mogući mostovi: između susjednih ćelija iste grupe (na p i na n strani) i između susjednih ćelija
    grupe g (n strana) i g+1 (p strana). Most = {'a': [cell, side], 'b': [cell, side], 'length': d}.
    Mostovi na p strani grupe 0 i n strani zadnje grupe su uključeni radi crtanja, ali u proračunu nose struju 0
    jer su te stezaljke idealno spojene (vidi _node)."""
    n = pack.no_groups
    cells = pack.grid.cells
    dist = lambda c, m: float(np.hypot(cells[c].x - cells[m].x, cells[c].y - cells[m].y))
    bridges = []
    for c in range(len(cell_to_group)):
        g = cell_to_group[c]
        if not 0 <= g < n:  # neiskorištene ćelije imaju grupu -1
            continue
        for m in pack.get_neighbours_ids(c):
            if cell_to_group[m] == g and c < m:  # unutar grupe, svaki par jednom
                for side in ('n', 'p'):
                    bridges.append({'a': [c, side], 'b': [m, side], 'length': dist(c, m)})
            elif cell_to_group[m] == g + 1:  # između grupa: n strana od g prema p strani od g+1
                bridges.append({'a': [c, 'n'], 'b': [m, 'p'], 'length': dist(c, m)})
    return bridges


# ---------- 2. saving and loading ----------
def save_solution(path, cell_to_group, bridges, r_cell, r_per_length, I):
    """Neobavezno: sprema ulaz proračuna (grupe ćelija, mostove, otpore, struju) da se kasnije može ponoviti."""
    json.dump({'cell_to_group': list(map(int, cell_to_group)), 'bridges': bridges, 'r_cell': r_cell,
               'r_per_length': r_per_length, 'I': I}, open(path, 'w'))


def load_solution(path):
    """Vraća rječnik čiji su ključevi baš argumenti od solve, pa vrijedi solve(**load_solution(path))."""
    return json.load(open(path))


# ---------- 3. equations and solving ----------
def _node(c, side, cell_to_group):
    """Ime čvora (stezaljke). Sve p stezaljke grupe 0 su jedan čvor (IN), sve n stezaljke zadnje grupe jedan (OUT)."""
    if side == 'p' and cell_to_group[c] == 0:
        return 'IN'
    if side == 'n' and cell_to_group[c] == max(cell_to_group):
        return 'OUT'
    return f'{c}{side}'


def _resistors(cell_to_group, bridges, r_cell, r_per_length):
    """Lista (čvor1, čvor2, otpor, oznaka): svaka ćelija ('cell', id) i svaki most ('bridge', indeks)."""
    ctg = cell_to_group
    res = []
    for c, g in enumerate(ctg):
        if g >= 0:
            res.append((_node(c, 'p', ctg), _node(c, 'n', ctg), r_cell, ('cell', c)))
    for i, b in enumerate(bridges):
        (c1, s1), (c2, s2) = b['a'], b['b']
        res.append((_node(c1, s1, ctg), _node(c2, s2, ctg), r_per_length * b['length'], ('bridge', i)))
    return res


def _matrix(resistors, I):
    """KCL u svakom čvoru: G·V = b. OUT je uzemljen (V=0), pa nije u sustavu; u IN se ubacuje struja I."""
    nodes = sorted({x for a, b, _, _ in resistors for x in (a, b)} - {'OUT'})
    idx = {n: k for k, n in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for a, b, r, _ in resistors:
        for x, y in ((a, b), (b, a)):
            if x in idx:
                G[idx[x], idx[x]] += 1 / r
                if y in idx:
                    G[idx[x], idx[y]] -= 1 / r
    rhs = np.zeros(len(nodes)); rhs[idx['IN']] = I
    return nodes, G, rhs


def solve(cell_to_group, bridges, r_cell, r_per_length, I):
    """Rješava mrežu izravno nad podacima u memoriji. Vraća
    {'R_total', 'nominal_current' (= I / P), 'cell_currents': {id: struja}, 'bridge_currents': [struja po indeksu u bridges]}.
    Struje su u jedinici u kojoj je zadan I (ampere samo ako je I u amperima)."""
    resistors = _resistors(cell_to_group, bridges, r_cell, r_per_length)
    nodes, G, rhs = _matrix(resistors, I)
    V = dict(zip(nodes, np.linalg.solve(G, rhs))); V['OUT'] = 0.0
    current = {label: abs(V[a] - V[b]) / r for a, b, r, label in resistors}
    P = sum(1 for g in cell_to_group if g == 0)  # ćelija u grupi, pa je nazivna struja ćelije I / P
    shorted = [l[1] for a, b, _, l in resistors if l[0] == 'bridge' and a == b]  # mostovi na idealnim krajevima, struja 0
    return {'R_total': float(V['IN'] / I), 'nominal_current': I / P, 'shorted_bridges': shorted,
            'cell_currents': {l[1]: float(i) for l, i in current.items() if l[0] == 'cell'},
            'bridge_currents': [float(current[('bridge', i)]) for i in range(len(bridges))]}


# ---------- 4. result: print and save ----------
def print_result(result, bridges, top=5, top_cells=5, idle=0.05):
    """Ispisuje ukupni otpor, statistiku po skupinama (ćelije, mostovi između grupa, mostovi unutar grupe),
    `top_cells` najopterećenijih ćelija i `top` najopterećenijih mostova (između kojih ćelija).
    Faktor vršnosti = max / prosjek; 'gotovo bez struje' = omjer ispod `idle` (nazivne struje ćelije)."""
    cc, bc, nom = result['cell_currents'], result['bridge_currents'], result['nominal_current']
    skip = set(result['shorted_bridges'])  # idealni krajevi nose 0 po pretpostavci, ne ulaze u statistiku
    print(f"R_total = {result['R_total']:.4f}, nazivna struja ćelije I/P = {nom:.4g} (omjeri niže su struja / I/P)")
 
    def stat(naziv, ratios, with_idle):
        mean, mx = sum(ratios) / len(ratios), max(ratios)
        extra = f", gotovo bez struje (< {idle:.0%}): {sum(r < idle for r in ratios) / len(ratios):.0%}" if with_idle else ""
        print(f"  {naziv} ({len(ratios)}): prosjek {mean:.3f}, max {mx:.3f}, faktor vršnosti {mx / mean:.2f}{extra}")
 
    print("statistika (omjeri prema nazivnoj struji):")
    stat('ćelije', [c / nom for c in cc.values()], False)
    between = [bc[i] / nom for i, b in enumerate(bridges) if i not in skip and b['a'][1] != b['b'][1]]
    within = [bc[i] / nom for i, b in enumerate(bridges) if i not in skip and b['a'][1] == b['b'][1]]
    stat('mostovi između grupa', between, True)
    stat('mostovi unutar grupe', within, True)
    if skip:
        print(f"  (bez {len(skip)} mostova na idealnim krajevima paketa, struja 0 po pretpostavci)")
 
    lo = min(cc, key=cc.get)
    print(f"najopterećenije ćelije (najmanje opterećena: ćelija {lo}, omjer {cc[lo] / nom:.3f}):")
    for c in sorted(cc, key=cc.get, reverse=True)[:top_cells]:
        print(f"  ćelija {c}: omjer {cc[c] / nom:.3f}")
    print(f"najopterećeniji mostovi (od {len(bc)}):")
    for i in sorted(range(len(bc)), key=lambda i: -bc[i])[:top]:
        (c1, s1), (c2, s2) = bridges[i]['a'], bridges[i]['b']
        print(f"  most {i}: ćelija {c1} ({s1}) - ćelija {c2} ({s2}), omjer {bc[i] / nom:.3f}  (struja {bc[i]:.4g})")
 
def save_result(path, result):
    """Sprema rezultat solve-a u JSON (ključevi ćelija postaju stringovi)."""
    json.dump(result, open(path, 'w'))


def export_spice(path, cell_to_group, bridges, r_cell, r_per_length, I):
    """Piše SPICE netlistu (LTspice, ngspice) iste mreže, za provjeru u drugom softveru. OUT je čvor 0 (masa),
    struja I se ubacuje u IN. Otpornici između istog čvora (mostovi na idealnim krajevima) se preskaču, nose 0."""
    lines = ['* mreza paketa: Rc = ćelije, Rb = mostovi', f'I1 0 IN DC {I}']
    for a, b, r, (kind, k) in _resistors(cell_to_group, bridges, r_cell, r_per_length):
        if a != b:
            lines.append(f"R{'c' if kind == 'cell' else 'b'}{k} {'0' if a == 'OUT' else a} {'0' if b == 'OUT' else b} {r}")
    lines += ['.op', '.end']
    open(path, 'w').write('\n'.join(lines) + '\n')
 