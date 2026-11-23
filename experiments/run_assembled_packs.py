"""Tablica 5, stupac "Model": razlika otpora snake i CLONALG paketa 7S3P po električnom modelu.

    uv run python experiments/run_assembled_packs.py

Rasporedi su ulaz, ne rezultat ove skripte: to su točno oni paketi koji su sastavljeni i izmjereni
(results/fig4_experiment/*.pkl|json). Snake je jednostavan snake po redovima (heuristics.snake_pattern_rows),
CLONALG raspored je iz interaktivnog main.py. Otpori: config.ASSEMBLED (traka 0.15 x 7 mm, R_cell 45 mOhm).
Izlaz: results/fig4_experiment/model_resistance.csv
"""
import matplotlib
matplotlib.use('Agg')

from kod.config import ASSEMBLED
from kod.metrics import real_metrics
from kod.storage import load_solution, write_rows

FOLDER = 'results/fig4_experiment'


def main():
    rows = []
    for name in ('snake_7S3P', 'clonalg_7S3P'):
        sol, _ = load_solution(f'{FOLDER}/{name}.pkl')
        m = real_metrics(sol, ASSEMBLED['r_cell'], ASSEMBLED['r_per_length'], selected=False, I=ASSEMBLED['I'])
        rows.append({'layout': name, 'R_total_mohm': round(m['R_total'] * 1000, 2), **ASSEMBLED})
    rows.append({'layout': 'difference', 'R_total_mohm': round(rows[0]['R_total_mohm'] - rows[1]['R_total_mohm'], 2), **ASSEMBLED})
    write_rows(f'{FOLDER}/model_resistance.csv', rows)
    for r in rows:
        print(f"{r['layout']:14} {r['R_total_mohm']:.1f} mOhm")


if __name__ == '__main__':
    main()
