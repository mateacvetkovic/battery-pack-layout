"""Spremanje i učitavanje rješenja i rezultata.

Rješenje se sprema dvaput:
  - .pkl: cijeli BatterySolution (s paketom), za crtanje i ponovni izračun;
  - .json: samo ulazi paketa i cell_to_group. Ne ovisi o verziji klasa, pa ga recenzent može pročitati i bez ovog koda.
"""
import csv
import json
import os
import pickle
import platform
import subprocess
import sys
from datetime import datetime


class _Unpickler(pickle.Unpickler):
    """Stari pickleovi pokazuju na src.kod.X; isti razredi su sada u kod.X."""
    def find_class(self, module, name):
        if module.startswith('src.kod.'):
            module = module[len('src.'):]
        return super().find_class(module, name)


def save_solution(path, solution, inputs, **extra):
    """Sprema <path>.pkl i <path>.json. extra (npr. seed, method) ide u oba."""
    base = path[:-4] if path.endswith('.pkl') else path
    os.makedirs(os.path.dirname(base) or '.', exist_ok=True)
    with open(base + '.pkl', 'wb') as f:
        pickle.dump({'solution': solution, 'inputs': inputs, **extra}, f)
    with open(base + '.json', 'w', encoding='utf-8') as f:
        json.dump({'inputs': inputs, 'bms_ids': sorted(solution.pack.bms_cell_ids),
                   'cell_to_group': [int(g) for g in solution.cell_to_group], **extra}, f, ensure_ascii=False, indent=1)


def load_solution(path):
    """Vraća (solution, inputs) iz .pkl, i iz starih pickleova (src.kod.*)."""
    with open(path, 'rb') as f:
        data = _Unpickler(f).load()
    return data['solution'], data['inputs']


def write_rows(path, rows):
    """Upisuje listu rječnika u CSV (stupci iz prvog retka)."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write_meta(folder, **params):
    """meta.json uz rezultate: git commit, verzije, datum i parametri pokretanja."""
    def git(*args):
        try:
            return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    import numpy, scipy
    meta = {'date': datetime.now().isoformat(timespec='seconds'), 'command': ' '.join(sys.argv),
            'git_commit': git('rev-parse', 'HEAD'), 'git_dirty': bool(git('status', '--porcelain', '--untracked-files=no')),
            'python': platform.python_version(), 'numpy': numpy.__version__, 'scipy': scipy.__version__,
            'platform': platform.platform(), 'processor': platform.processor(), **params}
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1, default=str)
