


"""
Companion to set_power_prebias.py

After capture, a plot opens. Use the normal matplotlib toolbar to
zoom/pan to wherever, then click the point where the current has settled 
(that's t0).
Use:
    python long_measure_thw.py --contiguous 60 --plot (for 60 seconds)
"""

import os
import argparse
import logging
import sys
import time
import csv

import numpy as np
import matplotlib.pyplot as plt  # Requires interactive backend (Qt/Tk) for pick_t0()

from joulescope import scan_require_one

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from joulescope_import.plot_cal import plot_iv

DURATION_MAX = 120  # in seconds


def float_or_none(x):
    if x is None:
        return None
    return float(x)


def get_parser():
    p = argparse.ArgumentParser(
        description='Read data from Joulescope for a pre-biased THW step test, '
                    'then manually pick t0 from a plot.')
    p.add_argument('--duration', '-d',
                    type=float_or_none,
                    help='The capture duration in seconds.')
    p.add_argument('--contiguous', '-c',
                    type=float_or_none,
                    help='The contiguous capture duration in seconds (no missing samples).')
    p.add_argument('--plot',
                    action='store_true',
                    help='Also show the full plot_iv() summary plot after t0 selection.')
    p.add_argument('--out-prefix', type=str, default='thw_run',
                    help='Filename prefix for the exported CSV.')
    return p


def pick_t0(t, current):

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(t, current, '-', lw=0.8, color='darkorange')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Current (A)')
    ax.grid(True)
    ax.set_title('Zoom/pan with the toolbar, then click where current has settled (t0).')

    picked = {}
    vline_holder = {}

    def on_click(event):

        if fig.canvas.toolbar is not None and fig.canvas.toolbar.mode != '':
            return
        if event.inaxes != ax or event.xdata is None:
            return
        picked['t'] = event.xdata
        if 'line' in vline_holder:
            vline_holder['line'].remove()
        vline_holder['line'] = ax.axvline(event.xdata, color='red', linestyle='--')
        ax.set_title(f'Selected t0 = {event.xdata:.6f} s. Click again to change it, '
                      f'or close the window to confirm.')
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect('button_press_event', on_click)



    plt.show()

    return picked.get('t', None)


def export_csv_with_t0(t, current, voltage, filepath, step_idx):
    """
    Writes time_s, t_rel_to_step_s, is_post_step, current_A, voltage_V.
    If step_idx is None (no point was picked), t_rel_to_step_s is left
    blank and is_post_step is False for every row.
    """
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_s', 't_rel_to_step_s', 'is_post_step', 'current_A', 'voltage_V'])
        for i in range(len(t)):
            if step_idx is None:
                t_rel = ''
                is_post = False
            else:
                t_rel = t[i] - t[step_idx]
                is_post = i >= step_idx
            writer.writerow([t[i], t_rel, is_post, current[i], voltage[i]])
    print(f'Exported {len(t)} rows to {filepath}')


def run():
    args = get_parser().parse_args()
    buffer_duration = args.contiguous
    if buffer_duration is None:
        buffer_duration = args.duration
    if buffer_duration is not None:
        if buffer_duration > DURATION_MAX:
            print(f'To capture more than {DURATION_MAX} seconds, see the read_by_callback.py example')
            return 1

    device = scan_require_one(config='auto')
    if buffer_duration is not None:
        device.parameter_set('buffer_duration', round(buffer_duration * 1.01 + 0.501))

    with device:
        device.stream_buffer.suppress_mode = 'off'
        print('READY', flush=True)

        logging.info('read start')
        data = device.read(duration=args.duration, contiguous_duration=args.contiguous)
        logging.info('read done')

    print(f'READY at {time.time()}', flush=True)

    fs = device.sampling_frequency
    n = len(data)
    t = np.arange(n, dtype=float) / fs
    current = data[:, 0]
    voltage = data[:, 1]

    print('Capture done. Opening plot for t0 selection...')
    clicked_t = pick_t0(t, current)

    if clicked_t is None:
        step_idx = None
        print('No t0 selected (window closed without a click). Proceeding without one')
    else:
        step_idx = int(np.argmin(np.abs(t - clicked_t)))
        print(f'Selected t0: sample {step_idx}, t = {t[step_idx]:.6f} s into this capture.')

    csv_path = f'{args.out_prefix}.csv'
    export_csv_with_t0(t, current, voltage, csv_path, step_idx)

    if args.plot:
        plot_iv(data, fs)

    return 0


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(name)s %(message)s', level=logging.INFO)
    sys.exit(run() or 0)