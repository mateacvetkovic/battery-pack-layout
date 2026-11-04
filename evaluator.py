from main import load_battery_solution
from src.kod.bridges import all_bridges, solve, print_result
from src.kod.visuals import draw_bridges
import numpy as np
sol, inputs = load_battery_solution('/home/mcvetkovic/Documents/diplomski/kod/rjesenja/baterija_saćasti_triangle_A36,0_B26,0_C28,0_2026-11-04_16-01-32_it1_id0.pkl')
bridges = all_bridges(sol.pack, sol.cell_to_group)
result = solve(sol.cell_to_group, bridges, r_cell=1.0, r_per_length=0.01, I=8)
nom = result['nominal_current']
print_result(result, bridges)

draw_bridges(sol, bridges, currents=[c / nom for c in result['bridge_currents']], label='struja mosta / nazivna struja ćelije (I/P)', save=False, show=True)

input("\nProgram je završio i prikazao rezultate. Za izlaz i zatvaranje svih prozora pritisnite ENTER... ")


