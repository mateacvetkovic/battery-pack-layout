"""
Fitness iz stvarnih struja (solver) + Pareto fronta: max ćelije, stdev ćelija, max most. Korisnik bira točku na fronti.

Primjer (pack = tvoj BatteryPack):
    from pareto import run_pareto, print_front, plot_front, select, rebuild
    rows, front = run_pareto(pack, iterations=50, seeds=(0, 1, 2))
    print_front(front)
    plot_front(rows, front, limit=3.0, save='pareto.png')
    sol = rebuild(pack, select(front, max_bridge=3.0)[0])   # npr. najmanji max ćelije uz most <= 3
    sol.display()

Fitness (CLONALG ga maksimizira):  -100 * ( lam*(cell_max-1)/3 + (1-lam)*cell_std + w_bridge*max(0, (bridge_max-limit)/limit) )
  lam = 1 -> samo max struja ćelije, lam = 0 -> samo stdev; (cell_max-1)/3 je skaliran da bude usporediv sa stdev
  (za približno normalnu raspodjelu je max - 1 oko 3 sigma). Most se kažnjava samo iznad granice `limit`, izražene u
  nazivnim strujama ćelije (npr. 15 A trake / 5 A po ćeliji = 3). Fronta se ne gradi iz težina, nego iz SVIH rješenja
  koja su se pojavila u svim pokretanjima (arhiva), pa lam služi samo da pokrije različite dijelove fronte.
"""
import contextlib
import pickle
import random

import matplotlib.pyplot as plt
import numpy as np

try:  # u projektu
    from src.kod.BatterySolution import BatterySolution
    from src.kod import IALG
    from src.kod.evaluation import real_metrics
except ImportError:  # samostalno
    from BatterySolution import BatterySolution
    import IALG
    from evaluation import real_metrics

KEYS = ('cell_max', 'cell_std', 'bridge_max')  # sve se minimiziraju


@contextlib.contextmanager
def balance_fitness(archive, lam=0.5, w_bridge=3.0, limit=3.0):
    """Privremeno zamjenjuje calculate_total_fitness fitnessom iz stvarnih struja i sprema svako evaluirano rješenje u archive."""
    original = BatterySolution.calculate_total_fitness

    def fit(self, *args, **kwargs):
        if not self.is_valid():
            self.fitness = -float('inf'); return self.fitness
        groups = sorted(g for g in self.group_dict if g != -1)
        res = []
        for i in range(len(groups) - 1):  # isti odabir mostova kao u tvom fitnessu
            r = self.find_optimal_bridges_and_score(group_id=groups[i], target_group=groups[i + 1], w_mean=1.0, w_var=2.0, w_load=1.5, verbose=False)
            if r is None:
                self.fitness = -float('inf'); return self.fitness
            res.append(r)
        self.bridge_results = res
        self.far_total = 0  # CLONALG faza 2 (kazna za daleke ćelije) se ne pokreće, struje to već vide
        counts = [r['num_bridges'] for r in res]
        self.fitness_details = {'bridge_counts': counts, 'min_bridges': min(counts), 'total_bridges': sum(counts), 'mean_bridges': float(np.mean(counts)),
                                'bridge_variance': float(np.var(counts)), 'mean_bridge_score': float(np.mean([r['bridge_score'] for r in res])), 'fitness': 0}
        m = real_metrics(self)
        archive.setdefault(self.get_fingerprint(), {**m, 'ctg': list(self.cell_to_group)})
        self.fitness = -100 * (lam * (m['cell_max'] - 1) / 3 + (1 - lam) * m['cell_std'] + w_bridge * max(0.0, (m['bridge_max'] - limit) / limit))
        return self.fitness

    BatterySolution.calculate_total_fitness = fit
    try:
        yield
    finally:
        BatterySolution.calculate_total_fitness = original


def pareto_front(rows, keys=KEYS):
    """Nedominirana rješenja (sve ključeve minimiziramo), sortirana po prvom ključu."""
    X = np.array([[r[k] for k in keys] for r in rows])
    keep = [i for i in range(len(X)) if not np.any(np.all(X <= X[i], axis=1) & np.any(X < X[i], axis=1))]
    return sorted((rows[i] for i in keep), key=lambda r: r[keys[0]])


def run_pareto(pack, lams=(0.0, 0.25, 0.5, 0.75, 1.0), w_bridge=3.0, limit=3.0, seeds=(0, 1, 2), iterations=50,
               population_size=20, clones_per_antibody=4, d_new_individuals=6):
    """Za svaki lam vrti CLONALG po seedovima, skuplja sva evaluirana rješenja. Vraća (sva rješenja, fronta)."""
    archive = {}
    for lam in lams:
        with balance_fitness(archive, lam, w_bridge, limit):
            for seed in seeds:
                random.seed(100 + seed); np.random.seed(100 + seed)
                IALG.ClonalgOptimizer(pack, max_iterations=iterations, population_size=population_size,
                                      clones_per_antibody=clones_per_antibody, d_new_individuals=d_new_individuals).run()
        print(f'lam = {lam:g} gotovo, rješenja u arhivi: {len(archive)}', flush=True)
    rows = list(archive.values())
    return rows, pareto_front(rows)


def print_front(front):
    """Ispis fronte: indeks, max ćelije, stdev ćelija, max most (u nazivnim strujama ćelije), R_total."""
    print(f"{'#':>3}{'max ćelije':>12}{'stdev':>9}{'max most':>10}{'R_total':>9}")
    for i, r in enumerate(front):
        print(f"{i:>3}{r['cell_max']:>12.3f}{r['cell_std']:>9.4f}{r['bridge_max']:>10.2f}{r['R_total']:>9.4f}")


def select(front, max_cell=None, max_std=None, max_bridge=None, by='cell_max'):
    """Rješenja s fronte koja zadovoljavaju zadane granice, sortirana po `by` (najbolje prvo). Prazna lista ako nijedno ne zadovoljava."""
    ok = [r for r in front if (max_cell is None or r['cell_max'] <= max_cell) and (max_std is None or r['cell_std'] <= max_std)
          and (max_bridge is None or r['bridge_max'] <= max_bridge)]
    return sorted(ok, key=lambda r: r[by])


def plot_front(rows, front, limit=None, save=None, show=True):
    """Lijevo: max ćelije naspram max mosta (boja = stdev); desno: max ćelije naspram stdev. Siva = sva rješenja, crveno = fronta."""
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    ax[0].scatter([r['bridge_max'] for r in rows], [r['cell_max'] for r in rows], c='lightgrey', s=8)
    sc = ax[0].scatter([r['bridge_max'] for r in front], [r['cell_max'] for r in front], c=[r['cell_std'] for r in front], cmap='viridis_r', s=40, edgecolor='red')
    if limit is not None:
        ax[0].axvline(limit, color='k', linestyle='--', label=f'granica trake {limit:g}'); ax[0].legend()
    ax[0].set_xlabel('max struja mosta / nazivna struja ćelije'); ax[0].set_ylabel('max struja ćelije / nazivna')
    fig.colorbar(sc, ax=ax[0], label='stdev struja ćelija')
    ax[1].scatter([r['cell_std'] for r in rows], [r['cell_max'] for r in rows], c='lightgrey', s=8)
    ax[1].scatter([r['cell_std'] for r in front], [r['cell_max'] for r in front], c='red', s=30)
    ax[1].set_xlabel('stdev struja ćelija'); ax[1].set_ylabel('max struja ćelije / nazivna')
    fig.suptitle('Pareto fronta (minimiziramo sve tri veličine)')
    fig.tight_layout()
    if save:
        fig.savefig(save, bbox_inches='tight')
    if show:
        plt.show()


def rebuild(pack, row):
    """Ponovo gradi BatterySolution iz retka fronte (row['ctg']); fitness je izračunat originalnom funkcijom."""
    sol = BatterySolution(pack)
    for c, g in enumerate(row['ctg']):
        if g >= 0:
            sol.assign_cell_to_group(c, g)
    sol.calculate_total_fitness()
    return sol


def save_front(path, rows, front):
    with open(path, 'wb') as f:
        pickle.dump({'rows': rows, 'front': front}, f)