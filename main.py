"""Interactive program (diploma thesis): pack input, cell removal for the BMS, voltage selection and CLONALG.
Results (images, .pkl and .json solutions) are saved to interactive_runs/. The experiments from the paper are in experiments/.

    uv run python main.py [seed]        # default seed: SEED_BASE from config.py
"""
import os
import random
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from kod.BatteryPack import setup_battery_pack
from kod.circuit import all_bridges, solve, print_result, junction_estimate
from kod.clonalg import ClonalgOptimizer
from kod.config import ALLOWED_CELL_TYPES, ALLOWED_NET_TYPES, CELL_SPECS, SEED_BASE, strip_r_per_length
from kod.storage import save_solution
from kod.visuals import draw_bridges

R_PER_LENGTH = strip_r_per_length(0.15)   # 0.15 x 7 mm strip, as in the assembled packs
OUT_DIR = 'interactive_runs'


def get_user_inputs():
    print("=" * 60)
    print("     BATTERY PACK OPTIMIZATION AND DESIGN")
    print("=" * 60)

    while True:
        print("\n[1/4] Select the cell type:")
        for idx, c_type in enumerate(ALLOWED_CELL_TYPES, 1):
            print(f"  {idx}. {c_type}")
        try:
            c_choice = int(input("Input: ")) - 1
            if 0 <= c_choice < len(ALLOWED_CELL_TYPES):
                cell_type = ALLOWED_CELL_TYPES[c_choice]
                break
            else:
                print("Invalid choice. Enter one of the listed numbers.")
        except ValueError:
            print("Enter an integer.")

    while True:
        print("\n[2/4] Enter the distance between cells (mm): ")
        try:
            d = int(input("Input: "))
            if CELL_SPECS[cell_type]['diameter'] <= d:
                break
            else:
                print("Invalid distance: it must be at least the cell diameter.")
        except ValueError:
            print("Enter an integer.")

    while True:
        print("\n[3/4] Select the grid type:")
        for idx, net in enumerate(ALLOWED_NET_TYPES, 1):
            print(f"  {idx}. {net}")
        try:
            n_choice = int(input("Input: ")) - 1
            if 0 <= n_choice < len(ALLOWED_NET_TYPES):
                net_type = ALLOWED_NET_TYPES[n_choice]
                break
            else:
                print("Enter one of the listed numbers.")
        except ValueError:
            print("Enter an integer.")

    while True:
        print("\n[4/4] Select the pack shape:")
        print("  1. Rectangle (width x height)")
        print("  2. Triangle (3 sides)")
        try:
            shape_choice = int(input("Input: "))
            if shape_choice in [1, 2]:
                break
            else:
                print("Invalid choice. Enter 1 or 2.")
        except ValueError:
            print("Enter an integer.")

    while True:
        try:
            if shape_choice == 1:
                shape_type = 'rectangle'
                print("\n[4/4] Enter the rectangle dimensions:")
                w_cm = float(input("Pack width (cm): "))
                h_cm = float(input("Pack height (cm): "))
                if w_cm > 0 and h_cm > 0:
                    dimensions_cm = [w_cm, h_cm]
                    break
                else:
                    print("Dimensions must be greater than 0.")
            else:
                shape_type = 'triangle'
                print("\n[4/4] Enter the triangle dimensions:")
                a_cm = float(input("Side a (cm): "))
                b_cm = float(input("Side b (cm): "))
                c_cm = float(input("Side c (cm): "))
                if a_cm <= 0 or b_cm <= 0 or c_cm <= 0:
                    print("All sides must be greater than 0.")
                elif (a_cm + b_cm > c_cm) and (a_cm + c_cm > b_cm) and (b_cm + c_cm > a_cm):
                    dimensions_cm = [a_cm, b_cm, c_cm]
                    break
                else:
                    print("Invalid dimensions: the sum of any two sides must be greater than the third.")
        except ValueError:
            print("Enter a valid number.")

    return {
        'cell_type': cell_type,
        'cell_distance':d,
        'net_type': net_type,
        'shape_type': shape_type,
        'dimensions_cm': dimensions_cm
    }

def interactive_cell_removal_and_voltage_setup(pack):
    print("\n" + "="*60)
    print("DRAWING THE INITIAL GRID...")
    print("A window with cell numbers (IDs) is shown...")
    print("="*60)

    pack.display()

    print("\n[BMS] Removing cells for the BMS, screws and mounts:")
    remove_input = input("Enter the IDs of the cells to remove (comma-separated, e.g. 0,1,12) or press ENTER to continue without removing cells: ")

    if remove_input.strip():
        try:
            bms_ids = [int(x.strip()) for x in remove_input.split(',')]
            pack.set_bms_cells(bms_ids)
            print(f"-> Cells for the BMS/components removed.")

            print("Showing the grid with the BMS positions marked...")
            pack.display()
        except ValueError:
            print("Invalid cell IDs. Continuing without removing cells.")

    print(f"\nPack status:")
    print(f" - Total usable cells: {pack.usable_cells}")

    cell_v = CELL_SPECS[pack.cell_type]['nominal_voltage']

    # list of possible configurations
    print("\n" + "="*60)
    print("POSSIBLE S/P PACK CONFIGURATIONS:")
    print("="*60)
    configs = pack.get_possible_configurations(cell_v)
    for cfg in configs:
        print(f" - {cfg['S']}S {cfg['P']}P -> Voltage: {cfg['voltage']:.1f} V (cells used: {cfg['used_cells']}/{pack.usable_cells})")

    # pack voltage input
    while True:
        print("\nElectrical parameters:")
        try:
            target_pack_voltage = float(input("Enter the desired pack voltage (V) [e.g. 36 or 48]: "))
            if target_pack_voltage > 0 and target_pack_voltage >= cell_v:
                try:
                    pack.set_voltage(target_pack_voltage, cell_v)
                    break
                except ValueError as e:
                    print(f"Error while setting the voltage: {e}")
            else:
                print("Invalid pack voltage.")
        except ValueError:
            print("Enter a valid number.")

    print(f"\nSelected configuration:")
    print(f" - Configuration: {pack.no_groups}S {pack.no_cells_per_group}P")

    if pack.usable_cells < pack.no_groups:
        print("\n[ERROR] Not enough cells in the pack for the requested voltage. Program terminated.")
        sys.exit()

def run_optimization(pack, inputs):
    print("\n" + "="*60)
    print("STARTING OPTIMIZATION OF THE GROUP CONNECTIONS...")
    print("="*60)
    current_dir = os.getcwd()

    grid_type = inputs['net_type']
    shape_type = inputs['shape_type']
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if shape_type == 'rectangle':
        W, H = inputs['dimensions_cm']
        file_name = f"{OUT_DIR}/battery_{grid_type}_{shape_type}_W{W}_H{H}_{timestamp}"
    else:
        a,b,c = inputs['dimensions_cm']
        file_name = f"{OUT_DIR}/battery_{grid_type}_{shape_type}_A{a}_B{b}_C{c}_{timestamp}"
    file_name = file_name.replace(".", ",")
    os.makedirs(OUT_DIR, exist_ok=True)
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else SEED_BASE
    random.seed(seed); np.random.seed(seed)
    print(f"Seed: {seed}")

    optimizer = ClonalgOptimizer(pack, max_iterations=500, population_size=50, stag_iter=100)
    best_solutions = optimizer.run()
    print(f"Found {len(best_solutions)} solutions.")
    S, P = pack.no_groups, pack.no_cells_per_group
    ideal = P * (S - 1)
    for k, sol in enumerate(best_solutions):
        print(f"\n[EVALUATION OF SOLUTION {k+1}/{len(best_solutions)}]")
        eval_info = sol.evaluate_solution(verbose=True)
        name = f"{file_name}_id{k}"
        save_solution(name, sol, inputs, seed=seed)

        pairs = eval_info['connection_results']  # (g, g+1) -> result for that pair of groups
        unique = sum(r['num_bridges'] for r in pairs.values())
        split_groups = [g for g, cells in sol.group_dict.items() if len(sol.get_components(cells)) > 1]
        worst_pair = min(pairs, key=lambda p: pairs[p]['num_bridges'])

        print(f"\n-> Fitness: {sol.fitness:.2f}")
        print(f"-> Unique (direct) bridges: {unique}/{ideal}  (fewest in a pair: {eval_info['min_bridges']})")
        print(f"-> Weakest pair of groups: G{worst_pair[0]}-G{worst_pair[1]} ({pairs[worst_pair]['num_bridges']}/{P} unique bridges)")
        print(f"-> Split groups: {split_groups if split_groups else 'none, all groups are compact'}")

        print("\nGenerating the plot of the final pack...")
        if k == 0:
            sol.display(save=True, name=f"{name}.png")
            bridges = all_bridges(sol.pack, sol.cell_to_group)
            result = solve(sol.cell_to_group, bridges, r_cell=CELL_SPECS[pack.cell_type]['R_cell'], r_per_length=R_PER_LENGTH, I=P)
            je = junction_estimate(bridges, sol.cell_to_group, r_per_length=R_PER_LENGTH)
            print_result(result, bridges, junction=je)
            nom = result['nominal_current']
            draw_bridges(sol, bridges, currents=[c / nom for c in result['bridge_currents']], vmax=3,
                         label='bridge current / nominal cell current (I/P)', save=True, name=f"{name}_bridges.png", show=False)
        else:
            sol.display(save=True, show=False, name=f"{name}.png")
        print(f"-> Image saved to: {os.path.join(current_dir, name)}.png")

    input("\nThe program has finished and shown the results. Press ENTER to exit and close all windows... ")
    plt.close('all')


if __name__ == "__main__":
    inputs = get_user_inputs()
    try:
        pack = setup_battery_pack(inputs)
    except ValueError as e:
        print(e)
        sys.exit()
    interactive_cell_removal_and_voltage_setup(pack)
    run_optimization(pack, inputs)