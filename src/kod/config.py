"""Sve konstante na jednom mjestu: ćelije, otpori trake, postavke CLONALG-a i seedovi za eksperimente iz članka."""

# ---- ćelije ----
CELL_SPECS = {
    '18650': {'diameter': 18, 'nominal_voltage': 3.6, 'R_cell': 0.07},  # mm, V, Ohm
    '21700': {'diameter': 21, 'nominal_voltage': 3.6, 'R_cell': 0.03},
}
ALLOWED_NET_TYPES = ['saćasti', 'pravokutni']
ALLOWED_CELL_TYPES = ['18650', '21700']

# ---- otpori (električni model, §2.9) ----
RHO_NI = 6.99e-5    # otpornost nikla, Ohm*mm
STRIP_WIDTH = 7     # mm


def strip_r_per_length(thickness_mm, width_mm=STRIP_WIDTH):
    """Otpor niklove trake po mm duljine (Ohm/mm)."""
    return RHO_NI / (thickness_mm * width_mm)


# Tablice 2-4 i Slika 2 (§3.1): R_cell = 50 mOhm, traka 0.3 x 7 mm (33.3 uOhm/mm)
#   3.328e-5 je zaokruženi strip_r_per_length(0.3) = 3.3286e-5; ostavljen jer su s njim izračunati postojeći rezultati
PAPER = {'r_cell': 0.05, 'r_per_length': 3.328e-5}
# Sastavljeni paketi, Tablica 5 (§3.6): izmjereni R_cell = 45 mOhm, traka 0.15 x 7 mm, struja impulsa 2.1 A
ASSEMBLED = {'r_cell': 0.045, 'r_per_length': strip_r_per_length(0.15), 'I': 2.1}

# ---- CLONALG (§2.8, §3.1) ----
# Tablica 2, 3 i 4: T = 500 iteracija, stagnacija 50
CLONALG_PAPER = dict(max_iterations=500, population_size=50, clones_per_antibody=5, d_new_individuals=12, stag_iter=50)
# Slika 3: samo prva faza, stagnacija 100
CLONALG_CONVERGENCE = dict(CLONALG_PAPER, stag_iter=100)

# ---- seedovi: pokretanje k koristi seed SEED_BASE + k ----
SEED_BASE = 100
