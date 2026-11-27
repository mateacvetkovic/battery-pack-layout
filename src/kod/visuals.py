import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib.patches import Polygon
import numpy as np
plt.ion()  

# veličine fontova za plotGroups (rasporede grupa); skripte za slike ih mijenjaju prije crtanja
# Slika 2 je nacrtana s axis=16, label=12, bms=8, ticks=12; Slika 4 s ovim zadanim vrijednostima
FONT = {'axis': 22, 'label': 20, 'bms': 20, 'ticks': 22}


def _init_plot(W, H, vertices, show):
    base_scale = 12 
    if W >= H:
        width_fig = base_scale
        height_fig = base_scale * (H / W)
    else:
        height_fig = base_scale
        width_fig = base_scale * (W / H)
        
    if not show:
        plt.ioff()

    fig, ax = plt.subplots(figsize=(max(width_fig, 4), max(height_fig, 4)))  
    
    if not show:
        plt.ion() # Vratimo natrag na ion stanje
    # ax.add_patch(patches.Rectangle((0, 0), W, H, linewidth=2, edgecolor='black', facecolor='none'))
    # if vertices is not None:
    #     ax.add_patch(Polygon(vertices, closed=True, fill=None, edgecolor='blue', linewidth=2, linestyle='--'))
    # return fig, ax
    if vertices is not None:
        ax.add_patch(Polygon(vertices, closed=True, fill=None, edgecolor='blue', linewidth=2, linestyle='--'))
    else:
        ax.add_patch(patches.Rectangle((0, 0), W, H, linewidth=2, edgecolor='black', facecolor='none'))
    return fig,ax


def _finalize_plot(ax, W, H, title, save, name, show):
    # ax.set_xlim(-5, W + 0.1 * W)
    # ax.set_ylim(-5, H + 0.1 * H)
    ax.autoscale_view()
    ax.margins(0.03)
    ax.set_xlabel('Width (mm)', fontsize=FONT['axis'], fontweight='bold')
    ax.set_ylabel('Height (mm)', fontsize=FONT['axis'], fontweight='bold')
    ax.set_aspect('equal')
    ax.set_title('{}'.format(title), fontsize=FONT['axis'])
    if save:
        plt.savefig(name,bbox_inches="tight")
    if show:
        plt.draw()
        plt.pause(0.1)


def plotGrid(cells, W, H, d, cell_d=None, save=False, show=True, name='battery_pack.png', title=None, vertices=None, higlight_ids=None):
    if not cells:
        print("The pack has no cells!")
        return
    if cell_d is None:
        cell_d = d
    _, ax = _init_plot(W, H, vertices, show)
    title_text = title if title is not None else f'Battery dimensions: {W}x{H} cm'
    added_labels = set()
    for i, cell in enumerate(cells):
        y, x = cell.y, cell.x
        if 0 <= x <= W and 0 <= y <= H:
            circle_color = 'grey'
            if higlight_ids is not None and cell.id in higlight_ids:
                c_label = 'BMS' if 'BMS' not in added_labels else None
                added_labels.add('BMS')
                circle_color = 'black'
                ax.text(x, y, "BMS", fontsize=16, ha='center', va='center', color='white', fontweight='bold', zorder=7)
            else:
                c_label = 'Free cells' if 'FREE' not in added_labels else None
                added_labels.add('FREE')
                ax.text(x, y, f"{cell.id}", fontsize=16, ha='center', va='center', color='grey', fontweight='bold', zorder=7)
            
            ax.add_patch(patches.Circle((x, y), cell_d/2, edgecolor='black', facecolor=circle_color, alpha=0.6, label = c_label))

    ax.legend(loc="upper right", fontsize=14)

    ax.tick_params(axis='both', which='major', labelsize=12)

    _finalize_plot(ax, W, H, title_text, save, name, show)


def plotGroups(cells, W, H, d, cell_to_group, no_groups,  cell_d=None, save=False, show=True, name='battery_pack.png', title='', vertices=None, inside_ids=None):
    if not cells:
        print("No cells to draw!")
        return
    
    if cell_d is None:
        cell_d = d
    _, ax = _init_plot(W, H, vertices, show)
    #cmap = plt.get_cmap('nipy_spectral', no_groups if no_groups > 0 else 1)
    cmap = plt.get_cmap('nipy_spectral')
    added_labels = set()
    for i, cell in enumerate(cells):
        y, x = cell.y, cell.x
        if getattr(cell, 'group', None) == -2:
            current_group = cell.group
        else:
            current_group = cell_to_group[i] if cell_to_group is not None else cell.group
        if 0 <= x <= W and 0 <= y <= H:
            if current_group == -2:
                circle_color = 'black'
                c_label = 'BMS' if 'BMS' not in added_labels else None
                added_labels.add('BMS')
                ax.text(x, y, "BMS", fontsize=FONT['bms'], color='white', ha='center', va='center', fontweight='bold', zorder=7)
            elif current_group is None or current_group == -1:
                circle_color = 'grey'
                c_label = 'Free cells' if 'FREE' not in added_labels else None
                added_labels.add('FREE')
                ax.text(x, y, f"C{cell.id}", fontsize=FONT['label'], ha='center', va='center', color='black', fontweight='bold', zorder=7)
            else:
                norm_group = current_group / max(1, no_groups)
                # circle_color = cmap(norm_group)
                circle_color = cmap(0.08 + 0.8 * current_group / max(1, no_groups - 1))
                group_key = f'G_{current_group}'
                c_label = f'Group {current_group}' if group_key not in added_labels else None
                added_labels.add(group_key)
                ax.text(x, y, f"G{current_group}", fontsize=FONT['label'], ha='center', va='center', zorder=6)
                #ax.text(x, y, f"C{cell.id}", fontsize=12, ha='center', va='center', zorder=6, label=f'Group {current_group}')
            ax.add_patch(patches.Circle((x, y), cell_d/2, edgecolor='black', facecolor=circle_color, alpha=0.6, label=c_label))
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        sorted_pairs = sorted(zip(handles, labels), key=lambda pair: pair[1])
        handles, labels = zip(*sorted_pairs)
        handles, labels = list(handles), list(labels)

    ax.legend(
        handles, 
        labels, 
        title="Electrical connection:\n- within a group: PARALLEL\n- between groups: SERIES", 
        loc='upper left', 
        bbox_to_anchor=(1.02, 1), 
        borderaxespad=0,
        fontsize=14,
        title_fontsize=14
    )
    ax.tick_params(axis='both', which='major', labelsize=FONT['ticks'])
    _finalize_plot(ax, W, H, title, save, name, show)


def _face(group, side):
    """Strana paketa na kojoj je stezaljka. Parne grupe: p gore, n dolje; neparne su okrenute, pa obrnuto.
    Zato su mostovi između grupa naizmjence gore i dolje, a most ima obje stezaljke na istoj strani."""
    return 'top' if (side == 'p') == (group % 2 == 0) else 'bottom'
 
 
def draw_bridges(sol, bridges, currents=None, pairs=None, face=None, save=False, name='bridges.png', show=True, label='bridge current', vmax=None):
    """
    Crta raspored ćelija (kao sol.display) i preko njega mostove iz all_bridges(...), zasebno za gornju i donju
    stranu paketa (face='top' ili 'bottom'; None = dvije slike). Konvencija: parne grupe imaju p stezaljku gore.
    Donja strana nije zrcaljena, ćelije su na istim mjestima kao na gornjoj slici.
      bridges:  lista mostova ({'a': [cell, side], 'b': [cell, side], 'length': d})
      currents: neobavezno, solve(...)['bridge_currents']; ako je zadano, boja mosta = struja, inače zeleno = unutar grupe, crno = između grupa
      pairs:    lista indeksa g (par g -> g+1) koje treba nacrtati, None = svi parovi
      label:    natpis uz traku boja, npr. 'omjer prema nazivnoj struji ćelije' ako šalješ currents / nominal_current
      vmax:     gornja granica skale boja (donja je 0); None = najveća vrijednost u currents. Fiksan vmax daje iste boje na svim
                slikama, pa se mogu uspoređivati; vrijednosti iznad vmax dobiju najtamniju boju
      name:     kod dviju slika dobiju nastavak _top i _bottom
    Linije idu od središta do središta ćelije. Most između grupa ima točkice na krajevima.
    """
    for f in (['top', 'bottom'] if face is None else [face]):
        _draw_face(sol, bridges, currents, pairs, f, save, name.replace('.png', f'_{f}.png') if face is None else name, show, label, vmax)
 
 
def _draw_face(sol, bridges, currents, pairs, face, save, name, show, label, vmax=None):
    pack, cg = sol.pack, sol.cell_to_group
    cells = pack.grid.cells
    title = f'Bridges, {"top" if face == "top" else "bottom"} side: {pack.no_groups}S {pack.no_cells_per_group}P'
    plotGroups(cells, pack.grid.W, pack.grid.H, pack.d, cg, pack.no_groups, title=title,
               cell_d=pack.cell_d, vertices=pack.vertices, save=False, show=False)
    ax = plt.gca()
    if currents is not None:
        cmap, norm = plt.cm.plasma_r, plt.Normalize(0, vmax if vmax is not None else max(currents), clip=True)
 
    for i, b in enumerate(bridges):
        (u, su), (v, sv) = b['a'], b['b']
        if _face(cg[u], su) != face:
            continue
        if pairs is not None and (cg[u] if su == 'n' else cg[u] - 1) not in pairs:
            continue
        intra = cg[u] == cg[v]
        colour = cmap(norm(currents[i])) if currents is not None else ('tab:green' if intra else 'black')  # crvena izbjegnuta: rezervirana za preopterećenje
        ax.plot([cells[u].x, cells[v].x], [cells[u].y, cells[v].y], color=colour, lw=2.5, solid_capstyle='round',
                zorder=5, marker=None if intra else 'o', markersize=4)  # zorder ispod oznaka grupa (6)
 
    if currents is not None:
        plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, label=label, orientation='horizontal', pad=0.12, shrink=0.6)  # ispod slike, da ne prekrije legendu
        ax.set_title(title + '  (colour = bridge current)', fontsize=14)
    else:
        ax.set_title(title + '  (green = within a group, black = between groups)', fontsize=12)
    if save:
        plt.savefig(name, bbox_inches='tight')
    if show:
        plt.draw()
        plt.pause(0.1)

# ---------- slike za članak (Slika 2 i 4) ----------
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch
from matplotlib.ticker import FixedFormatter, FixedLocator

SEG_NORM = LogNorm(vmin=1, vmax=6)   # zajednička skala struje segmenta za sve panele Slike 2
SEG_CMAP = plt.get_cmap('plasma_r')
SEG_TICKS = [1, 1.5, 2, 3, 4, 6]


def solve_all_bridges(sol, r_cell, r_per_length):
    """Električni model sa svim mogućim mostovima (§2.9). Vraća (mostovi, rezultat solvera)."""
    from kod.circuit import all_bridges, solve
    bridges = all_bridges(sol.pack, sol.cell_to_group)
    return bridges, solve(sol.cell_to_group, bridges, r_cell, r_per_length, sol.pack.no_cells_per_group)


def draw_hot_cells(ax, sol, res, cell_threshold=1.03):
    """Crveni prsten oko ćelija čija struja prelazi nazivnu za više od (cell_threshold - 1)."""
    cells, nom = sol.pack.grid.cells, res['nominal_current']
    for c, I in res['cell_currents'].items():
        if I / nom >= cell_threshold:
            ax.add_patch(Circle((cells[c].x, cells[c].y), sol.pack.cell_d / 2, fill=False, edgecolor='red', lw=2.5, zorder=11))


def draw_layout_currents(ax, sol, r_cell, r_per_length, n_segments=4, cell_threshold=1.03):
    """Najopterećenije ćelije + n_segments segmenata s najvećom strujom, obojanih po struji. Vraća te struje (relativne)."""
    bridges, res = solve_all_bridges(sol, r_cell, r_per_length)
    cells, nom = sol.pack.grid.cells, res['nominal_current']
    seg = sorted(((res['bridge_currents'][i] / nom, b) for i, b in enumerate(bridges) if i not in res['shorted_bridges']),
                 key=lambda t: t[0], reverse=True)[:n_segments]
    for v, b in reversed(seg):  # najjači se crta zadnji, preko ostalih
        c1, c2 = cells[b['a'][0]], cells[b['b'][0]]
        ax.plot([c1.x, c2.x], [c1.y, c2.y], color='black', lw=6, solid_capstyle='round', zorder=12)
        ax.plot([c1.x, c2.x], [c1.y, c2.y], color=SEG_CMAP(SEG_NORM(max(v, 1))), lw=4, solid_capstyle='round', zorder=13)
    draw_hot_cells(ax, sol, res, cell_threshold)
    return [v for v, _ in seg]


def save_colorbar(path):
    """Zajednička (logaritamska) skala struje segmenta."""
    fig = plt.figure(figsize=(3.5, 0.6))
    cax = fig.add_axes([0.05, 0.55, 0.9, 0.2])
    fig.colorbar(ScalarMappable(SEG_NORM, SEG_CMAP), cax=cax, orientation='horizontal')
    cax.xaxis.set_major_locator(FixedLocator(SEG_TICKS))
    cax.xaxis.set_major_formatter(FixedFormatter([str(t) for t in SEG_TICKS]))
    cax.xaxis.set_minor_locator(FixedLocator([]))
    cax.set_xlabel('Segment current / nominal cell current', fontsize=10)
    cax.tick_params(labelsize=10)
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)


def save_legend(no_groups, path, ncol=8, bms=False, n_segments=None, bridges=False):
    """Jedna legenda za sve panele; boje grupa iste kao u plotGroups.
    bms: dodaje BMS; n_segments: dodaje oznake za preopterećene ćelije i n_segments najjačih segmenata (Slika 2)."""
    cmap = plt.get_cmap('nipy_spectral')
    handles = [Patch(facecolor=cmap(0.08 + 0.8 * g / max(1, no_groups - 1)), edgecolor='black', alpha=0.6, label=f'G{g}')
               for g in range(no_groups)]
    if bms:
        handles.append(Patch(facecolor='black', edgecolor='black', alpha=0.6, label='BMS'))
    handles.append(Patch(facecolor='grey', edgecolor='black', alpha=0.6, label='Unused'))
    if n_segments:
        handles += [Line2D([], [], marker='o', ls='', markerfacecolor='none', markeredgecolor='red',
                           markeredgewidth=2, markersize=9, label='Cell current > 1.03'),
                    Line2D([], [], color=SEG_CMAP(0.5), lw=4, label=f'{n_segments} highest segment currents')]
    if bridges:
        handles += [Line2D([], [], color='tab:green', lw=2.5, label='Connection within a group'),
                    Line2D([], [], color='black', lw=2.5, marker='o', markersize=4, label='Connection between groups')]
    fig = plt.figure(figsize=(7, 0.6))
    fig.legend(handles=handles, loc='center', ncol=ncol, fontsize=14, frameon=False)
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
