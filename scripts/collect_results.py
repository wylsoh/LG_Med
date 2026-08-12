"""
Collect experiment results from training logs / lightning metrics CSV.

Usage:
    python scripts/collect_results.py                 # all configs under config/exp
    python scripts/collect_results.py config/exp/full.yaml
    python scripts/collect_results.py --json out.json

For each experiment it prints the best validation epoch (by val_loss) and the
corresponding dice / MIoU / acc, plus the latest training run info.
"""

import argparse
import glob
import json
import os
import re

import pandas as pd


def best_val_from_metrics_csv(csv_path):
    """Return dict with best val_dice / val_MIoU / val_acc / val_loss rows."""
    if not os.path.isfile(csv_path):
        return None
    df = pd.read_csv(csv_path)
    val = df.dropna(subset=["val_loss"])
    if val.empty:
        return None
    best = val.loc[val["val_loss"].idxmin()]
    out = {
        "best_val_loss": float(best["val_loss"]),
        "best_val_dice": float(best["val_dice"]),
        "best_val_MIoU": float(best["val_MIoU"]),
        "best_val_acc": float(best["val_acc"]),
        "best_val_epoch": int(best["epoch"]),
    }
    # also max dice epoch
    dice = val.loc[val["val_dice"].idxmax()]
    out["max_dice_epoch"] = int(dice["epoch"])
    out["max_dice"] = float(dice["val_dice"])
    out["max_MIoU"] = float(dice["val_MIoU"])
    out["n_epochs_run"] = int(val["epoch"].max())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("configs", nargs="*", help="config paths (default: all under config/exp)")
    ap.add_argument("--json", default=None, help="optional json output path")
    args = ap.parse_args()

    cfg_root = os.path.join(os.path.dirname(__file__), "..", "config", "exp")
    if args.configs:
        cfgs = args.configs
    else:
        cfgs = sorted(glob.glob(os.path.join(cfg_root, "*.yaml")))

    rows = []
    for cfg in cfgs:
        name = os.path.splitext(os.path.basename(cfg))[0]
        # find the lightning_logs/version_* that used this config (match by checkpoint name)
        metric_paths = sorted(glob.glob("lightning_logs/version_*/metrics.csv"),
                              key=lambda p: os.path.getmtime(p), reverse=True)
        best = None
        for mp in metric_paths:
            # verify hparams match this config name (checkpoint filename)
            hp = os.path.join(os.path.dirname(mp), "hparams.yaml")
            if os.path.isfile(hp) and name in open(hp).read():
                best = best_val_from_metrics_csv(mp)
                break
        rows.append({"config": name, **({} if best is None else best)})

    df = pd.DataFrame(rows)
    cols = ["config", "best_val_loss", "best_val_dice", "best_val_MIoU",
            "best_val_acc", "best_val_epoch", "max_dice_epoch", "max_dice",
            "max_MIoU", "n_epochs_run"]
    print(df.to_string(index=False))

    if args.json:
        with open(args.json, "w") as f:
            json.dump(rows, f, indent=2, default=str)
        print(f"\n[collect_results] saved -> {args.json}")


if __name__ == "__main__":
    main()
