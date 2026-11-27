"""Print DC internal resistance measurements (Table 5) from a folder containing
log_ir*.csv files and run.log.

A file with a 'target_time_s' column is a time series; its rows are matched to a
measurement by (timestamp, cell_id), so file names do not have to correspond.

    uv run python experiments/read_measurement.py <measurement_folder>
"""
import csv
import glob
import os
import sys


def show(folder):
    measurements, series = [], {}
    for path in sorted(glob.glob(os.path.join(folder, 'log_ir*.csv'))):
        with open(path) as f:
            reader = csv.DictReader(f)
            is_series = 'target_time_s' in reader.fieldnames
            for r in reader:
                if is_series:
                    series.setdefault((r['timestamp'], r['cell_id']), []).append(r)
                else:
                    measurements.append((path, r))

    for path, r in measurements:
        show_one(path, r, series.get((r['timestamp'], r['cell_id']), []))

    log = os.path.join(folder, 'run.log')
    if os.path.exists(log):
        with open(log) as f:
            for line in f:
                if 'Connected to:' in line or 'SYST:ERR' in line:
                    print('  ' + line.split('] ', 1)[-1].strip())


def show_one(path, r, points):
    print(f"Measurement:   {path}")
    print(f"Time:          {r['timestamp']}")
    print(f"Cell:          {r['cell_id']} ({r['cell_name']})")
    print(f"Pulse:         {float(r['requested_current_A']):g} A, {float(r['actual_pulse_duration_s']):.2f} s")
    print(f"V before:      {float(r['voltage_before_V']):.4f} V")
    print(f"V under load:  {float(r['voltage_loaded_V']):.4f} V")
    print(f"dV / dI:       {float(r['delta_voltage_V']):.4f} V / {float(r['delta_current_A']):.4f} A")
    print(f"DCIR:          {float(r['dcir_mohm']):.2f} mOhm")
    if 'temperature_C' in r:
        print(f"Temperature:   {float(r['temperature_C']):.1f} C")
    else:
        print(f"Temperature:   {float(r['temperature_before_C']):.1f} C -> {float(r['temperature_final_C']):.1f} C")

    for p in points:
        print(f"  after {float(p['target_time_s']):.1f} s: V = {float(p['voltage_V']):.4f} V, "
              f"DCIR = {float(p['dcir_mohm']):.2f} mOhm")
    print()


if __name__ == '__main__':
    show(sys.argv[1])