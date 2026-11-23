"""Operatori mutacije CLONALG-a (§2.8.3): boundary swap, three-way cyclic exchange, steal and shift."""
import random


def mutate_swap_boundary(solution):
    """
    ide kroz sve celije odabrane grupe, pronade susjedne celije (one koje su granica),
    zamjenjuje neke od njih i vraca samo validno rjesenje.

    Argumenti:
        solution (object): rjesenje na kojem se provodi mutacija.

    Vraca:
        bool: true ako je mutacija uspjesno primijenjena, inace false.
    """
    selected_g = select_groups_for_mutation(solution)
    
    if selected_g is None or selected_g == -1:
        return False

    selected_cells = list(solution.group_dict.get(selected_g, set()))
    
    swap_candidates = []
    for c_A in selected_cells:
        for c_B in solution.pack.get_neighbours_ids(c_A):
            neighbor_g = solution.cell_to_group[c_B]
            
            if neighbor_g is not None and neighbor_g != -1 and neighbor_g != selected_g:
                swap_candidates.append(('swap', c_A, c_B, neighbor_g))
                
            elif neighbor_g == -1 or neighbor_g is None:
                swap_candidates.append(('empty', c_A, c_B, selected_g))

    if not swap_candidates:
        return False
        
    random.shuffle(swap_candidates)
    for action_type, c_A, c_B, target_g in swap_candidates:
        if action_type == 'swap':
            solution.assign_cell_to_group(c_A, target_g)
            solution.assign_cell_to_group(c_B, selected_g)
            
            is_selected_ok = solution.is_group_connected(selected_g)
            is_neighbor_ok = solution.is_group_connected(target_g)
            
            if is_selected_ok and is_neighbor_ok:
                return True
                
            solution.assign_cell_to_group(c_A, selected_g)
            solution.assign_cell_to_group(c_B, target_g)
            
        elif action_type == 'empty':
            solution.assign_cell_to_group(c_A, -1)
            solution.assign_cell_to_group(c_B, selected_g)
            
            if solution.is_group_connected(selected_g):
                return True
            solution.assign_cell_to_group(c_A, selected_g)
            solution.assign_cell_to_group(c_B, -1)
    return False


def mutate_cyclic_3way_swap(solution):
    """
    provodi trostranu kruznu zamjenu celija izmedju tri susjedne grupe radi poticanja lokalne promjene.

    Argumenti:
        solution (object): rjesenje na kojem se izvrsava zamjena celija.

    Vraca:
        bool: true ako je zamjena uspjela uz ocuvanu povezanost, inace false.
    """
    g1 = select_groups_for_mutation(solution)
    if g1 is None:
        return False

    g1_cells = list(solution.group_dict.get(g1, set()))
    
    g2_candidates = set()
    for c1 in g1_cells:
        for nbr in solution.pack.get_neighbours_ids(c1):
            g_nbr = solution.cell_to_group[nbr]
            if g_nbr is not None and g_nbr != -1 and g_nbr != g1:
                g2_candidates.add(g_nbr)
                
    if not g2_candidates:
        return False
    g2 = random.choice(list(g2_candidates))
    
    g2_cells = list(solution.group_dict.get(g2, set()))
    g3_candidates = set()
    for c2 in g2_cells:
        for nbr in solution.pack.get_neighbours_ids(c2):
            g_nbr = solution.cell_to_group[nbr]
            if g_nbr is not None and g_nbr != -1 and g_nbr not in (g1, g2):
                g3_candidates.add(g_nbr)
                
    if not g3_candidates:
        return False
    g3 = random.choice(list(g3_candidates))

    candidates_c1 = [c for c in g1_cells if any(solution.cell_to_group[n] == g2 for n in solution.pack.get_neighbours_ids(c))]
    candidates_c2 = [c for c in g2_cells if any(solution.cell_to_group[n] == g3 for n in solution.pack.get_neighbours_ids(c))]
    candidates_c3 = [c for c in solution.group_dict.get(g3, set()) if any(solution.cell_to_group[n] == g1 for n in solution.pack.get_neighbours_ids(c))]

    if not candidates_c1 or not candidates_c2 or not candidates_c3:
        return False

    random.shuffle(candidates_c1)
    random.shuffle(candidates_c2)
    random.shuffle(candidates_c3)

    for c1 in candidates_c1[:5]:
        for c2 in candidates_c2[:5]:
            for c3 in candidates_c3[:5]:
                solution.group_dict[g1].remove(c1)
                solution.group_dict[g1].add(c3)
                solution.group_dict[g2].remove(c2)
                solution.group_dict[g2].add(c1)
                solution.group_dict[g3].remove(c3)
                solution.group_dict[g3].add(c2)
                
                solution.cell_to_group[c1] = g2
                solution.cell_to_group[c2] = g3
                solution.cell_to_group[c3] = g1
                
                if solution.is_group_connected(g1) and solution.is_group_connected(g2) and solution.is_group_connected(g3):
                    return True
                
                solution.group_dict[g1].remove(c3)
                solution.group_dict[g1].add(c1)
                solution.group_dict[g2].remove(c1)
                solution.group_dict[g2].add(c2)
                solution.group_dict[g3].remove(c2)
                solution.group_dict[g3].add(c3)
                
                solution.cell_to_group[c1] = g1
                solution.cell_to_group[c2] = g2
                solution.cell_to_group[c3] = g3

    return False


def mutate_steal_and_shift(solution):
    """
    mutacija 'kradi i gurni' (steal & shift):
    1. odabire grupu a i pronalazi njezinu rubnu celiju koja granici s grupom b.
    2. provjerava ima li grupa b u svojoj okolini prazno mjesto (-1).
    3. ako ima, grupa a uzima poziciju od grupe b, a celija grupe b klizi u prazno mjesto.

    Argumenti:
        solution (object): rjesenje na kojem se primjenjuje mutacija.

    Vraca:
        bool: true ako je mutacija bila uspjesna, inace false.
    """
    all_groups = [g for g in solution.group_dict.keys() if g != -1]
    if not all_groups:
        return False

    group_a = select_groups_for_mutation(solution)
    cells_a = list(solution.group_dict.get(group_a, set()))
    if not cells_a:
        return False

    candidates_for_steal = []
    for cell_a in cells_a:
        for neighbor_id in solution.pack.get_neighbours_ids(cell_a):
            neighbor_g = solution.cell_to_group[neighbor_id] if neighbor_id < len(solution.cell_to_group) else -1
            if neighbor_g != -1 and neighbor_g != group_a:
                candidates_for_steal.append((neighbor_id, neighbor_g))

    if not candidates_for_steal:
        return False

    cell_to_steal, group_b = random.choice(candidates_for_steal) #celija iz grupe b koju cemo ubacit u a
    cells_b = list(solution.group_dict.get(group_b, set()))
    cell_from_b_to_shift = None
    empty_spot = None

    for cell_b in cells_b:
        if cell_b == cell_to_steal:
            continue
        for neighbor_id in solution.pack.get_neighbours_ids(cell_b):
            neighbor_g = solution.cell_to_group[neighbor_id] if neighbor_id < len(solution.cell_to_group) else -1
            if neighbor_g == -1:
                cell_from_b_to_shift = cell_b
                empty_spot = neighbor_id
                break
        if empty_spot is not None:
            break

    if empty_spot is None:
        return False


    cell_from_a_to_free = None
    for cell_a in cells_a:
        if cell_a == cell_to_steal:
            continue
        for neighbor_id in solution.pack.get_neighbours_ids(cell_a):
            neighbor_g = solution.cell_to_group[neighbor_id] if neighbor_id < len(solution.cell_to_group) else -1
            if neighbor_g == -1:
                cell_from_a_to_free = neighbor_id
                cell_to_drop = cell_a
                break
        if cell_from_a_to_free is not None:
            break

    if cell_from_a_to_free is None:
        return False

    backup_steal = solution.cell_to_group[cell_to_steal]
    backup_shift = solution.cell_to_group[cell_from_b_to_shift]
    backup_empty = solution.cell_to_group[empty_spot]
    backup_drop = solution.cell_to_group[cell_to_drop]
    backup_drop_spot = solution.cell_to_group[cell_from_a_to_free]



    solution.assign_cell_to_group(cell_to_steal, group_a)
    solution.assign_cell_to_group(empty_spot, group_b)
    solution.assign_cell_to_group(cell_to_drop, -1)
    if solution.is_group_connected(group_a) and solution.is_group_connected(group_b):
        return True

    solution.assign_cell_to_group(cell_to_steal, backup_steal)
    solution.assign_cell_to_group(empty_spot, backup_empty)
    solution.assign_cell_to_group(cell_to_drop, backup_drop)

    return False


def select_groups_for_mutation(solution, random_prob=0.5):
    """
    odabire grupu za mutaciju na temelju vjerojatnosti: nasumicno ili najgoru grupu prema fitnessu.

    Argumenti:
        solution (object): rjesenje iz kojeg se bira grupa.
        random_prob (float): vjerojatnost odabira potpuno nasumicne grupe.

    Vraca:
        int/object: identifikator odabrane grupe ili none ako nema grupa.
    """
    all_groups = [g for g in solution.group_dict.keys() if g != -1]    
    if random.random() < random_prob and all_groups:
        return random.choice(all_groups)
            
    worst_g = solution.eval_info.get('worst_group') if solution.eval_info else None
    if worst_g is not None and worst_g != -1 and worst_g in solution.group_dict:
        return worst_g
        
    return random.choice(all_groups) if all_groups else None
