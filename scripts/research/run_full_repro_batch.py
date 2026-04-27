from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class RunResult:
    kind: str
    name: str
    source: str
    output: str
    status: str
    returncode: int
    duration_sec: float
    log_file: str
    error_tail: str


def _load_previous_results(summary_path: Path) -> dict[tuple[str, str], dict]:
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    results = payload.get("results", [])
    if not isinstance(results, list):
        return {}

    out: dict[tuple[str, str], dict] = {}
    for r in results:
        if not isinstance(r, dict):
            continue
        kind = r.get("kind")
        name = r.get("name")
        if isinstance(kind, str) and isinstance(name, str):
            out[(kind, name)] = r
    return out


def _default_window_features_path(repo_root: Path) -> Path:
    candidates = [
        repo_root / "data" / "picoclimate_test" / "window_features.csv",
        repo_root / "data" / "window_features.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "Could not find a default window_features.csv. Checked: " + ", ".join(str(p) for p in candidates)
    )


def _run_command(cmd: List[str], cwd: Path, log_file: Path, timeout: int = 7200) -> tuple[int, float, str]:
    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=os.environ.copy(),
    )
    duration = time.time() - start

    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("w", encoding="utf-8") as f:
        f.write("$ " + " ".join(cmd) + "\n\n")
        f.write("[stdout]\n")
        f.write(proc.stdout or "")
        f.write("\n\n[stderr]\n")
        f.write(proc.stderr or "")

    tail = ""
    if proc.returncode != 0:
        err_text = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = "\n".join(err_text[-8:])

    return proc.returncode, duration, tail


def _collect_figure_files(repo_root: Path, out_root: Path, start_epoch: float) -> list[dict]:
    figures_dir = out_root / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    exts = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".webp", ".gif"}
    scan_roots = [
        repo_root / "outputs",
        repo_root / "docs" / "slides" / "2026-04-24" / "figures",
    ]

    copied = []
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in exts:
                continue
            if figures_dir in path.parents:
                continue

            include = False
            if str(out_root) in str(path):
                include = True
            elif root.name == "outputs" and path.stat().st_mtime >= (start_epoch - 120):
                include = True
            elif "docs/slides/2026-04-24/figures" in str(path).replace("\\", "/"):
                include = True

            if not include:
                continue

            rel = path.relative_to(repo_root)
            target = figures_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

            copied.append(
                {
                    "source": str(rel).replace("\\", "/"),
                    "target": str(target.relative_to(repo_root)).replace("\\", "/"),
                    "bytes": int(path.stat().st_size),
                    "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                }
            )

    copied.sort(key=lambda x: x["source"])
    manifest_csv = out_root / "figures_manifest.csv"
    with manifest_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "target", "bytes", "mtime"])
        writer.writeheader()
        writer.writerows(copied)

    return copied


def main() -> int:
    python_exe = Path(sys.executable)
    repo_root = Path(__file__).resolve().parents[2]
    date_tag = datetime.now().strftime("%Y-%m-%d")

    out_root = repo_root / "outputs" / date_tag
    notebooks_out = out_root / "notebooks"
    logs_out = out_root / "logs"

    out_root.mkdir(parents=True, exist_ok=True)
    notebooks_out.mkdir(parents=True, exist_ok=True)
    logs_out.mkdir(parents=True, exist_ok=True)

    summary_path = out_root / "execution_summary.json"
    prev_results = _load_previous_results(summary_path) if summary_path.exists() else {}

    batch_start = time.time()

    notebook_files = sorted((repo_root / "scripts" / "notebooks").glob("*.ipynb"))
    script_files = sorted((repo_root / "scripts" / "research").glob("*.py"))
    script_files = [p for p in script_files if p.name != Path(__file__).name]

    results: list[RunResult] = []

    for nb in notebook_files:
        output_name = f"{nb.stem}.executed.ipynb"
        log_file = logs_out / f"notebook__{nb.stem}.log"
        output_path = notebooks_out / output_name

        prev = prev_results.get(("notebook", nb.name))
        if prev and prev.get("status") == "ok" and output_path.exists():
            results.append(
                RunResult(
                    kind="notebook",
                    name=nb.name,
                    source=str(nb.relative_to(repo_root)).replace("\\", "/"),
                    output=str(output_path.relative_to(repo_root)).replace("\\", "/"),
                    status="skipped",
                    returncode=0,
                    duration_sec=0.0,
                    log_file=str(prev.get("log_file", str(log_file.relative_to(repo_root)).replace("\\", "/"))),
                    error_tail="Previously ok; skipped",
                )
            )
            continue

        cmd = [
            str(python_exe),
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            str(nb),
            "--output",
            output_name,
            "--output-dir",
            str(notebooks_out),
            "--ExecutePreprocessor.timeout=3600",
            f"--ExecutePreprocessor.cwd={repo_root}",
        ]

        try:
            rc, dur, tail = _run_command(cmd, repo_root, log_file)
        except subprocess.TimeoutExpired:
            rc, dur, tail = 124, 7200.0, "Timed out after 7200 seconds"
            with log_file.open("w", encoding="utf-8") as f:
                f.write("$ " + " ".join(cmd) + "\n\n")
                f.write("[error]\nTimed out after 7200 seconds\n")

        results.append(
            RunResult(
                kind="notebook",
                name=nb.name,
                source=str(nb.relative_to(repo_root)).replace("\\", "/"),
                output=str(output_path.relative_to(repo_root)).replace("\\", "/"),
                status="ok" if rc == 0 else "failed",
                returncode=rc,
                duration_sec=round(dur, 2),
                log_file=str(log_file.relative_to(repo_root)).replace("\\", "/"),
                error_tail=tail,
            )
        )

    research_out = out_root / "research"
    research_out.mkdir(parents=True, exist_ok=True)
    default_data = _default_window_features_path(repo_root)

    for script in script_files:
        log_file = logs_out / f"script__{script.stem}.log"

        prev = prev_results.get(("script", script.name))
        if prev and prev.get("status") == "ok":
            results.append(
                RunResult(
                    kind="script",
                    name=script.name,
                    source=str(script.relative_to(repo_root)).replace("\\", "/"),
                    output=str(prev.get("output", "")),
                    status="skipped",
                    returncode=0,
                    duration_sec=0.0,
                    log_file=str(prev.get("log_file", str(log_file.relative_to(repo_root)).replace("\\", "/"))),
                    error_tail="Previously ok; skipped",
                )
            )
            continue

        script_output = ""
        cmd = [str(python_exe), str(script)]
        if script.name != "shapelet_stability.py":
            script_out = research_out / script.stem
            script_out.mkdir(parents=True, exist_ok=True)
            script_output = str(script_out.relative_to(repo_root)).replace("\\", "/")
            cmd += ["--data", str(default_data), "--outdir", str(script_out)]

        try:
            rc, dur, tail = _run_command(cmd, repo_root, log_file)
        except subprocess.TimeoutExpired:
            rc, dur, tail = 124, 7200.0, "Timed out after 7200 seconds"
            with log_file.open("w", encoding="utf-8") as f:
                f.write("$ " + " ".join(cmd) + "\n\n")
                f.write("[error]\nTimed out after 7200 seconds\n")

        results.append(
            RunResult(
                kind="script",
                name=script.name,
                source=str(script.relative_to(repo_root)).replace("\\", "/"),
                output=script_output,
                status="ok" if rc == 0 else "failed",
                returncode=rc,
                duration_sec=round(dur, 2),
                log_file=str(log_file.relative_to(repo_root)).replace("\\", "/"),
                error_tail=tail,
            )
        )

    copied_figures = _collect_figure_files(repo_root, out_root, batch_start)

    summary = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "python_executable": str(python_exe),
        "repo_root": str(repo_root),
        "out_root": str(out_root),
        "notebooks_total": len([r for r in results if r.kind == "notebook"]),
        "scripts_total": len([r for r in results if r.kind == "script"]),
        "ok_total": len([r for r in results if r.status == "ok"]),
        "skipped_total": len([r for r in results if r.status == "skipped"]),
        "failed_total": len([r for r in results if r.status == "failed"]),
        "figures_exported": len(copied_figures),
        "results": [asdict(r) for r in results],
    }

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    failed = [r for r in results if r.status == "failed"]

    print(f"Run root: {out_root}")
    print(f"Notebooks: {summary['notebooks_total']}, Scripts: {summary['scripts_total']}")
    print(f"Success: {summary['ok_total']}, Skipped: {summary['skipped_total']}, Failed: {summary['failed_total']}")
    print(f"Figures exported: {summary['figures_exported']}")
    print(f"Summary file: {summary_path}")

    if failed:
        print("Failed tasks:")
        for r in failed:
            print(f"- [{r.kind}] {r.name} (rc={r.returncode})")
            if r.error_tail:
                print("  " + r.error_tail.replace("\n", "\n  "))

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
