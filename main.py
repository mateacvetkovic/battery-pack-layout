"""Interaktivni program (diplomski rad): unos paketa, uklanjanje ćelija za BMS, odabir napona i CLONALG.
Rezultati (slike, .pkl i .json rješenja) spremaju se u interactive_runs/. Eksperimenti iz članka su u experiments/.

    uv run python main.py
"""
import os
import random
import sys
from datetime import datetime

import matplotlib.pyplot as plt

from kod.BatteryPack import setup_battery_pack
from kod.circuit import all_bridges, solve, print_result, junction_estimate
from kod.clonalg import ClonalgOptimizer
from kod.config import ALLOWED_CELL_TYPES, ALLOWED_NET_TYPES, CELL_SPECS, strip_r_per_length
from kod.storage import save_solution
from kod.visuals import draw_bridges

R_PER_LENGTH = strip_r_per_length(0.15)   # traka 0.15 x 7 mm, kao u sastavljenim paketima
OUT_DIR = 'interactive_runs'


def get_user_inputs():
    print("=" * 60)
    print("     OPTIMIZACIJA I DIZAJN BATERIJSKOG PAKETA")
    print("=" * 60)

    while True:
        print("\n[1/4] Odaberite tip ćelije:")
        for idx, c_type in enumerate(ALLOWED_CELL_TYPES, 1):
            print(f"  {idx}. {c_type}")
        try:
            c_choice = int(input("Unos: ")) - 1
            if 0 <= c_choice < len(ALLOWED_CELL_TYPES):
                cell_type = ALLOWED_CELL_TYPES[c_choice]
                break
            else:
                print("Krivi odabir. Odaberite ponuđeni broj.")
        except ValueError:
            print("Unesite cijeli broj.")

    while True:
        print("\n[2/4] Unesite udaljenost među ćelijama(mm): ")
        try:
            d = int(input("Unos: "))
            if CELL_SPECS[cell_type]['diameter'] <= d:
                break
            else:
                print("Unesite ispravnu vrijednost udaljenosti.")
        except ValueError:
            print("Unesite cijeli broj.")

    while True:
        print("\n[3/4] Odaberite tip mreže (grid):")
        for idx, net in enumerate(ALLOWED_NET_TYPES, 1):
            print(f"  {idx}. {net}")
        try:
            n_choice = int(input("Unos: ")) - 1
            if 0 <= n_choice < len(ALLOWED_NET_TYPES):
                net_type = ALLOWED_NET_TYPES[n_choice]
                break
            else:
                print("Odaberite ponuđeni broj.")
        except ValueError:
            print("Unesite cijeli broj.")

    while True:
        print("\n[4/4] Odaberite oblik paketa:")
        print("  1. Pravokutnik (Širina x Visina)")
        print("  2. Trokut (3 stranice)")
        try:
            shape_choice = int(input("Unos: "))
            if shape_choice in [1, 2]:
                break
            else:
                print("Krivi odabir. Unesite 1 ili 2.")
        except ValueError:
            print("Unesite cijeli broj.")

    while True:
        try:
            if shape_choice == 1:
                shape_type = 'rectangle'
                print("\n[4/4] Unesite dimenzije pravokutnika:")
                w_cm = float(input("Unesite širinu paketa (cm): "))
                h_cm = float(input("Unesite visinu paketa (cm): "))
                if w_cm > 0 and h_cm > 0:
                    dimensions_cm = [w_cm, h_cm]
                    break
                else:
                    print("Dimenzije moraju biti veće od 0.")
            else:
                shape_type = 'triangle'
                print("\n[4/4] Unesite dimenzije trokuta:")
                a_cm = float(input("Unesite stranicu a (cm): "))
                b_cm = float(input("Unesite stranicu b (cm): "))
                c_cm = float(input("Unesite stranicu c (cm): "))
                if a_cm <= 0 or b_cm <= 0 or c_cm <= 0:
                    print("Sve stranice moraju biti veće od 0.")
                elif (a_cm + b_cm > c_cm) and (a_cm + c_cm > b_cm) and (b_cm + c_cm > a_cm):
                    dimensions_cm = [a_cm, b_cm, c_cm]
                    break
                else:
                    print("Neispravne dimenzije! Zbroj dviju stranica mora biti veći od treće.")
        except ValueError:
            print("Unesite ispravnu brojčanu vrijednost.")

    return {
        'cell_type': cell_type,
        'cell_distance':d,
        'net_type': net_type,
        'shape_type': shape_type,
        'dimensions_cm': dimensions_cm
    }

def interactive_cell_removal_and_voltage_setup(pack):
    print("\n" + "="*60)
    print("CRTANJE INICIJALNOG GRID-A...")
    print("Prikazuje se prozor s brojevima (ID-jevima) ćelija...")
    print("="*60)
    
    pack.display()  

    print("\n[BMS] Uklanjanje ćelija za BMS, šarafe i nosače:")
    remove_input = input("Unesite ID-jeve ćelija koje želite ukloniti (odvojene zarezom, npr. 0,1,12) ili stisnite ENTER za nastavljanje bez uklanjanja ćelija: ")

    if remove_input.strip():
        try:
            bms_ids = [int(x.strip()) for x in remove_input.split(',')]
            pack.set_bms_cells(bms_ids)  
            print(f"-> Uspješno uklonjene ćelije za BMS/komponente.")
            
            print("Prikaz mreže s označenim BMS mjestima...")
            pack.display()  
        except ValueError:
            print("Neispravan unos ID-jeva. Nastavlja se bez uklanjanja.")

    print(f"\nStanje paketa:")
    print(f" - Ukupno iskoristivih ćelija: {pack.usable_cells}")

    cell_v = CELL_SPECS[pack.cell_type]['nominal_voltage']

    # ispis mogućih konfiguracija
    print("\n" + "="*60)
    print("MOGUĆE S/P KONFIGURACIJE PAKETA:")
    print("="*60)
    configs = pack.get_possible_configurations(cell_v)
    for cfg in configs:
        print(f" - {cfg['S']}S {cfg['P']}P -> Napon: {cfg['voltage']:.1f} V (Iskorišteno ćelija: {cfg['used_cells']}/{pack.usable_cells})")

    # unos napona paketa
    while True:
        print("\nElektrični parametri:")
        try:
            target_pack_voltage = float(input("Unesite željeni napon paketa (V) [npr. 36 ili 48]: "))
            if target_pack_voltage > 0 and target_pack_voltage >= cell_v:
                try:
                    pack.set_voltage(target_pack_voltage, cell_v)
                    break
                except ValueError as e:
                    print(f"Greška pri postavljanju napona: {e}")
            else:
                print("Neispravan napon paketa.")
        except ValueError:
            print("Unesite ispravan broj.")

    print(f"\nOdabrana konfiguracija:")
    print(f" - Konfiguracija: {pack.no_groups}S {pack.no_cells_per_group}P")  
    
    if pack.usable_cells < pack.no_groups:
        print("\n[GREŠKA] Nedovoljno ćelija u paketu za zadani napon! Program prekinut.")
        sys.exit()

def run_optimization(pack, inputs):
    print("\n" + "="*60)
    print("KREĆE OPTIMIZACIJA I EVOLUCIJA POVEZIVANJA GRUPA...")
    print("="*60)
    current_dir = os.getcwd()

    grid_type = inputs['net_type']
    shape_type = inputs['shape_type']
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if shape_type == 'rectangle':
        W, H = inputs['dimensions_cm']
        file_name = f"{OUT_DIR}/baterija_{grid_type}_{shape_type}_W{W}_H{H}_{timestamp}"
    else:
        a,b,c = inputs['dimensions_cm']
        file_name = f"{OUT_DIR}/baterija_{grid_type}_{shape_type}_A{a}_B{b}_C{c}_{timestamp}"
    file_name = file_name.replace(".", ",")
    os.makedirs(OUT_DIR, exist_ok=True)
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(2**32)
    random.seed(seed)
    print(f"Seed: {seed}")

    best_sol_ever = None
    best_fitness_ever = 0




    for i in range(1):
        print(f"{i+1}/3 pokušaja")
        optimizer = ClonalgOptimizer(pack, max_iterations=500, population_size=50, stag_iter=100)
        best_solutions = optimizer.run()  
        print(f"Pronađeno {len(best_solutions)} rješenja.")
        for id, best_solution in enumerate(best_solutions):
            print(f"\n[EVALUACIJA RJEŠENJA {id+1}/{len(best_solutions)}]")
            fitness_val = best_solution.fitness  
            eval_info = best_solution.evaluate_solution(verbose=True)  
            if (best_fitness_ever < best_solution.fitness):
                best_fitness_ever = best_solution.fitness
                best_sol_ever = best_solution

            file_name_it = f"{file_name}_it{i+1}_id{id}.png"
            save_solution(file_name_it.replace('.png', ''), best_solution, inputs, seed=seed)
            # print(f"\n-> Ukupna ocjena kvalitete paketa (Fitness): {fitness_val:.2f}")  
            # print(f"-> Minimalan broj direktnih spojeva između ikojih susjednih grupa: {eval_info['min_bridges']}")  
            # print(f"-> Ukupan broj direktnih serijskih spojeva u paketu/idealan broj spojeva: {eval_info['total_bridges']}/{pack.no_cells_per_group*(pack.no_groups-1)}")  
            # if eval_info['total_bridges'] == pack.no_cells_per_group*(pack.no_groups-1):
            #     best_solution.display(save=True, name=file_name_it)
            #     print(f"-> Slika spremljena na lokaciju: {os.path.join(current_dir, file_name_it)}")
            #     break
            # if eval_info['worst_group'] is not None:
            #     print(f"-> Najkritičnija grupa s najmanje direktnih spojeva: Grupa {eval_info['worst_group']}")  
            S, P = pack.no_groups, pack.no_cells_per_group
            ideal = P * (S - 1)
            pairs = eval_info['connection_results']  # (g, g+1) -> rezultat za taj par grupa
            unique = sum(r['num_bridges'] for r in pairs.values())
            split_groups = [g for g, cells in best_solution.group_dict.items() if len(best_solution.get_components(cells)) > 1]
            worst_pair = min(pairs, key=lambda k: pairs[k]['num_bridges'])

            print(f"\n-> Fitness: {fitness_val:.2f}")
            print(f"-> Jedinstveni (izravni) mostovi: {unique}/{ideal}  (najmanje u paru: {eval_info['min_bridges']})")
            print(f"-> Najslabiji par grupa: G{worst_pair[0]}-G{worst_pair[1]} ({pairs[worst_pair]['num_bridges']}/{P} jedinstvenih mostova)")
            print(f"-> Razdvojene grupe: {split_groups if split_groups else 'nema, sve su kompaktne'}")

            print("\nGeneriranje grafičkog prikaza konačnog paketa...")
            if (id==0):
                best_solution.display(save=True, name=file_name_it)
                bridges = all_bridges(best_solution.pack, best_solution.cell_to_group)
                result = solve(best_solution.cell_to_group, bridges, r_cell=CELL_SPECS[pack.cell_type]['R_cell'], r_per_length=R_PER_LENGTH, I=pack.no_cells_per_group)
                je = junction_estimate(bridges, best_solution.cell_to_group, r_per_length=R_PER_LENGTH)
                print_result(result, bridges, junction=je)  
                nom = result['nominal_current']

                draw_bridges(best_solution, bridges, currents=[c / nom for c in result['bridge_currents']], vmax=3, label='struja mosta / nazivna struja ćelije (I/P)', save=True, name=file_name_it+'_mostovi.png', show=False)
            else:
                best_solution.display(save=True, show=False,name=file_name_it)
            print(f"-> Slika spremljena na lokaciju: {os.path.join(current_dir, file_name_it)}")

    input("\nProgram je završio i prikazao rezultate. Za izlaz i zatvaranje svih prozora pritisnite ENTER... ")
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
