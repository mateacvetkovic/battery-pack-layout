from main import setup_battery_pack
from src.kod.BatterySolution import BatterySolution 
from src.kod.bridges import solve, print_result
from src.kod.visuals import draw_bridges

# pravokutnik 7 x 8 cm daje 12 ćelija u 4 reda po 3 (naizmjenično pomaknuti), 3 grupe po 4 ćelije
pack = setup_battery_pack({'cell_type': '18650', 'cell_distance': 20, 'net_type': 'saćasti',
                           'shape_type': 'rectangle', 'dimensions_cm': [7, 8, 3]})
pack.set_voltage(10.8, 3.6)

# id ćelija po retku, od vrha slike: (a1 a2 b1) (a3 b2 c1) (a4 b3 c2) (b4 c3 c4)
a1, a2, b1, a3, b2, c1, a4, b3, c2, b4, c3, c4 = range(12)
sol = BatterySolution(pack)
for c in (a1, a2, a3, a4): sol.assign_cell_to_group(c, 0)
for c in (b1, b2, b3, b4): sol.assign_cell_to_group(c, 1)
for c in (c1, c2, c3, c4): sol.assign_cell_to_group(c, 2)


def bridge(c1, side1, c2, side2):
    assert c2 in pack.get_neighbours_ids(c1), (c1, c2)  # most smije spajati samo susjedne ćelije
    p, q = pack.grid.cells[c1], pack.grid.cells[c2]
    return {'a': [c1, side1], 'b': [c2, side2], 'length': ((p.x - q.x) ** 2 + (p.y - q.y) ** 2) ** 0.5}


bridges = (
    [bridge(x, 'n', y, 'n') for x, y in [(a1, a2), (a1, a3), (a2, a3), (a3, a4)]]            # G0 unutar grupe (zeleno)
    + [bridge(x, 'p', y, 'p') for x, y in [(a1, a2), (a1, a3), (a2, a3), (a3, a4)]]            # G0 unutar grupe, p strana (idealni kraj, struja 0)
    + [bridge(x, 'n', y, 'p') for x, y in [(a2, b1), (a2, b2), (a3, b2), (a3, b3), (a4, b3), (a4, b4)]]  # G0 -> G1 (narančasto)
    + [bridge(x, 'p', y, 'p') for x, y in [(b1, b2), (b2, b3), (b3, b4)]]                    # G1 unutar grupe, p strana (žuto)
    + [bridge(x, 'n', y, 'n') for x, y in [(b1, b2), (b2, b3), (b3, b4)]]                    # G1 unutar grupe, n strana (žuto)
    + [bridge(x, 'n', y, 'p') for x, y in [(b1, c1), (b2, c1), (b2, c2), (b3, c2), (b3, c3), (b4, c3)]]  # G1 -> G2 (crveno)
    + [bridge(x, 'p', y, 'p') for x, y in [(c1, c2), (c2, c3), (c3, c4), (c2, c4)]]          # G2 unutar grupe, p strana (svijetloplavo)
    + [bridge(x, 'n', y, 'n') for x, y in [(c1, c2), (c2, c3), (c3, c4), (c2, c4)]]          # G2 unutar grupe, n strana (idealni kraj, struja 0)
)

# duljina mosta u mm (razmak ćelija je 20), pa je r_per_length = 0.05 / 20 da most duljine jednog razmaka ima 0.05
result = solve(sol.cell_to_group, bridges, r_cell=1.0, r_per_length=0.05 / 20, I=8)
print_result(result, bridges, top=len(bridges))

cc=result['cell_currents']
print(cc)
nom = result['nominal_current']
draw_bridges(sol, bridges, currents=[c / nom for c in result['bridge_currents']], label='struja mosta / nazivna struja ćelije (I/P)', save=True, name='3grupe_mostovi.png', show=False)