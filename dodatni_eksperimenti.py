"""
Dva dodatna eksperimenta za rezultate.

1) resistance_sweep: spremljena rjesenja (.pkl) ponovno racuna solverom za stvarne kombinacije
   niklove trake (0.3 i 0.15 mm) i otpora celije (30 i 50 mOhm). Optimizacija se NE ponavlja.
2) convergence: za odabrane pakete pokrece CLONALG, biljezi tijek najboljeg fitnessa
   po iteracijama i vrijeme izvodjenja.

Pokretanje iz korijena projekta, npr.:
    from dodatni_eksperimenti import resistance_sweep, convergence
    resistance_sweep('rjesenja_baseline/novo', 'otpor.csv')
    convergence('rjesenja/paketi.json', ['trokut_2', 'trokut_3'], 'konvergencija.csv')
"""
import csv
import glob
import os
import pickle
import time
import pandas as pd
import matplotlib.pyplot as plt

from src.kod import IALG
from src.kod.evaluation import real_metrics, load_packs

RHO_NI = 6.99e-5   # otpornost nikla u ohm*mm (6.99e-8 ohm*m), ista kao za R_PER_LENGTH u evaluation.py
STRIP_WIDTH = 7    # mm
# stvarne kombinacije: (debljina trake u mm, otpor celije u ohmima)
SCENARIOS = [(0.3, 0.05), (0.3, 0.03), (0.15, 0.05), (0.15, 0.03)]
OPT = dict(max_iterations=500, population_size=50, stag_iter=50)  # iste postavke kao u rezultatima


def resistance_sweep(folder, csv_path, scenarios=SCENARIOS):
    """Za svaki .pkl u folderu (i podfolderima) i svaku kombinaciju trake i celije racuna stvarne mjere
    uz sve izgradjene mostove. Optimizacija se ne ponavlja."""
    rows = []
    for path in sorted(glob.glob(os.path.join(folder, '**', '*.pkl'), recursive=True)):
        with open(path, 'rb') as f:
            sol = pickle.load(f)['solution']
        sol.calculate_total_fitness()
        for thickness, r_cell in scenarios:
            r_per_length = RHO_NI / (thickness * STRIP_WIDTH)   # ohm po mm
            m = real_metrics(sol, r_cell=r_cell, r_per_length=r_per_length, selected=False)
            rows.append({'file': os.path.basename(path)[:-4], 'strip_mm': thickness, 'r_cell': r_cell,
                         'ratio': r_per_length * sol.pack.d / r_cell,   # otpor segmenta / R_cell
                         'cell_overcurrent_pct': (m['cell_max'] - 1) * 100, 'cell_std': m['cell_std'],
                         'segment_max': m['bridge_max'], 'R_total': m['R_total']})
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


CONV_OPT = dict(max_iterations=500, population_size=50, stag_iter=100)  # dulja stagnacija da se vide zastoji


def convergence(json_path, names, csv_path, runs=3, opt_kwargs=CONV_OPT):
    """Pokrece CLONALG `runs` puta po paketu, samo prvu fazu (w_far=0, fitness je cijelo vrijeme na istoj skali).
    Sprema najbolji i prosjecni fitness populacije po iteraciji, broj iteracija i vrijeme."""
    packs = {p['name']: p['pack'] for p in load_packs(json_path)}
    rows = []
    for name in names:
        for run in range(runs):
            opt = IALG.ClonalgOptimizer(packs[name], **opt_kwargs)
            t0 = time.time()
            best = opt.run(w_far=0)   # bez druge faze
            seconds = time.time() - t0
            # history je prazan ako je idealan broj mostova nadjen vec u prvoj iteraciji
            history = opt.history or [{'iteration': 0, 'best_population_fitness': best[0].fitness}]
            # avg_fitness se dopunjuje dvaput po iteraciji; drugi zapis je prosjek nove populacije
            means = opt.avg_fitness[1::2] or [float('nan')]
            for i, h in enumerate(history):
                rows.append({'pack': name, 'run': run, 'iteration': h['iteration'],
                             'best_fitness': h['best_population_fitness'],
                             'mean_fitness': means[min(i, len(means) - 1)],
                             'iterations_total': len(opt.history), 'time_s': round(seconds, 1),
                             'fitness_std': h.get('fitness_std'),
                             'diversity': h.get('diversity'),})
            print(f'{name} run {run}: {len(opt.history)} iteracija, {seconds:.0f} s')
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows



def plot_convergence():
    d = pd.read_csv('konvergencija_tri4.csv')  
    d2 = pd.read_csv('konvergencija_tri6.csv') 
    d= pd.concat([d,d2])
    packs = [('trokut_5','Triangle 4'), ('pravokutni_trokut_B', 'Triangle 6')]
    colors = ['#2a78d6', '#eb6834', '#1baf7a']

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.4))
    for ax, (name, label) in zip(axes, packs):
        for run, x in d[d.pack == name].groupby('run'):
            c = colors[run]
            ax.plot(x.iteration, x.mean_fitness, color=c, lw=1.5, drawstyle='steps-post')
        ax.set_title(label, fontsize=9)
        ax.set_xlabel('Iteration', fontsize=8)
        ax.set_xlim(0, d[d.pack == name].iteration.max())
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3, lw=0.5)
    axes[0].set_ylabel('Average population fitness', fontsize=8)

    handles = [plt.Line2D([], [], color=c, lw=1.5) for c in colors]
    fig.legend(handles, ['Run 1', 'Run 2', 'Run 3'],
            loc='upper center', ncol=5, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig('slike/convergence_tri4.pdf')

from src.kod.bridges import all_bridges, solve
from src.kod.evaluation import R_CELL, R_PER_LENGTH
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Circle, Patch
from matplotlib.lines import Line2D

NORM = Normalize(vmin=1, vmax=2)
CMAP = plt.get_cmap('plasma_r')


def _solve(sol):
    pack, ctg = sol.pack, sol.cell_to_group
    bridges = all_bridges(pack, ctg)
    res = solve(ctg, bridges, R_CELL, R_PER_LENGTH, pack.no_cells_per_group)
    return bridges, res


def draw_hot_cells(ax, sol, res, cell_threshold=1.03):
    """Crveni prsten oko celija cija struja prelazi nazivnu za vise od (cell_threshold - 1)."""
    cells, nom = sol.pack.grid.cells, res['nominal_current']
    for c, I in res['cell_currents'].items():
        if I / nom >= cell_threshold:
            ax.add_patch(Circle((cells[c].x, cells[c].y), sol.pack.cell_d / 2, fill=False, edgecolor='red', lw=2.5, zorder=11))


from matplotlib.colors import LogNorm
from matplotlib.ticker import FixedLocator, FixedFormatter

SEG_NORM = LogNorm(vmin=1, vmax=6)
SEG_CMAP = plt.get_cmap('plasma_r')
SEG_TICKS = [1, 1.5, 2, 3, 4, 6]


def draw_layout_currents(ax, sol, n_segments=4, cell_threshold=1.03):
    """Najopterecenije celije + n_segments segmenata s najvecom strujom, obojanih po struji. Vraca te struje."""
    bridges, res = _solve(sol)
    cells, nom = sol.pack.grid.cells, res['nominal_current']
    seg = sorted(((res['bridge_currents'][i] / nom, b) for i, b in enumerate(bridges) if i not in res['shorted_bridges']),
                 key=lambda t: t[0], reverse=True)[:n_segments]
    for v, b in reversed(seg):  # najjaci se crta zadnji, preko ostalih
        c1, c2 = cells[b['a'][0]], cells[b['b'][0]]
        ax.plot([c1.x, c2.x], [c1.y, c2.y], color='black', lw=6, solid_capstyle='round', zorder=12)
        ax.plot([c1.x, c2.x], [c1.y, c2.y], color=SEG_CMAP(SEG_NORM(max(v, 1))), lw=4, solid_capstyle='round', zorder=13)
    draw_hot_cells(ax, sol, res, cell_threshold)
    return [v for v, _ in seg]


def save_colorbar(path='slike/colorbar.pdf'):
    """Zajednicka (logaritamska) skala struje segmenta za sva tri panela."""
    fig = plt.figure(figsize=(3.5, 0.6))
    cax = fig.add_axes([0.05, 0.55, 0.9, 0.2])
    fig.colorbar(ScalarMappable(SEG_NORM, SEG_CMAP), cax=cax, orientation='horizontal')
    cax.xaxis.set_major_locator(FixedLocator(SEG_TICKS))
    cax.xaxis.set_major_formatter(FixedFormatter([str(t) for t in SEG_TICKS]))
    cax.xaxis.set_minor_locator(FixedLocator([]))
    cax.set_xlabel('Segment current / nominal cell current', fontsize=7)
    cax.tick_params(labelsize=7)
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)


def save_legend(no_groups, n_segments=1, path='slike/legend.pdf', ncol=8):
    """Jedna legenda za sve panele; boje grupa iste kao u plotGroups."""
    cmap = plt.get_cmap('nipy_spectral')
    handles = [Patch(facecolor=cmap(0.08 + 0.8 * g / max(1, no_groups - 1)), edgecolor='black', alpha=0.6, label=f'G{g}')
               for g in range(no_groups)]
    handles += [Patch(facecolor='black', edgecolor='black', alpha=0.6, label='BMS'),
                Patch(facecolor='grey', edgecolor='black', alpha=0.6, label='Unused'),
                Line2D([], [], marker='o', ls='', markerfacecolor='none', markeredgecolor='red',
                       markeredgewidth=2, markersize=9, label='Cell current > 1.03'),
                Line2D([], [], color=SEG_CMAP(0.5), lw=4, path_effects=[], label=f'{n_segments} highest segment currents')]
    fig = plt.figure(figsize=(7, 0.6))
    fig.legend(handles=handles, loc='center', ncol=ncol, fontsize=7, frameon=False)
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)


def segment_face(b, ctg):
    """Strana paketa na kojoj je segment: n-strana parne i p-strana neparne grupe su na istoj strani."""
    c, side = b['a']
    return 'A' if (side == 'n') == (ctg[c] % 2 == 0) else 'B'


def draw_all_segment_currents(ax, sol, face, seg_threshold=1.0, cell_threshold=1.03):
    """Stara verzija: svi segmenti na strani `face` ('A' ili 'B') iznad praga, boja i debljina po struji."""
    bridges, res = _solve(sol)
    ctg, cells, nom = sol.cell_to_group, sol.pack.grid.cells, res['nominal_current']
    segs, vals = [], []
    for i, b in enumerate(bridges):
        if i in res['shorted_bridges'] or segment_face(b, ctg) != face:
            continue
        v = res['bridge_currents'][i] / nom
        if v < seg_threshold:
            continue
        c1, c2 = cells[b['a'][0]], cells[b['b'][0]]
        segs.append([(c1.x, c1.y), (c2.x, c2.y)])
        vals.append(v)
    lw = [0.5 + 2.5 * min(v, NORM.vmax) / NORM.vmax for v in vals]
    ax.add_collection(LineCollection(segs, colors=CMAP(NORM(vals)), linewidths=lw, capstyle='round', zorder=10))
    draw_hot_cells(ax, sol, res, cell_threshold)

def timing(json_path, names, csv_path, runs=3):
    """Vrijeme CLONALG-a s postavkama iz glavnih rezultata (OPT, obje faze).
    Vrijeme do najboljeg = zadnje poboljsanje u fazi iz koje je konacno rjesenje."""
    packs = {p['name']: p['pack'] for p in load_packs(json_path)}
    rows = []
    for name in names:
        for run in range(runs):
            opt = IALG.ClonalgOptimizer(packs[name], **OPT)
            t0 = time.time()
            opt.run()
            total = time.time() - t0
            h = opt.history
            # podjela na faze: brojac iteracija krece ispocetka u drugoj fazi
            start = max([i for i in range(len(h)) if h[i]['iteration'] == 1] or [0])
            phases = [h[:start], h[start:]] if start > 0 else [h]
            k_best = 0
            for ph_start, ph in ((0, phases[0]), (start, phases[-1])) if len(phases) == 2 else ((0, h),):
                for i in range(1, len(ph)):
                    if ph[i]['best_population_fitness'] > ph[i - 1]['best_population_fitness'] + 1e-9:
                        k_best = ph_start + i
            rows.append({'pack': name, 'run': run, 'S': packs[name].no_groups, 'P': packs[name].no_cells_per_group,
                         'iterations_to_best': k_best + 1 if h else 0, 'iterations_total': len(h),
                         'time_to_best_s': round(h[k_best]['time'] - t0, 1) if h else 0.0,
                         'time_total_s': round(total, 1), 'phase2': len(phases) == 2})
            print(rows[-1])
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows

VARIANTS = {
    'base':    {},
    'new0':    dict(d_new_individuals=0),
    'new25':   dict(d_new_individuals=25),
    'mut6':    dict(max_extra_mutations=6),
    'elite05': dict(elite_ratio=0.5),
    'pop100':  dict(population_size=100),
}


def param_study(json_path, names, csv_path, runs=5, iterations=150, variants=VARIANTS):
    """Jedan parametar odjednom; bez stagnacije, samo prva faza, isti broj iteracija za sve."""
    packs = {p['name']: p['pack'] for p in load_packs(json_path)}
    rows = []
    for name in names:
        for var, kw in variants.items():
            for run in range(runs):
                params = dict(max_iterations=iterations, population_size=50, stag_iter=iterations + 1)
                params.update(kw)
                opt = IALG.ClonalgOptimizer(packs[name], **params)
                t0 = time.time()
                best = opt.run(w_far=0)
                total = time.time() - t0
                h = opt.history
                last = max([i for i in range(1, len(h)) if h[i]['best_population_fitness'] > h[i - 1]['best_population_fitness'] + 1e-9] or [0])
                sol = best[0]
                m = real_metrics(sol, selected=False)
                rows.append({'pack': name, 'variant': var, 'run': run, 'fitness': sol.fitness,
                             'iteration_last_improvement': last + 1, 'time_s': round(total, 1),
                             'cell_overcurrent_pct': (m['cell_max'] - 1) * 100, 'segment_max': m['bridge_max']})
                print(rows[-1])
                with open(csv_path, 'w', newline='') as f:   # sprema nakon svakog pokretanja, da ne izgubis sve ako prekine
                    w = csv.DictWriter(f, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
    return rows
    import numpy as np

def population_snapshot(json_path, name, csv_path):
    """Jedno pokretanje (samo prva faza); sprema fitness pocetne i konacne populacije
    i broj razlicitih rasporeda medju jedinkama blizu najboljeg rjesenja."""
    pack = {p['name']: p['pack'] for p in load_packs(json_path)}[name]
    opt = IALG.ClonalgOptimizer(pack, **CONV_OPT)
    opt.run(w_far=0)
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    for h in opt.history:
        ax.scatter([h['iteration']] * len(h['fitnesses']), h['fitnesses'], s=2, color='#2a78d6', alpha=0.15, lw=0)
    ax.plot([h['iteration'] for h in opt.history], [h['best_population_fitness'] for h in opt.history], color='black', lw=1.2)
    fig.savefig('slike/population2.pdf')
    rows = [{'population': 'initial', 'fitness': s.fitness} for s in opt.start_population] + \
           [{'population': 'final', 'fitness': s.fitness} for s in opt.final_population]
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['population', 'fitness'])
        w.writeheader()
        w.writerows(rows)
    best = max(s.fitness for s in opt.final_population)
    top = [s for s in opt.final_population if s.fitness >= best - 1]
    distinct = len({tuple(s.cell_to_group) for s in top})
    print(f'{name}: {len(top)} jedinki unutar 1 od najboljeg, od toga {distinct} razlicitih rasporeda')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
if __name__ == '__main__':

    #convergence('rjesenja/svipaketi.json', ['trokut_5'], 'konvergencija_tri4.csv')                   # Triangle 4
    #convergence('rjesenja/svipaketi.json', ['pravokutnik_diplomski'], 'konvergencija_pravokutnikdipl.csv')   # Triangle 6
    # N_SEG = 4
    # for fname, out in [('trokut_4_snake_1_red', 'snake'), ('trokut_4_početna_heuristika_run0', 'init'),
    #                    ('trokut_4_CLONALG_w_split=0_run0', 'clonalg')]:
    #     with open(f'rjesenja_baseline/novo/trokut_4/{fname}.pkl', 'rb') as f:
    #         sol = pickle.load(f)['solution']
    #     sol.display(save=False, show=False)
    #     ax = plt.gca()
    #     ax.get_legend().remove()  # legenda grupa ide u zasebnu sliku
    #     vals = draw_layout_currents(ax, sol, n_segments=N_SEG)
    #     print(out, 'najjaci segmenti:', [round(v, 2) for v in vals])
    #     plt.savefig(f'slike/trokut4_{out}.pdf', bbox_inches='tight')
    #     plt.close('all')
    # save_legend(sol.pack.no_groups, N_SEG)
    # save_colorbar()
        # stara verzija, sve struje po stranama:
        # for face in 'AB':
        #     sol.display(save=False, show=False)
        #     draw_all_segment_currents(plt.gca(), sol, face)
        #     plt.savefig(f'slike/trokut4_{out}_{face}.pdf', bbox_inches='tight')
        #     plt.close('all')
    # save_colorbar()
    # plot_convergence()
    #timing('rjesenja/svipaketi.json', ['pravokutnik_2', 'trokut_2', 'trokut_3', 'trokut_4'], 'vrijeme_hex.csv')
    #timing('rjesenja/svipaketi.json', ['pravokutni_trokut_B', 'pravokutni_pravokutnik_A'], 'vrijeme_orth.csv')
    #timing('rjesenja/svipaketi.json', ['trokut_21700'], 'vrijeme_21700.csv')
    #param_study('rjesenja/svipaketi.json', ['pravokutni_trokut_B'], 'parametri_tri6.csv', runs=1, iterations=5)
    # param_study('rjesenja/svipaketi.json', ['trokut_3'], 'parametri_tri2.csv') 

    population_snapshot('rjesenja/svipaketi.json', 'pravokutnik_1', 'populacija_rect1.csv')   # Triangle 6    d = pd.read_csv('populacija_tri6.csv')
    #d = pd.read_csv('populacija_tri4.csv')


    # rng = np.random.default_rng(0)
    # fig, ax = plt.subplots(figsize=(3.5, 1.6))
    # for k, (pop, color) in enumerate([('initial', '#9ec5ee'), ('final', '#2a78d6')]):
    #     f = d[d.population == pop].fitness.values
    #     ax.scatter(f, k + rng.uniform(-0.18, 0.18, len(f)), s=12, color=color, edgecolor='black', lw=0.3, zorder=3)
    # ax.axvline(d.fitness.max(), color='0.4', lw=0.8, ls='--', zorder=1)
    # ax.set_yticks([0, 1])
    # ax.set_yticklabels(['Initial', 'Final'], fontsize=8)
    # ax.set_ylim(-0.5, 1.5)
    # ax.set_xlabel('Fitness', fontsize=8)
    # ax.tick_params(labelsize=7)
    # ax.grid(axis='x', alpha=0.3, lw=0.5)
    # fig.tight_layout()
    # fig.savefig('slike/population.pdf')
    # plot_convergence()
    