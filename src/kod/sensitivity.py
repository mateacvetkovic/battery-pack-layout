"""
Analiza osjetljivosti težina funkcije dobrote, na paketima iz paketi.json.
Pokreće se iz korijena projekta (tamo gdje je mapa src/): python sensitivity.py
Jedna težina se množi faktorom, ostale ostaju osnovne; CLONALG se vrti s istim seedovima za sve varijante.
Mjere kojima se varijante uspoređuju (struje sa svim mostovima) ne ovise o težinama, pa usporedba nije kružna.
"""
import csv
import random
import time

from src.kod.BatterySolution import BatterySolution
from src.kod.IALG import ClonalgOptimizer
from src.kod.evaluation import load_packs, real_metrics

PACKS_JSON = "rjesenja/paketi.json"
PACKS = ["pravokutnik_1", "trokut_5"]  # imena iz paketi.json; svaki paket x varijante x ponavljanja = jedno CLONALG pokretanje
BASE = {"w_score": 2.0, "w_min_bridges": 5.0, "w_total_bridges": 1.0, "w_bridge_balance": 2.0}  # = defaulti u calculate_total_fitness
W_FAR_BASE = 2.0           # = default u ClonalgOptimizer.run
W_FAR_VALUES = [0.0, 5.0]  # uz osnovnu vrijednost; w_far je jedina težina vezana uz ćelije koje su daleko od mosta
FACTORS = [0.5, 2.0]
REPEATS = 3
OPTIMIZER_KWARGS = {"max_iterations": 200, "population_size": 50, "stag_iter": 50}  # main.py koristi 500; vidi trajanje prije povećanja
OUT_CSV = "sensitivity_results.csv"
METRICS = ["cell_max", "cell_std", "cell_p95", "cells_over", "bridge_max", "junction_max"]


def set_fitness_weights(w):
    """Mijenja zadane vrijednosti argumenata calculate_total_fitness bez diranja izvornog koda."""
    d = list(BatterySolution.calculate_total_fitness.__defaults__)  # w_score, w_min_bridges, w_total_bridges, w_bridge_balance, w_split, w_far
    d[0:4] = [w["w_score"], w["w_min_bridges"], w["w_total_bridges"], w["w_bridge_balance"]]
    BatterySolution.calculate_total_fitness.__defaults__ = tuple(d)


def variants():
    """(težina, faktor ili vrijednost, težine, w_far): osnovna + one-at-a-time promjene."""
    yield "base", 1.0, dict(BASE), W_FAR_BASE
    for name in BASE:
        for f in FACTORS:
            yield name, f, {**BASE, name: BASE[name] * f}, W_FAR_BASE
    for v in W_FAR_VALUES:
        yield "w_far", v, dict(BASE), v


def run():
    packs = [p for p in load_packs(PACKS_JSON) if p["name"] in PACKS]
    fields = ["pack", "weight", "factor", "rep", "S", "P", "min_bridges", "total_bridges", "bridge_var", "far_total", "fitness", "time_s"] + METRICS
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        try:
            for p in packs:
                pack = p["pack"]
                for w_name, factor, w, w_far in variants():
                    set_fitness_weights(w)
                    for rep in range(REPEATS):
                        random.seed(rep)  # isti seed za sve varijante -> poštena usporedba
                        t0 = time.time()
                        best = max(ClonalgOptimizer(pack, **OPTIMIZER_KWARGS).run(w_far=w_far), key=lambda s: s.fitness)
                        info = best.evaluate_solution()
                        best.calculate_total_fitness()
                        real = real_metrics(best, p["r_cell"], p["r_per_length"], selected=False)
                        row = {"pack": p["name"], "weight": w_name, "factor": factor, "rep": rep, "S": pack.no_groups,
                               "P": pack.no_cells_per_group, "min_bridges": info["min_bridges"], "total_bridges": info["total_bridges"],
                               "bridge_var": info["bridge_variance"], "far_total": best.far_total, "fitness": best.fitness,
                               "time_s": round(time.time() - t0, 1), **{m: real[m] for m in METRICS}}
                        writer.writerow(row)
                        f.flush()  # rezultat se sprema odmah
                        print(f"[{p['name']}] {w_name} x{factor} rep {rep}: cell_std={row['cell_std']:.4f} cell_max={row['cell_max']:.3f} "
                              f"total={row['total_bridges']} ({row['time_s']} s)", flush=True)
        finally:
            set_fitness_weights(BASE)


def summarize():
    """Prosjek metrika po varijanti i razlika od osnovne varijante, izražena u standardnim devijacijama osnovne (|z| < 1 = unutar šuma)."""
    import pandas as pd
    df = pd.read_csv(OUT_CSV)
    cols = ["total_bridges"] + METRICS
    mean = df.groupby(["pack", "weight", "factor"])[cols].mean()
    for pack_name in df["pack"].unique():
        base = df[(df["pack"] == pack_name) & (df["weight"] == "base")][cols]
        m, sd = base.mean(), base.std().replace(0, float("nan"))
        print(f"\n=== {pack_name}: osnovna varijanta (prosjek / std) ===")
        print(pd.DataFrame({"mean": m, "std": sd}).round(4).to_string())
        diff = (mean.loc[pack_name] - m)
        print("razlika od osnovne (prosjek), te u jedinicama std osnovne:")
        print(diff.round(4).to_string())
        print((diff / sd).round(1).to_string())
    mean.round(4).to_csv("sensitivity_summary.csv")


if __name__ == "__main__":
    run()
    summarize()