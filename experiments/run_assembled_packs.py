"""Table 5, column "Model": resistance difference between the snake and CLONALG 7S3P packs according to the electrical model.

    uv run python experiments/run_assembled_packs.py

The layouts are inputs, not results of this script: they are exactly the packs that were assembled and measured
(results/fig9_experiment/*.pkl|json). Snake is the plain row-wise snake (heuristics.snake_pattern_rows);
the CLONALG layout comes from the interactive main.py. Resistances: config.ASSEMBLED (strip 0.15 x 7 mm, R_cell 45 mOhm).
Output: results/fig9_experiment/model_resistance.csv
"""
import matplotlib
matplotlib.use('Agg')

from kod.config import ASSEMBLED
from kod.metrics import real_metrics
from kod.storage import load_solution, write_rows

FOLDER = 'results/fig9_experiment'


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
