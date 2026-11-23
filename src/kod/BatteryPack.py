import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib.patches import Polygon
from kod.grids import Cell, Grid
from kod.visuals import plotGrid
from kod.BatterySolution import BatterySolution

class BatteryPack:
    """
    razred koji predstavlja baterijski paket, upravlja njegovom geometrijom,
    celijama i konfiguracijom serijskih i paralelnih spojeva.
    """
    def __init__(self, grid, cell_type, battery_voltage=None, cell_voltage=None, type=None, vertices=None):
        """
        inicijalizacija baterijskog paketa s opcionalnim elektricnim parametrima.

        argumenti:
            grid: objekt mreze koji sadrzi celije i dimenzije
            cell_type: tip baterijske celije
            battery_voltage (float): opcionalni ukupni zeljeni napon paketa
            cell_voltage (float): opcionalni napon pojedinacne celije
            type (str): oblik ili tip paketa (npr. rectangle, triangle)
            vertices: opcionalni vrhovi poligona koji definira oblik paketa
        """
        self.d = grid.d
        self.cell_d = 21 if cell_type=='21700' else 18
        self.grid = grid
        self.usable_cells = self.grid.total_cells
        self.vertices = vertices
        self.cell_type = cell_type
        self.type = type
        self.bms_cell_ids = set()
        
        self.battery_voltage = None
        self.cell_voltage = None
        self.no_groups = None
        self.no_cells_per_group = None

        if battery_voltage is not None and cell_voltage is not None:
            self.set_voltage(battery_voltage, cell_voltage)

    def set_voltage(self, battery_voltage, cell_voltage):
        """
        postavlja napone paketa i celije te izracunava broj grupa i celija po grupi.

        argumenti:
            battery_voltage (float): ukupni zeljeni napon paketa
            cell_voltage (float): napon pojedinacne celije
        """
        if battery_voltage < cell_voltage:
            raise ValueError("Napon paketa mora biti veći od napona ćelije!")
        
        no_groups = int(battery_voltage / cell_voltage)
        if no_groups > self.usable_cells:
            raise ValueError("Nedovoljno ćelija u paketu za traženi napon!")
            
        self.battery_voltage = battery_voltage
        self.cell_voltage = cell_voltage
        self.no_groups = no_groups
        self.no_cells_per_group = self.usable_cells // self.no_groups   

    def get_possible_configurations(self, cell_voltage):
        """
        izracunava sve moguce s/p konfiguracije na temelju trenutnog broja iskoristivih celija.

        argumenti:
            cell_voltage (float): napon pojedinacne celije

        povratna vrijednost:
            list: lista rjecnika s mogucim konfiguracijama (s, p, napon, iskoristeno_celija)
        """
        configs = []
        for s in range(1, self.usable_cells + 1):
            p = self.usable_cells // s
            if p > 0:
                configs.append({'S': s, 'P': p, 'voltage': s * cell_voltage, 'used_cells': s * p})
        return configs

    def set_bms_cells(self, cell_ids):
        """
        postavlja rezervirane bms celije i azurira broj iskoristivih celija po grupi.

        argumenti:
            cell_ids (iterable): identifikatori celija koje sluze za bms
        """
        for cell_id in cell_ids:
            if cell_id<self.grid.total_cells and cell_id>=0:
                self.bms_cell_ids.add(cell_id)
        self.usable_cells = self.grid.total_cells - len(self.bms_cell_ids)
        if self.no_groups is not None:
            self.no_cells_per_group = self.usable_cells // self.no_groups
        for cell in self.grid.cells:
            if cell.id in self.bms_cell_ids:
                cell.group = -2

    def get_neighbours(self, cell_id):
        """
        dohvaca objekte susjednih celija koje nisu rezervirane za bms.

        argumenti:
            cell_id (int): identifikator celije za koju se traze susjedi

        povratna vrijednost:
            list: lista objekata susjednih celija
        """
        return [n for n in self.grid.get_neighbouring_cells(cell_id) if n.group != -2]
    
    def get_neighbours_ids(self, cell_id):
        """
        dohvaca identifikatore susjednih celija koje nisu rezervirane za bms.

        argumenti:
            cell_id (int): identifikator celije za koju se traze susjedi

        povratna vrijednost:
            list: lista identifikatora susjednih celija
        """
        all_neighbors = self.grid.get_neighbouring_cells(cell_id)
        return [cell.id for cell in all_neighbors if cell.group != -2]
        
    def display(self):
        """
        prikazuje vizualizaciju mreze baterijskog paketa i njegove konfiguracije.
        """
        if(self.no_groups is not None and self.no_cells_per_group is not None):
            title = f'Ukupan broj iskoristivih ćelija: {self.usable_cells}, konfiguracija {self.no_groups}S {self.no_cells_per_group}P'
        else:
            title = f'Ukupan broj iskoristivih ćelija: {self.usable_cells}'

        plotGrid(self.grid.cells, self.grid.W, self.grid.H, self.d, self.cell_d, title=title, vertices=self.vertices, higlight_ids=self.bms_cell_ids)

def setup_battery_pack(inputs):
    """Gradi BatteryPack iz ulaza (cell_type, cell_distance, net_type, shape_type, dimensions_cm):
    smješta rešetku u pravokutnik (obje orijentacije za saćastu, §2.3.1) ili trokut (§2.3.2)."""
    from kod.grids import HexGrid, RectangularGrid
    from kod.containers import TriangleContainer
    from kod.optimizers import TriangleContainerOptimizer

    d = inputs['cell_distance']
    dims_mm = [dim * 10.0 for dim in inputs['dimensions_cm']]

    if inputs['shape_type'] == 'rectangle':
        v = None
        W, H = dims_mm[0], dims_mm[1]
        if inputs['net_type'] == 'saćasti':
            grid_h = HexGrid(d, W, H)
            grid_h.fit()
            grid_v = HexGrid(d, H, W)
            grid_v.fit()
            grid = grid_h if grid_h.total_cells >= grid_v.total_cells else grid_v
        else:
            grid = RectangularGrid(cell_distance=d, width=W, height=H)
            grid.fit()
    else:
        container = TriangleContainer(inputs['dimensions_cm'])
        max_dim = container.calculate_triangle_grid_size(d)
        W, H = max_dim, max_dim
        if inputs['net_type'] == 'saćasti':
            grid = HexGrid(cell_distance=d, width=W, height=H)
        else:
            grid = RectangularGrid(cell_distance=d, width=W, height=H)
        grid.fit()
        to = TriangleContainerOptimizer(container, grid)
        cells_inside_ids, v, grid = to.solve(15)
        grid.create_subgrid(cells_inside_ids)

    return BatteryPack(grid=grid, cell_type=inputs['cell_type'], vertices=v, type=inputs['shape_type'])


def load_packs(path, names=None):
    """Učitava pakete iz JSON-a (data/packages.json): lista objekata s ključevima name, cell_type, cell_distance,
    net_type, shape_type, dimensions_cm, voltage i neobavezno bms_ids, r_cell, r_per_length.
    names: ako je zadano, gradi samo te pakete (gradnja trokuta traje). Vraća {ime: {'name', 'pack', 'inputs', 'r_cell', 'r_per_length'}}."""
    import json
    from kod.config import CELL_SPECS, PAPER
    with open(path, encoding='utf-8') as f:
        examples = json.load(f)
    packs = {}
    for i, ex in enumerate(examples):
        name = ex.get('name', f'paket{i + 1}')
        if names is not None and name not in names:
            continue
        missing = [k for k in ('cell_type', 'cell_distance', 'net_type', 'shape_type', 'dimensions_cm', 'voltage') if k not in ex]
        if missing:
            raise ValueError(f'{name}: nedostaju ključevi {missing}')
        pack = setup_battery_pack({k: ex[k] for k in ('cell_type', 'cell_distance', 'net_type', 'shape_type', 'dimensions_cm')})
        if ex.get('bms_ids'):  # isti redoslijed kao u main.py: prvo BMS, pa napon
            pack.set_bms_cells(ex['bms_ids'])
        pack.set_voltage(ex['voltage'], CELL_SPECS[ex['cell_type']]['nominal_voltage'])
        packs[name] = {'name': name, 'pack': pack, 'inputs': dict(ex),
                       'r_cell': ex.get('r_cell', PAPER['r_cell']), 'r_per_length': ex.get('r_per_length', PAPER['r_per_length'])}
    if names is not None and set(names) - set(packs):
        raise KeyError(f'nema u {path}: {sorted(set(names) - set(packs))}')
    return packs
