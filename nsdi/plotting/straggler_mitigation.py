import json
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import sys
import seaborn as sns
import utils
sns.set_style("white")
sns.set_context("paper", font_scale=1.2,)

"""
    NOTES:
    This experiment examines the increase in mean and p99 latency
    when increasing the size of an ensemble. Each element in the
    ensemble in this experiment was a random forest of depth 16 with
    10 trees trained in Scikit-Learn. The experiment compares two
    latencies. The Clipper latencies are the latency of responses
    returned from Clipper, regardless of whether all the components
    of the ensemble have returned in time. The "Blocking" latency
    measures the latency of the last component in the ensemble to
    return a prediction, and is a measure of the prediction latency
    if Clipper did not return predictions early to meet latency objectives.
    Notably, the prediction load (requested throughput) was set to ensure
    that the blocking latency for an ensemble with one model was well within
    the latency objective. In all experiments the latency objective was
    set to 20ms.


"""

fig_dir = utils.NSDI_FIG_DIR

log_loc = os.path.abspath("../results/straggler_mitigation")
# colors = sns.color_palette("Set1", n_colors=8, desat=.5)
colors = sns.cubehelix_palette(4, start=0.5, rot=-0.75, dark=0.2, light=0.75)

def extract_results(i, df, fname):
    with open(os.path.join(log_loc, fname), "r") as f:
        ensemble_size = int(fname.split("_")[2])
        res = json.load(f)
        clipper_p99 = [m["p99"] for m in res["histograms"] if "prediction_latency" in m["name"]][0] / 1000.0
        blocking_p99 = [m["p99"] for m in res["histograms"] if "straggler_blocking_prediction_latency" in m["name"]][0] / 1000.0
        clipper_mean = [m["mean"] for m in res["histograms"] if "prediction_latency" in m["name"]][0] / 1000.0
        blocking_mean = [m["mean"] for m in res["histograms"] if "straggler_blocking_prediction_latency" in m["name"]][0] / 1000.0
        in_time_mean = 100 - ([m["mean"] for m in res["histograms"] if "in_time_predictions" in m["name"]][0] / float(ensemble_size) * 100)
        in_time_p99 = 100 - ([m["p99"] for m in res["histograms"] if "in_time_predictions" in m["name"]][0] / float(ensemble_size) * 100)
        if ensemble_size < 18:
            df.loc[i] = [ensemble_size, clipper_mean, clipper_p99, blocking_mean, blocking_p99, in_time_mean, in_time_p99]


def plot_line(cur_col, ax, label, color, marker, ls="-"):
    cur_col.plot(y="mean", yerr="std", ax=ax, marker=marker, color=color, ls=ls, label=label)

def plot_straggler_mitigation():
    results_files = utils.get_results_files(log_loc)
    df = pd.DataFrame(columns=("ensemble_size", "clipper_mean_lat", "clipper_p99", "blocking_mean_lat", "blocking_p99", "in_time_mean", "in_time_p99"))
    for (i,r) in enumerate(results_files):
        extract_results(i, df, r)
    df.sort_values("ensemble_size", inplace=True)
    f = {'clipper_mean_lat':['mean','std'],
         'clipper_p99':['mean','std'],
         'blocking_mean_lat':['mean','std'],
         'blocking_p99':['mean','std'],
         'in_time_mean':['mean','std'],
         'in_time_p99':['mean','std'],
         }
    tgs = df.groupby("ensemble_size").agg(f)
    # print tgs.index.values
    # print tgs["clipper_p99","mean"].values
    tgs.columns.get_level_values(0)
    # fig, (ax_lat, ax_in_time) = plt.subplots(ncols=2, sharex=False, figsize=(4,3), gridspec_kw = {'height_ratios':[2, 1.5]})
    fig, (ax_lat, ax_in_time) = plt.subplots(ncols=2, sharex=False, figsize=(6,2))

    plot_line(tgs["clipper_p99"], ax_lat, "No Stragglers P99", colors[0], "o")
    plot_line(tgs["clipper_mean_lat"], ax_lat, "No Stragglers Mean", colors[0], "o", ls="--")
    plot_line(tgs["blocking_p99"], ax_lat, "Stragglers P99", colors[2], "v")
    plot_line(tgs["blocking_mean_lat"], ax_lat, "Stragglers Mean", colors[2], "v", ls="--")
    plot_line(tgs["in_time_mean"], ax_in_time, "P99", colors[1], None)
    plot_line(tgs["in_time_p99"], ax_in_time, "Mean", colors[1], None, ls="--")
    # print(tgs["blocking_mean_lat"]["mean"])
    ax_lat.legend(loc=0, ncol=1)
    ax_lat.set_ylim(0, 400)
    ax_lat.set_ylabel("Latency (ms)")
    ax_lat.set_xlabel("Size of ensemble")
    ax_in_time.set_ylabel("% Ensemble Missing")
    ax_in_time.set_xlabel("Size of ensemble")
    ax_in_time.set_ylim(0, 100)
    fig.subplots_adjust(wspace=0.3)
    fname = "%s/straggler_mitigation.pdf" % (fig_dir)
    plt.savefig(fname, bbox_inches='tight')
    print(fname)

    
if __name__=="__main__":
    plot_straggler_mitigation()
