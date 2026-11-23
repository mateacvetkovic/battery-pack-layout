"""Rješava proizvoljnu mrežu otpornika iz JSON-a, npr.:

    uv run python examples/solve_circuit.py data/examples/3_grupe.json
"""
import json, sys
import numpy as np


def solve_circuit(path):
    """Cita JSON {"I": struja, "ulaz": cvor, "izlaz": cvor, "otpornici": [[cvor1, cvor2, otpor], ...]}.
    Izlaz je uzemljen (V=0), u ulaz se ubacuje struja I. Ispisuje napone cvorova, struje otpornika i ukupni otpor."""
    d = json.load(open(path))
    nodes = sorted({n for a, b, _ in d['otpornici'] for n in (a, b)} - {d['izlaz']})
    idx = {n: k for k, n in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for a, b, r in d['otpornici']:  # matrica vodljivosti: KCL u svakom cvoru
        for x, y in ((a, b), (b, a)):
            if x in idx:
                G[idx[x], idx[x]] += 1 / r
                if y in idx: G[idx[x], idx[y]] -= 1 / r
    rhs = np.zeros(len(nodes)); rhs[idx[d['ulaz']]] = d['I']
    V = dict(zip(nodes, np.linalg.solve(G, rhs))); V[d['izlaz']] = 0.0
    for a, b, r in d['otpornici']:
        print(f"{a}-{b}: struja {abs(V[a] - V[b]) / r:.4f}  (otpor {r})")
    print(f"ukupni otpor = {V[d['ulaz']] / d['I']:.4f}")
    return V


if __name__ == '__main__':
    solve_circuit(sys.argv[1])