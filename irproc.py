# (C) Alexander S. Shved and the Denmark Laboratory

"""
    This file has a set of tools for quick IR processing
"""

import numpy as np
import pandas as pd
from argparse import ArgumentParser
from glob import glob
import os
from sys import stderr, stdout
from matplotlib import pyplot as plt, rc_context
from scipy.signal import find_peaks

parser = ArgumentParser(
    description="Quick IR processing tools. Default parameters should be universally useful, but this CLI allows the user to vary those according to their own needs. By default, the transmittance data is normalized."
)

MPL_DEFAULT_PARAM = {
    "font.family": "sans-serif",
    "font.sans-serif": "Arial",
    "mathtext.fontset": "stixsans",
    "font.size": 8.0,
    "figure.figsize": (8, 4),
    "lines.linewidth": 0.75,
    "axes.linewidth": 0.5,
    "axes.spines.top": True,
    "axes.spines.right": True,
    "xtick.major.width": 0.5,
    "xtick.minor.width": 0.5,
    "xtick.major.size": 5,
    "xtick.minor.size": 2,
    "xtick.minor.visible": False,
    "xtick.direction": "in",
    "ytick.major.width": 0.5,
    "ytick.minor.width": 0.5,
    "ytick.major.size": 5,
    "ytick.minor.size": 2,
    "ytick.minor.visible": False,
    "ytick.direction": "in",
}

parser.add_argument(
    "files",
    nargs="+",
    metavar="file_name",
    help="List of files (or wildcard patterns) to process",
)

parser.add_argument(
    "-o",
    "--output",
    metavar="file_name",
    action="store",
    default=None,
    help="File that the IR writeup should be saved to. If not specified, output will be produced in STDOUT",
)

parser.add_argument(
    "-p",
    "--plot",
    metavar="*.svg",
    action="store",
    default="{FILENAME}.svg",
    type=str,
    help="This is used to specify a pattern that determines where the plot files. Star will be replaced with the actual file name. File extension determines the output",
)

parser.add_argument(
    "-m",
    "--mpl_param",
    metavar="mpl.par",
    type=str,
    help="Pass a matplotlib parameter file for plot customization",
)

parser.add_argument(
    "-bw",
    "--broad_peak_min_width",
    metavar="100",
    default=100.0,
    type=float,
    help="Width of a peak (in cm**-1) to be considered broad.",
)

parser.add_argument(
    "-pd",
    "--peak_min_distance",
    metavar="30",
    default=30.0,
    type=float,
    help="Minimal distance between the peaks (in cm**-1). If multiple peaks are within reach, only the highest intensity is considered viable",
)

parser.add_argument(
    "-pw",
    "--peak_min_width",
    metavar="4",
    default=4,
    type=float,
    help="Minimal FWHM (in cm**-1) of the peak to be considered real.",
)

parser.add_argument(
    "-pr",
    "--peak_min_prominence",
    metavar="5",
    default=5.0,
    type=float,
    help="Minimal prominence of the peak (in %%T).",
)

parser.add_argument(
    "--dpi",
    metavar="600",
    action="store",
    type=int,
    default=600,
    help="Determines the resolution for raster image outputs. Ignored if SVG is requested.",
)

parser.add_argument(
    "--raw",
    action="store_true",
    help="Raw values of transmittance will be used (i. e. the data won't be normalized to the most intense peak in the spectrum. DO NOT USE unless you are certain of what you are doing.",
)


def get_all_files(file_args: list):
    """
    Figure out a complete list of files to process based on the list
    """
    all_files = []
    for f in file_args:
        all_files.extend(glob(f))

    return all_files


def process_file(file_name: str, normalize=True):
    """
    Break down the file into x and y value arrays
    """
    # Default CSV file reader

    data = pd.read_csv(file_name, header=1, index_col=False)
    ir_w = data["cm-1"].to_numpy()
    ir_t_raw = data["%T"].to_numpy()

    if normalize:
        ir_inv = 100.0 - ir_t_raw
        ir_t = 100 - 100 * ir_inv / np.max(ir_inv)
    else:
        ir_t = ir_t_raw

    return ir_w, ir_t


def desc(trel: float, w: float, br_w: float = 100, sep: str = " "):
    """
    Describe a peak based on transmittance and width
    """
    res = []
    if 0 <= trel <= 33:
        res.append("s")
    elif 33 < trel < 66:
        res.append("m")
    elif 66 < trel <= 100:
        res.append("w")
    else:
        raise ValueError

    if w > br_w:
        res.append("br")

    return "(" + sep.join(res) + ")"


def ms_report(ir_w, ir_t, prominence=2, width=2, distance=20, br_w=100, sep: str = " "):
    """ """

    peaks, pkinfo = find_peaks(
        100 - ir_t, prominence=prominence, width=width, distance=distance
    )

    widths = pkinfo["widths"]

    w_av = np.average(widths)
    w_std = np.std(widths)

    for i, p in enumerate(peaks):
        de = desc(ir_t[p], widths[i], br_w)
        yield (p, de)


def generate_report(
    fname: str,
    normalize=True,
    prominence: float = 2.0,
    width: float = 4.0,
    broad_width: float = 100.0,
    distance: float = 25,
):
    """
    This function generates full report
    """
    x, y = process_file(fname, normalize=True)
    peaks = ms_report(
        x, y, prominence=prominence, width=width, distance=distance, br_w=broad_width
    )

    plt.figure()
    ax: plt.Axes = plt.axes()

    report = []

    for i, pk in enumerate(peaks):
        p, d = pk
        ax.vlines(x[p], y[p] - 3, y[p] - 7, linewidths=0.5, colors=(0.0, 0.0, 0.0))
        ax.text(
            x[p],
            y[p] - 8,
            f"{x[p]:.0f} {d[1:-1]}",
            verticalalignment="top",
            horizontalalignment="center",
            rotation=90,
            fontsize=7,
        )
        report.append(f"{x[p]:.0f} {d}")

    ax.plot(x, y, color=(0.0, 0.0, 0.3))
    # ax.set_xlim(np.max(x), np.min(x))

    ax.set_title(fname, loc="left")

    y_ticks = np.linspace(0, 100, 11)
    ax.set_xscale("log")
    ax.set_ylim(-20, 100)
    ax.set_yticks(y_ticks)

    ax.set_ylabel("% Transmittance (normalized)")

    x_ticks = np.linspace(4000, 500, num=8, dtype="int")
    ax.set_xticks(x_ticks)
    ax.xaxis.tick_top()
    ax.set_xticklabels(x_ticks)
    ax.set_xlim(4000, 450)

    ax.set_xlabel(r"Wavenumber [$\mathrm{cm}^{-1}$]")
    ax.xaxis.set_label_position("top")

    plt.tight_layout()

    return report


def main():
    print("=" * 80, file=stderr)
    print("IR Spectral Processing (C) Alexander Shved and the Denmark Lab", file=stderr)
    print("=" * 80, file=stderr)
    parsed = parser.parse_args()
    all_files = get_all_files(parsed.files)

    if parsed.output:
        outstream = open(parsed.output, "at")
    else:
        outstream = stdout

    if not all_files:
        print("No valid files to process. Exiting...", file=stderr)
        exit(1)
    else:
        print(f"Requested to process {len(all_files)} files.")

    with rc_context(MPL_DEFAULT_PARAM, fname=parsed.mpl_param):
        for f in all_files:
            fname = f.removesuffix(".csv")

            print(f">>> {os.path.abspath(f)}", file=outstream)
            ir_w, ir_t = process_file(f)

            report = generate_report(
                f,
                normalize=~parsed.raw,
                prominence=parsed.peak_min_prominence,
                width=parsed.peak_min_width,
                broad_width=parsed.broad_peak_min_width,
                distance=parsed.peak_min_distance,
            )
            print("Plot", f, "-->", parsed.plot.format(FILENAME=fname), file=stderr)

            # plt.savefig(parsed.plot.replace("*", fname), dpi=parsed.dpi)

            _rep = ", ".join(report)
            print(f"IR (ATR): {_rep}.", file=outstream)


if __name__ == "__main__":
    main()
