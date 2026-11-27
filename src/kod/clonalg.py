import random
from kod.heuristics import skewed_sweep, check_simple_solution, snake_pattern_rows, snake_pattern_bottom_up, snake_pattern_columns, max_shared_boundary_distance_based_universal_smart
import time
from kod.mutations import mutate_swap_boundary, mutate_cyclic_3way_swap, mutate_steal_and_shift
import numpy as np

def remove_duplicates(population):
    """
    Uklanja duplikate iz populacije na temelju otiska prsta (fingerprint) rjesenja.

    Argumenti:
        population (list): lista rjesenja koja se filtrira.

    Vraca:
        list: lista jedinstvenih rjesenja bez duplikata.
    """
    unique_population = []
    seen_fingerprints = set()
    
    for sol in population:
        fp = sol.get_fingerprint()
        if fp not in seen_fingerprints:
            seen_fingerprints.add(fp)
            unique_population.append(sol)
            
    return unique_population


def generate_initial_population(pack, population_size=10, snakes=True):
    """
    kreira raznoliku pocetnu populaciju bez duplikata generirajuci nova rjesenja
    sve dok se ne popuni zeljeni broj jedinki ili ne potrosi maksimalan broj pokusaja.

    Argumenti:
        pack (object): objekt koji definira problem pakiranja.
        population_size (int): zeljena velicina populacije.
        snakes (bool): zastavica koja odredjuje hoce li se koristiti zmijoliki uzorci.

    Vraca:
        list: sortirana lista pocetnih rjesenja po fitnessu.
    """
    population = []
    seen_fingerprints = set() 
    
    def try_add_solution(sol):
        """
        pomocna funkcija za validaciju, izracun fitnessa i dodavanje rjesenja u skup.

        Argumenti:
            sol (object): rjesenje koje se pokusava dodati.

        Vraca:
            bool: true ako je rjesenje uspjesno dodano, inace false.
        """
        if sol and sol.is_valid():
            fp = sol.get_fingerprint()
            if fp not in seen_fingerprints:
                seen_fingerprints.add(fp)
                sol.calculate_total_fitness()
                population.append(sol)
                return True
        return False

    if pack.type == 'rectangle':
        sol = check_simple_solution(pack)
        try_add_solution(sol)

    snake_generators = [
        lambda p: snake_pattern_rows(p),
        lambda p: snake_pattern_bottom_up(p),
        lambda p: snake_pattern_columns(p)
    ]

    if snakes == True:
        for gen_func in snake_generators:
            sol = gen_func(pack)
            try_add_solution(sol)

    strategies = ["horizontal", "vertical", "diagonal"]
    for _ in range(population_size * 3):
        sol = skewed_sweep(pack, axis=random.choice(["x", "y"]), reverse=random.choice([False, True]),
                           amp=random.choice([0.5, 1.0, 1.5, 2.0]), noise=random.choice([0.0, 0.3]))
        try_add_solution(sol)
    directions = {
        "horizontal": ["top-down", "bottom-up"],
        "vertical": ["left-to-right", "right-to-left"],
        "diagonal": ["top-down", "bottom-up"]
    }
    diagonal_types = ["backslash", "slash"]

    temperatures = [0, 15, 25]            
    p_stochastics = [0.0, 0.2, 0.5]     

    attempts = 0
    max_attempts = population_size * 40  
    
    while len(population) < population_size * 4 and attempts < max_attempts:
        attempts += 1
        
        strat = random.choice(strategies)
        dir = random.choice(directions[strat])
        temp = random.choice(temperatures)
        p_stoch = random.choice(p_stochastics)
        diag_type = random.choice(diagonal_types)

        if strat == 'diagonal':
            rev_cols = random.choice([True, False]) 
        else:
            rev_cols = False

        sol = max_shared_boundary_distance_based_universal_smart(pack, strategy=strat, direction=dir, diagonal_type=diag_type, reverse_columns=rev_cols, p_stochastic=p_stoch, temperature=temp)
        
        try_add_solution(sol)

    population.sort(key=lambda s: s.fitness, reverse=True)
    
    if len(population) >= population_size:
        return population[:population_size]
    else:
        return population


class ClonalgOptimizer:
    """
    Razred koji implementira imunoloski algoritam clonalg za optimizaciju rjesenja pakiranja.

    """
    def __init__(self, pack, max_iterations=50, population_size=50, clones_per_antibody=5, d_new_individuals=12, beta=10, stag_iter=100, max_extra_mutations=3, elite_ratio=0.8):
        """
        Argumenti:
        pack (object): objekt koji opisuje mrežu
        max_iterations (int): maksimalni broj iteracija optimizacije.
        population_size (int): ciljana velicina populacije.
        clones_per_antibody (int): bazni broj klonova po antitijelu.
        d_new_individuals (int): broj novih jedinki koje se unose u svaku populaciju.
        beta (int): faktor za skaliranje broja klonova u ovisnosti o rangu.
        """
        self.pack = pack
        self.max_iterations = max_iterations
        self.population_size = population_size
        self.clones_per_antibody = clones_per_antibody
        self.d_new_individuals = d_new_individuals
        self.beta = beta
        self.stag_iter=stag_iter
        
        self.start_population = []
        self.best_ever_solution = None
        self.best_ever_fitness = -float('inf')
        self.history = []
        self.mutation_stats_history = []
        self.final_population=[]
        self.max_extra_mutations = max_extra_mutations
        self.elite_ratio = elite_ratio

        self.avg_fitness = []

    def run(self, w_far=2.0, phase2_fraction=0.5):
        # faza 1 = dosadasnji algoritam bez kazne za daleke celije
        best = self._run_phase()
        if not best or w_far <= 0:
            return best
        best[0].calculate_total_fitness()
        if best[0].far_total == 0:
            return best  # nema dalekih celija, faza 2 se ne pokrece
        # faza 2: ista populacija, ali s kaznom za daleke celije (2+ koraka)
        print(f"[CLONALG] rjesenje ima daleke celije ({best[0].far_total}); faza 2 s w_far={w_far}")
        sol_cls = type(best[0])
        sol_cls.W_FAR = w_far
        try:
            population = [ind.copy() for ind in self.final_population]
            for ind in population:
                ind.calculate_total_fitness()
            self.best_ever_fitness = -float('inf')
            self.best_ever_solution = None
            iters = self.max_iterations
            self.max_iterations = max(1, int(iters * phase2_fraction))
            best = self._run_phase(population)
            self.max_iterations = iters
        finally:
            sol_cls.W_FAR = 0.0
        return best    
    def _run_phase(self,  population=None):
        """
        pokrece glavnu petlju algoritma s evolucijskim operacijama.

        Vraca:
            object: najbolje pronadjeno rjesenje (jedinka) tijekom izvodjenja.
        """
        # population = generate_initial_population(self.pack, self.population_size, snakes=True)
        # self.start_population = [ind.copy() for ind in population]
        # stag = 0
        if population is None:
            population = generate_initial_population(self.pack, self.population_size, snakes=True)
            self.start_population = [ind.copy() for ind in population]
        stag = 0
        
        mutation_stats = {
            'swap_boundary': {'tried': 0, 'improved': 0},
            'cyclic': {'tried': 0, 'improved': 0},
            'steal': {'tried': 0, 'improved': 0}
        }

        for t in range(self.max_iterations):
            
            population.sort(key=lambda s: s.fitness, reverse=True)
            
            current_best = population[0]
            if current_best.fitness > self.best_ever_fitness:
                stag = 0
                self.best_ever_fitness = current_best.fitness
                self.best_ever_solution = current_best.copy()
            else:
                stag += 1
                if stag > self.stag_iter:
                    print(f"[CLONALG] rani prekid u iteraciji {t+1} zbog stagnacije.")
                    break
                    
            if current_best.eval_info['total_bridges'] == (self.pack.no_groups - 1) * self.pack.no_cells_per_group:
                return [current_best]

            clonal_pool = []
            # odabir broja klonova u ovisnosti o kvaliteti rjesenja - bolja rjesenja, vise klonova
            for i, antibody in enumerate(population):
                affinity_rank_factor = (len(population) - i) / len(population)
                
                num_clones = int(self.beta * affinity_rank_factor)
                num_clones = max(1, num_clones)

                for _ in range(num_clones):
                    clone = antibody.copy() 
                    clonal_pool.append((i, clone))
                    
            mutated_pool = []
            n_pop = len(population)

            valid_fitnesses = [s.fitness for s in population if s.fitness != -float('inf')]

            if valid_fitnesses:
                self.avg_fitness.append(sum(valid_fitnesses) / len(valid_fitnesses))
            else:
                self.avg_fitness.append(0)
                        
            for rank, (parent_rank, clone) in enumerate(clonal_pool):

                parent_fitness = population[parent_rank].fitness                
                rank_ratio = parent_rank / (n_pop - 1) if n_pop > 1 else 0.0

                # bolji rade 1 mutaciju, losiji mogu odraditi vise njih u nizu (npr. do 4)
                #num_mutations = 1 + int(3 * rank_ratio)
                num_mutations = 1 + int(self.max_extra_mutations * rank_ratio)

                for _ in range(num_mutations):
                    r = random.random()
                    if r < 0.5:
                        mut_type = 'swap_boundary'
                        mutate_swap_boundary(clone)
                    elif r < 0.75:
                        mut_type = 'cyclic'
                        mutate_cyclic_3way_swap(clone)
                    else:
                        mut_type = 'steal'
                        mutate_steal_and_shift(clone)
                
                    mutation_stats[mut_type]['tried'] += 1
                
                clone.calculate_total_fitness()
                
                if clone.fitness > parent_fitness:
                    mutation_stats[mut_type]['improved'] += 1
                    
                mutated_pool.append(clone)
            #combined_pool = population + mutated_pool
            num_elite = 5
            next_population = [ind.copy() for ind in population[:num_elite]]
        
            unique_mutants = []
            seen_fps = {ind.get_fingerprint() for ind in next_population}

            for ind in mutated_pool:
                if ind:
                    fp = ind.get_fingerprint()
                    if fp not in seen_fps:
                        seen_fps.add(fp)
                        unique_mutants.append(ind)
                        
            unique_mutants.sort(key=lambda s: s.fitness, reverse=True)
            
            target_size_without_new = self.population_size - self.d_new_individuals
            slots_for_mutants = target_size_without_new - len(next_population)
            if slots_for_mutants > 0:
                # next_population.extend(unique_mutants[:slots_for_mutants])
                #chosen_mutants = roulette_wheel_selection(unique_mutants, slots_for_mutants)

                #chosen_mutants = hybrid_elitist_random_selection(unique_mutants, slots_for_mutants)
                chosen_mutants = hybrid_elitist_random_selection(unique_mutants, slots_for_mutants, elite_ratio=self.elite_ratio)
                next_population.extend(chosen_mutants)

            needed_new = self.d_new_individuals
            if needed_new > 0:
                new_bloods = generate_initial_population(self.pack, population_size=needed_new, snakes=False)
                for nb in new_bloods:
                    if nb:
                        next_population.append(nb)
                        
            while len(next_population) < self.population_size and population:
                next_population.append(population[0].copy())
                
            population = next_population
            valid_fitnesses = [s.fitness for s in population if s.fitness != -float('inf')]

            if valid_fitnesses:
                self.avg_fitness.append(sum(valid_fitnesses) / len(valid_fitnesses))
            else:
                self.avg_fitness.append(0)
            self.mutation_stats_history.append({
                'iteration': t + 1,
                'stats': {k: v.copy() for k, v in mutation_stats.items()}
            })
            ctg = np.array([ind.cell_to_group for ind in population])
            usable = [c for c in range(ctg.shape[1]) if c not in self.pack.bms_cell_ids]
            ctg = ctg[:, usable]
            diff = (ctg[:, None, :] != ctg[None, :, :]).mean(axis=2)
            diversity = float(diff[np.triu_indices(len(ctg), 1)].mean()) if len(ctg) > 1 else 0.0

            self.history.append({
                'iteration': t + 1,
                'best_population_fitness': self.best_ever_fitness,
                'time': time.time(),
                'fitness_std': float(np.std(valid_fitnesses)) if valid_fitnesses else 0.0,
                'diversity': diversity,
                'fitnesses': list(valid_fitnesses),
            })
            if t % 10 == 0:
                print(f"iteracija {t+1}/{self.max_iterations} | najbolji fitness u populaciji: {self.best_ever_fitness:.2f}")
            # print("   -> Uspješnost mutacija:")
            # for m_name, stats in mutation_stats.items():
            #     tried = stats['tried']
            #     improved = stats['improved']
            #     rate = (improved / tried * 100) if tried > 0 else 0
            #     print(f"      {m_name}: {improved}/{tried} ({rate:.1f}%)")
        self.final_population = [ind.copy() for ind in population]

        best_solutions = [ind.copy() for ind in self.final_population if abs(ind.fitness - self.best_ever_fitness) < 1e-9]
        
        if not best_solutions and self.best_ever_solution is not None:
            best_solutions = [self.best_ever_solution]
            
        return best_solutions


def hybrid_elitist_random_selection(mutants, num_to_select, elite_ratio=0.8):
    """
    bira 'num_to_select' jedinki iz liste mutanata kombinirajuci elitizam i nasumicni odabir.

    Argumenti:
        mutants (list): lista kandidata mutanata.
        num_to_select (int): ukupan broj jedinki koje je potrebno odabrati.
        elite_ratio (float): udio najboljih jedinki koje se obavezno zadrzavaju.

    Vraca:
        list: odabrane jedinke kombinacijom elitizma i nasumicnog izbora.
    """
    if not mutants or num_to_select <= 0:
        return []
        
    if len(mutants) <= num_to_select:
        return list(mutants)

    sorted_mutants = sorted(mutants, key=lambda s: s.fitness, reverse=True)
    
    num_elite = int(num_to_select * elite_ratio)
    num_random = num_to_select - num_elite
    
    if num_elite == 0 and num_to_select > 0:
        num_elite = 1
        num_random = num_to_select - 1

    chosen_mutants = sorted_mutants[:num_elite]
    
    remainder = sorted_mutants[num_elite:]
    
    if remainder and num_random > 0:
        if len(remainder) <= num_random:
            chosen_mutants.extend(remainder)
        else:
            chosen_mutants.extend(random.sample(remainder, num_random))
            
    while len(chosen_mutants) < num_to_select and remainder:
        for m in remainder:
            if m not in chosen_mutants:
                chosen_mutants.append(m)
                break
        else:
            break

    return chosen_mutants

from contextlib import contextmanager


@contextmanager
def fitness_weights(**weights):
    """Privremeno mijenja zadane težine u BatterySolution.calculate_total_fitness, po IMENU (npr. w_split=1000).
    Nepoznato ime je greška, pa se promjena potpisa funkcije ne može tiho izgubiti."""
    import inspect
    from kod.BatterySolution import BatterySolution
    fn = BatterySolution.calculate_total_fitness
    params = [p for p in inspect.signature(fn).parameters.values() if p.default is not inspect.Parameter.empty]
    unknown = set(weights) - {p.name for p in params}
    if unknown:
        raise TypeError(f'calculate_total_fitness nema težine {sorted(unknown)}')
    old = fn.__defaults__
    fn.__defaults__ = tuple(weights.get(p.name, p.default) for p in params)
    try:
        yield
    finally:
        fn.__defaults__ = old
