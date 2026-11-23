"""Ispis jednog mjerenja DC unutarnjeg otpora (Tablica 5) iz mape s log_ir.csv, log_ir_timeseries.csv i run.log.

    uv run python experiments/read_measurement.py <mapa_mjerenja>
"""
import csv
import os
import sys


def show(folder):
    with open(os.path.join(folder, 'log_ir.csv')) as f:
        r = next(csv.DictReader(f))
    print(f"Mjerenje:      {folder}")
    print(f"Vrijeme:       {r['timestamp']}")
    print(f"Oznaka:        {r['cell_id']} ({r['cell_name']})")
    print(f"Impuls:        {float(r['requested_current_A']):g} A, {float(r['actual_pulse_duration_s']):.2f} s")
    print(f"Napon prije:   {float(r['voltage_before_V']):.4f} V")
    print(f"Napon pod opt: {float(r['voltage_loaded_V']):.4f} V")
    print(f"dV / dI:       {float(r['delta_voltage_V']):.4f} V / {float(r['delta_current_A']):.4f} A")
    print(f"DCIR:          {float(r['dcir_mohm']):.2f} mOhm")
    print(f"Temperatura:   {float(r['temperature_C']):.1f} C")

    ts = os.path.join(folder, 'log_ir_timeseries.csv')
    if os.path.exists(ts):
        with open(ts) as f:
            for p in csv.DictReader(f):
                print(f"  nakon {float(p['target_time_s']):.1f} s: V = {float(p['voltage_V']):.4f} V, "
                      f"DCIR = {float(p['dcir_mohm']):.2f} mOhm")

    log = os.path.join(folder, 'run.log')
    if os.path.exists(log):
        with open(log) as f:
            for line in f:
                if 'Connected to:' in line or 'SYST:ERR' in line:
                    print('  ' + line.split('] ', 1)[-1].strip())


if __name__ == '__main__':
    show(sys.argv[1])