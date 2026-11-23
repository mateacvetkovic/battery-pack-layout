# Rezultati članka

Imena paketa u kodu i u članku razlikuju se: vidi `data/pack_names.csv`. Definicije paketa su u `data/packages.json`
(npr. Triangle 1 u članku = `trokut_2` u kodu).

| Mapa | U članku | Proizvela ga je |
|---|---|---|
| `table2_table3_baseline/<paket>.csv` | Tablica 2; retci `CLONALG w_split=1000` su Tablica 3 ("Split = no") | `evaluator.run()` → `evaluation.baseline_table` |
| `table2_table3_baseline/<paket>_sazetak.csv` | isto, prosjek ± std | isto |
| `table2_table3_baseline/solutions/<paket>/` | rješenja iz kojih su CSV-ovi; Slika 2 = `trokut_4/` (snake_1_red i CLONALG_w_split=0_run0) | isto |
| `table2_table3_baseline/trokut_21700_part1*.csv`, `_part2*.csv` | Triangle 8 u Tablici 2 = part1 (3 pokretanja, 11.11. 12:42) + part2 (2 pokretanja, 11.11. 13:44) spojeno ručno, n = 5 | isto, pokrenuto dvaput |
| `table4_timing/` | Tablica 4 | `dodatni_eksperimenti.timing()` |
| `fig3_convergence/` | Slika 3 (`trokut_5` = Triangle 4, `pravokutni_trokut_B` = Triangle 6) | `dodatni_eksperimenti.convergence()` → `plot_convergence()` |
| `fig4_experiment/` | Slika 4 i stupac "Model" u Tablici 5 | `main.py` (CLONALG), `run_snake` (snake); model: kraj `dodatni_eksperimenti.py` |
| `extra_resistance_sweep/otpor.csv` | nije u članku; podržava tvrdnju da poredak metoda ne ovisi o otporima | `dodatni_eksperimenti.resistance_sweep()` |
| `extra_population/` | nije u članku | `dodatni_eksperimenti.population_snapshot()` |

Nedostaje: izmjereni podaci za Tablicu 5 (mape s `log_ir.csv`) i fotografije za Sliku 4b i 4d.
