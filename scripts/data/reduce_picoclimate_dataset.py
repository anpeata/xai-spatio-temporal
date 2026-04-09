"""Reduce a generated picoclimate dataset size (e.g., by half).

This utility keeps the *same schema* but reduces the number of raw samples
by taking every N-th sample per device (time-ordered), then recomputes
`window_features.csv` from the reduced raw measurements.

Typical use (half the data, in-place):
    python scripts/data/reduce_picoclimate_dataset.py \
        --data-dir data --keep-every 2 --inplace

Notes
- This is designed for the synthetic dataset produced by generate_picoclimate_data.py
- The data directory is ignored by git in this repo.

"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import importlib.util

import pandas as pd


def _load_generator_module(gen_path: Path):
    spec = importlib.util.spec_from_file_location("picoclimate_generator", gen_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import generator from: {gen_path}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses (and other stdlib) expect the module to exist in sys.modules
    # during execution when resolving annotations.
    sys.modules[module.__name__] = module
    spec.loader.exec_module(module)
    return module


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Reduce synthetic picoclimate dataset size")
    p.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory containing raw_measurements.csv and metadata.json (e.g. data)",
    )
    p.add_argument(
        "--keep-every",
        type=int,
        default=2,
        help="Keep every N-th sample per location (2 ≈ half the samples)",
    )
    p.add_argument(
        "--window-seconds",
        type=int,
        default=120,
        help="Window size to recompute window_features.csv",
    )
    p.add_argument(
        "--inplace",
        action="store_true",
        help="Overwrite files in --data-dir. If not set, writes into a sibling folder named '<data-dir>_reduced'.",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    data_dir = Path(args.data_dir)
    keep_every = int(args.keep_every)

    if keep_every <= 0:
        raise SystemExit("--keep-every must be > 0")

    raw_path = data_dir / "raw_measurements.csv"
    if not raw_path.exists():
        raise SystemExit(f"Missing file: {raw_path}")

    # Resolve output dir
    if args.inplace:
        out_dir = data_dir
    else:
        out_dir = data_dir.parent / f"{data_dir.name}_reduced"
        out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading: {raw_path}")
    raw = pd.read_csv(raw_path)

    if "timestamp" not in raw.columns or "location_id" not in raw.columns:
        raise SystemExit("raw_measurements.csv must contain 'timestamp' and 'location_id'")

    raw["timestamp"] = pd.to_datetime(raw["timestamp"], utc=True, errors="coerce")
    raw = raw.sort_values(["location_id", "timestamp"], kind="mergesort")

    reduced = raw.groupby("location_id", group_keys=False).apply(lambda g: g.iloc[::keep_every])
    reduced = reduced.reset_index(drop=True)

    out_raw = out_dir / "raw_measurements.csv"
    print(f"Writing reduced raw: {out_raw} (rows: {len(reduced):,} from {len(raw):,})")
    reduced.to_csv(out_raw, index=False)

    # Recompute window_features using the generator's implementation
    gen_path = Path(__file__).with_name("generate_picoclimate_data.py")
    gen = _load_generator_module(gen_path)

    out_win = out_dir / "window_features.csv"
    print(f"Recomputing window features -> {out_win}")
    if hasattr(gen, "_build_window_features"):
        win = gen._build_window_features(reduced)
    elif hasattr(gen, "_window_features"):
        win = gen._window_features(reduced, window_seconds=int(args.window_seconds))
    else:
        raise RuntimeError("No compatible window feature builder found in generate_picoclimate_data.py")
    win.to_csv(out_win, index=False)

    # Update metadata (copy + annotate)
    meta_in = data_dir / "metadata.json"
    out_meta = out_dir / "metadata.json"
    meta: Dict[str, Any] = {}
    if meta_in.exists():
        try:
            meta = json.loads(meta_in.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

    meta.setdefault("reductions", [])
    meta["reductions"].append(
        {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "method": "keep_every_n_per_location",
            "keep_every": keep_every,
            "original_rows": int(len(raw)),
            "reduced_rows": int(len(reduced)),
            "window_seconds": int(args.window_seconds),
        }
    )

    out_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote metadata: {out_meta}")


if __name__ == "__main__":
    main()
