import json
import numpy as np


# ---------- 1. all possible bridges ----------
def all_bridges(pack, cell_to_group):
    """All possible bridges: between adjacent cells of the same group (on the p and on the n side) and between adjacent
    cells of group g (n side) and g+1 (p side). Bridge = {'a': [cell, side], 'b': [cell, side], 'length': d}.
    Bridges on the p side of group 0 and on the n side of the last group are included for plotting, but carry zero
    current in the calculation because those terminals are ideally connected (see _node)."""
    n = pack.no_groups
    cells = pack.grid.cells
    dist = lambda c, m: float(np.hypot(cells[c].x - cells[m].x, cells[c].y - cells[m].y))
    bridges = []
    for c in range(len(cell_to_group)):
        g = cell_to_group[c]
        if not 0 <= g < n:  # unused cells have group -1
            continue
        for m in pack.get_neighbours_ids(c):
            if cell_to_group[m] == g and c < m:  # within a group, each pair once
                for side in ('n', 'p'):
                    bridges.append({'a': [c, side], 'b': [m, side], 'length': dist(c, m)})
            elif cell_to_group[m] == g + 1:  # between groups: n side of g to p side of g+1
                bridges.append({'a': [c, 'n'], 'b': [m, 'p'], 'length': dist(c, m)})
    return bridges


# ---------- 2. saving and loading ----------
def save_solution(path, cell_to_group, bridges, r_cell, r_per_length, I):
    """Optional: saves the input of the calculation (cell groups, bridges, resistances, current) so it can be repeated later."""
    json.dump({'cell_to_group': list(map(int, cell_to_group)), 'bridges': bridges, 'r_cell': r_cell,
               'r_per_length': r_per_length, 'I': I}, open(path, 'w'))


def load_solution(path):
    """Returns a dict whose keys are exactly the arguments of solve, so solve(**load_solution(path)) works."""
    return json.load(open(path))


# ---------- 3. equations and solving ----------
def _node(c, side, cell_to_group):
    """Node (terminal) name. All p terminals of group 0 form one node (IN), all n terminals of the last group one node (OUT)."""
    if side == 'p' and cell_to_group[c] == 0:
        return 'IN'
    if side == 'n' and cell_to_group[c] == max(cell_to_group):
        return 'OUT'
    return f'{c}{side}'


def _resistors(cell_to_group, bridges, r_cell, r_per_length):
    """List of (node1, node2, resistance, label): every cell ('cell', id) and every bridge ('bridge', index)."""
    ctg = cell_to_group
    res = []
    for c, g in enumerate(ctg):
        if g >= 0:
            res.append((_node(c, 'p', ctg), _node(c, 'n', ctg), r_cell, ('cell', c)))
    for i, b in enumerate(bridges):
        (c1, s1), (c2, s2) = b['a'], b['b']
        res.append((_node(c1, s1, ctg), _node(c2, s2, ctg), r_per_length * b['length'], ('bridge', i)))
    return res


def _matrix(resistors, I):
    """KCL at every node: G·V = b. OUT is grounded (V=0), so it is not in the system; current I is injected at IN."""
    nodes = sorted({x for a, b, _, _ in resistors for x in (a, b)} - {'OUT'})
    idx = {n: k for k, n in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for a, b, r, _ in resistors:
        for x, y in ((a, b), (b, a)):
            if x in idx:
                G[idx[x], idx[x]] += 1 / r
                if y in idx:
                    G[idx[x], idx[y]] -= 1 / r
    rhs = np.zeros(len(nodes)); rhs[idx['IN']] = I
    return nodes, G, rhs


def solve(cell_to_group, bridges, r_cell, r_per_length, I):
    """Solves the network directly from in-memory data. Returns
    {'R_total', 'nominal_current' (= I / P), 'cell_currents': {id: current}, 'bridge_currents': [current per index in bridges]}.
    Currents are in the unit in which I is given (amperes only if I is in amperes)."""
    resistors = _resistors(cell_to_group, bridges, r_cell, r_per_length)
    nodes, G, rhs = _matrix(resistors, I)
    V = dict(zip(nodes, np.linalg.solve(G, rhs))); V['OUT'] = 0.0
    current = {label: abs(V[a] - V[b]) / r for a, b, r, label in resistors}
    P = sum(1 for g in cell_to_group if g == 0)  # cells per group, so the nominal cell current is I / P
    shorted = [l[1] for a, b, _, l in resistors if l[0] == 'bridge' and a == b]  # bridges at the ideal pack terminals, zero current
    return {'R_total': float(V['IN'] / I), 'nominal_current': I / P, 'shorted_bridges': shorted,
            'cell_currents': {l[1]: float(i) for l, i in current.items() if l[0] == 'cell'},
            'bridge_currents': [float(current[('bridge', i)]) for i in range(len(bridges))]}


def print_result(result, bridges, top=5, top_cells=5, idle=0.05, junction=None):
    """Prints the total resistance, statistics per category (cells, bridges between groups, bridges within a group),
    the `top_cells` most loaded cells and the `top` most loaded bridges (with the cells they connect).
    Peak factor = max / mean; 'nearly idle' = ratio below `idle` (of the nominal cell current)."""
    cc, bc, nom = result['cell_currents'], result['bridge_currents'], result['nominal_current']
    skip = set(result['shorted_bridges'])  # ideal terminals carry zero current by assumption and are excluded from the statistics
    print(f"R_total = {result['R_total']:.4f}, nominal cell current I/P = {nom:.4g} (ratios below are current / (I/P))")

    def stat(name, ratios, with_idle, with_std=False):
        mean, mx = sum(ratios) / len(ratios), max(ratios)
        extra = f", stdev {np.std(ratios):.3f}" if with_std else ""
        extra += f", nearly idle (< {idle:.0%}): {sum(r < idle for r in ratios) / len(ratios):.0%}" if with_idle else ""
        print(f"  {name} ({len(ratios)}): mean {mean:.3f}, max {mx:.3f}, peak factor {mx / mean:.3f}{extra}")

    print("statistics (ratios to the nominal cell current):")
    stat('cells', [c / nom for c in cc.values()], False, True)
    between = [bc[i] / nom for i, b in enumerate(bridges) if i not in skip and b['a'][1] != b['b'][1]]
    within = [bc[i] / nom for i, b in enumerate(bridges) if i not in skip and b['a'][1] == b['b'][1]]
    stat('bridges between groups', between, True, True)
    stat('bridges within groups', within, True, True)
    if skip:
        print(f"  (excluding {len(skip)} bridges at the ideal pack terminals, zero current by assumption)")
    if junction:
        worst = max(junction, key=lambda g: junction[g]['total'])
        print("junction resistance estimate (border bridges in parallel + the larger of the two paths to the farthest cell):")
        for g in sorted(junction):
            j = junction[g]
            print(f"  G{g} - G{g + 1}: {j['total']:.4f} = border {j['border']:.4f} + max(G{g} {j['far_a']:.4f}, G{g + 1} {j['far_b']:.4f})" + ("   <- largest" if g == worst else ""))
    lo = min(cc, key=cc.get)
    print(f"most loaded cells (least loaded: cell {lo}, ratio {cc[lo] / nom:.3f}):")
    for c in sorted(cc, key=cc.get, reverse=True)[:top_cells]:
        print(f"  cell {c}: ratio {cc[c] / nom:.3f}")
    print(f"most loaded bridges (out of {len(bc)}):")
    for i in sorted(range(len(bc)), key=lambda i: -bc[i])[:top]:
        (c1, s1), (c2, s2) = bridges[i]['a'], bridges[i]['b']
        print(f"  bridge {i}: cell {c1} ({s1}) - cell {c2} ({s2}), ratio {bc[i] / nom:.3f}  (current {bc[i]:.4g})")


def save_result(path, result):
    """Saves the result of solve to JSON (cell keys become strings)."""
    json.dump(result, open(path, 'w'))


def junction_estimate(bridges, cell_to_group, r_per_length):
    """Estimate of the junction resistance between groups g and g+1 without the solver (no currents needed):
      'border' = parallel resistance of all border bridges = 1 / Σ(1/R_k)
      'far_a'  = resistance of the shortest path (over within-group bridges of g, n side) from the nearest border bridge to the farthest cell of g
      'far_b'  = the same for group g+1 (p side)
      'total'  = border + max(far_a, far_b)
    The shortest path is a single path (parallel paths are not counted), so far_* is an upper bound. Cells that cannot be
    reached over within-group bridges (no path from the border) are not included in the max."""
    import heapq
    ctg = cell_to_group
    R = lambda b: r_per_length * b['length']

    def far(group, side, sources):
        adj = {}
        for b in bridges:
            (c1, s1), (c2, s2) = b['a'], b['b']
            if s1 == s2 == side and ctg[c1] == ctg[c2] == group:
                adj.setdefault(c1, []).append((c2, R(b)))
                adj.setdefault(c2, []).append((c1, R(b)))
        dist = {c: 0.0 for c in sources}
        heap = [(0.0, c) for c in sources]
        while heap:
            d, c = heapq.heappop(heap)
            if d > dist[c]:
                continue
            for m, r in adj.get(c, []):
                if d + r < dist.get(m, float('inf')):
                    dist[m] = d + r
                    heapq.heappush(heap, (d + r, m))
        return max(dist.values())

    out = {}
    for g in range(max(ctg)):
        border = [b for b in bridges if b['a'][1] == 'n' and b['b'][1] == 'p' and ctg[b['a'][0]] == g and ctg[b['b'][0]] == g + 1]
        if not border:
            continue
        r_border = 1 / sum(1 / R(b) for b in border)
        far_a = far(g, 'n', {b['a'][0] for b in border})
        far_b = far(g + 1, 'p', {b['b'][0] for b in border})
        out[g] = {'border': r_border, 'far_a': far_a, 'far_b': far_b, 'total': r_border + max(far_a, far_b)}
    return out