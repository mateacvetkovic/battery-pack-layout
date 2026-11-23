"""Mjere iz §3.2 članka, izračunate električnim modelom (circuit.py): ΔIc,max, σc, Is,max, Rtotal i Nsplit,
te članovi fitnessa za isto rješenje."""
import numpy as np

from kod.circuit import all_bridges, solve, junction_estimate
from kod.config import PAPER

R_CELL = PAPER['r_cell']
R_PER_LENGTH = PAPER['r_per_length']


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
