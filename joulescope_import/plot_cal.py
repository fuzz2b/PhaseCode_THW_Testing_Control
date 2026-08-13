# Copyright 2019 Jetperch LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#python another_js_tool.py --contiguous 0.5 --plot  

"""Plot calibrated data (This was altered from something from Joulescopes library)"""

import matplotlib.pyplot as plt
import numpy as np
import os
import psutil
import csv


def plot_axis(axis, x, y, label=None):
    if label is not None:
        axis.set_ylabel(label)
    axis.grid(True)
    axis.plot(x, y)
    # draw vertical lines at start/end of NaN region
    yvalid = np.isfinite(y)
    diffs = np.diff(yvalid)
    for line in x[np.nonzero(diffs)]:
        axis.axvline(line, color='red')
    is_nan = np.logical_not(yvalid)
    nan_padded = np.concatenate(([False], is_nan, [False]))
    idx = np.flatnonzero(nan_padded[1:] != nan_padded[:-1])
    
    # Pair up start and end indices to create shaded regions
    for start, end in zip(idx[::2], idx[1::2]):
        x_start = x[start]
        x_end = x[min(end, len(x) - 1)]
        axis.axvspan(x_start, x_end, facecolor='red', alpha=0.5)
    return axis


def plot_iv(data, sampling_frequency, show=None):
    x = np.arange(len(data), dtype=float)
    x *= 1.0 / sampling_frequency
    f = plt.figure()
    ax_i = f.add_subplot(2, 1, 1)
    plot_axis(ax_i, x, data[:, 0], label='Current (A)')
    ax_v = f.add_subplot(2, 1, 2, sharex=ax_i)
    plot_axis(ax_v, x, data[:, 1], label='Voltage (V)')
    if show is None or bool(show):
        plt.show()
        plt.close(f)


def export_csv(data, sampling_frequency, filepath='output.csv'):
    """
    Export current and voltage data to a CSV file.

    numpy array of shape (N, 2) where column 0 is current (A) and column 1 is 
    voltage (V).
    """
    # export_csv(data, sampling_frequency, filepath='my_data.csv')
    x = np.arange(len(data), dtype=float) / sampling_frequency

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_s', 'current_A', 'voltage_V'])
        for t, row in zip(x, data):
            writer.writerow([t, row[0], row[1]])
    print(f'Exported {len(data)} rows to {filepath}')


def memory():
    return psutil.Process(os.getpid()).memory_info().rss  # in bytes


def print_stats(data, sampling_frequency):
    mem = memory() / 2e6
    print(f'Memory usage: {mem:.1f} MB')
    is_finite = np.isfinite(data[:, 0])
    duration = len(data) / sampling_frequency
    finite = np.count_nonzero(is_finite)
    total = len(data)
    nonfinite = total - finite
    print(f'found {nonfinite} NaN out of {total} samples ({duration:.3f} seconds)')
    is_finite[0], is_finite[-1] = True, True  # force counting at start and end
    nan_edges = np.nonzero(np.diff(is_finite))[0]
    nan_runs = len(nan_edges) // 2
    if nan_runs:
        print(f'nan edges: {nan_edges.reshape((-1, 2))}')
        nan_edge_lengths = nan_edges[1::2] - nan_edges[0::2]
        run_mean = np.mean(nan_edge_lengths)
        run_std = np.std(nan_edge_lengths)
        run_min = np.min(nan_edge_lengths)
        run_max = np.max(nan_edge_lengths)
        print(f'found {nan_runs} NaN runs: {run_mean} mean, {run_std} std, {run_min} min, {run_max} max')


if __name__ == '__main__':
    plot_iv()
    plot_axis()