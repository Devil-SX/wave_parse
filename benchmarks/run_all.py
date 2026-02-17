#!/usr/bin/env python3
"""Master orchestrator for VCD/FST library benchmark suite.

Coordinates test data generation, Python benchmarks (in isolated uv venvs),
and Rust benchmarks. Collects all results and generates a comparison report.

Usage:
    python run_all.py --scale small              # Quick smoke test
    python run_all.py --scale medium             # Standard run
    python run_all.py --scale large              # Extreme test (100MB+ files)
    python run_all.py --scale small --skip-rust  # Python only
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BENCH_DIR = Path(__file__).parent.resolve()
DATA_DIR = BENCH_DIR / "data"
PYTHON_DIR = BENCH_DIR / "python"
RUST_DIR = BENCH_DIR / "rust"
RESULTS_DIR = BENCH_DIR / "results"

# Subprocess timeout per scale (seconds)
SCALE_TIMEOUTS = {"small": 300, "medium": 600, "large": 1200}

# Python benchmarks: (script_name, venv_name, description)
PYTHON_BENCHMARKS = [
    ("bench_vcdvcd.py", ".venv_vcdvcd", "vcdvcd (Python VCD)"),
    ("bench_pylibfst.py", ".venv_pylibfst", "pylibfst (Python FST)"),
    ("bench_pywellen.py", ".venv_pywellen", "pywellen (Python VCD+FST)"),
]


def log(msg):
    print(f"[run_all] {msg}", file=sys.stderr, flush=True)


def run_subprocess(cmd, cwd=None, timeout=600, description=""):
    """Run a subprocess with timeout. Returns (stdout, stderr, returncode)."""
    log(f"  Running: {description or ' '.join(str(c) for c in cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT after {timeout}s: {description}")
        return "", f"TIMEOUT after {timeout}s", -1
    except FileNotFoundError as e:
        log(f"  NOT FOUND: {e}")
        return "", str(e), -2
    except Exception as e:
        log(f"  ERROR: {e}")
        return "", str(e), -3


def ensure_test_data(scale, datagen_python):
    """Generate test data if it doesn't exist."""
    # Check if data files exist for this scale
    vcd_file = DATA_DIR / f"bench_{scale}.vcd"
    fst_file = DATA_DIR / f"bench_{scale}.fst"

    if vcd_file.exists() and fst_file.exists():
        vcd_size = vcd_file.stat().st_size
        fst_size = fst_file.stat().st_size
        log(f"Test data exists: VCD={vcd_size / 1024 / 1024:.1f}MB, FST={fst_size / 1024 / 1024:.1f}MB")
        return True

    log(f"Generating test data for scale={scale}...")
    gen_script = BENCH_DIR / "generate_testdata.py"
    if not gen_script.exists():
        log(f"ERROR: {gen_script} not found")
        return False

    stdout, stderr, rc = run_subprocess(
        [datagen_python, str(gen_script), "--scale", scale, "--data-dir", str(DATA_DIR)],
        timeout=SCALE_TIMEOUTS.get(scale, 600),
        description=f"generate_testdata.py --scale {scale}",
    )
    if stderr:
        for line in stderr.strip().split("\n"):
            log(f"    {line}")
    if stdout:
        for line in stdout.strip().split("\n"):
            log(f"    {line}")

    if rc != 0:
        log(f"WARNING: Data generation returned code {rc}")
    return vcd_file.exists()


def find_datagen_python():
    """Find a Python interpreter that has pyvcd and pylibfst for data generation."""
    # pylibfst venv needs both pyvcd and pylibfst for generating both formats
    for venv in [".venv_pylibfst", ".venv_vcdvcd"]:
        python = PYTHON_DIR / venv / "bin" / "python"
        if python.exists():
            return str(python)
    # Fall back to system python
    return sys.executable


def run_python_benchmarks(scale, timeout):
    """Run all Python benchmark scripts, return list of result dicts."""
    all_results = []

    for script_name, venv_name, description in PYTHON_BENCHMARKS:
        log(f"\n--- Python: {description} ---")

        script_path = PYTHON_DIR / script_name
        if not script_path.exists():
            log(f"  SKIP: {script_path} not found")
            all_results.append({
                "library": description,
                "format": "unknown",
                "results": [{
                    "test": "setup",
                    "scale": scale,
                    "file": "",
                    "file_size_bytes": 0,
                    "times_s": [],
                    "mean_s": 0,
                    "stdev_s": 0,
                    "memory_kb": 0,
                    "status": "error",
                    "error": f"Script not found: {script_path}",
                }],
            })
            continue

        venv_python = PYTHON_DIR / venv_name / "bin" / "python"
        if not venv_python.exists():
            log(f"  SKIP: venv not found at {venv_python}")
            log(f"  Run 'bash benchmarks/python/setup_envs.sh' first")
            all_results.append({
                "library": description,
                "format": "unknown",
                "results": [{
                    "test": "setup",
                    "scale": scale,
                    "file": "",
                    "file_size_bytes": 0,
                    "times_s": [],
                    "mean_s": 0,
                    "stdev_s": 0,
                    "memory_kb": 0,
                    "status": "error",
                    "error": f"venv not found: {venv_python}. Run setup_envs.sh first.",
                }],
            })
            continue

        output_file = RESULTS_DIR / f"{venv_name.strip('.')}.json"

        # Use scale-specific subdirectory if it exists
        scale_data_dir = DATA_DIR / scale
        effective_data_dir = str(scale_data_dir) if scale_data_dir.is_dir() else str(DATA_DIR)

        stdout, stderr, rc = run_subprocess(
            [
                str(venv_python),
                str(script_path),
                "--data-dir", effective_data_dir,
                "--scale", scale,
                "--output", str(output_file),
            ],
            timeout=timeout,
            description=f"{script_name} (scale={scale})",
        )

        if stderr:
            for line in stderr.strip().split("\n"):
                if line.strip():
                    log(f"    {line}")

        if rc == -1:
            # Timeout
            all_results.append({
                "library": description,
                "format": "unknown",
                "results": [{
                    "test": "all",
                    "scale": scale,
                    "file": "",
                    "file_size_bytes": 0,
                    "times_s": [],
                    "mean_s": 0,
                    "stdev_s": 0,
                    "memory_kb": 0,
                    "status": "timeout",
                    "error": f"Subprocess timed out after {timeout}s",
                }],
            })
        elif output_file.exists():
            try:
                with open(output_file) as f:
                    data = json.load(f)
                all_results.append(data)
                ok_count = sum(1 for r in data.get("results", []) if r.get("status") == "ok")
                total = len(data.get("results", []))
                log(f"  Done: {ok_count}/{total} tests passed")
            except json.JSONDecodeError as e:
                log(f"  ERROR parsing output: {e}")
                all_results.append({
                    "library": description,
                    "format": "unknown",
                    "results": [{
                        "test": "parse_output",
                        "scale": scale,
                        "file": "",
                        "file_size_bytes": 0,
                        "times_s": [],
                        "mean_s": 0,
                        "stdev_s": 0,
                        "memory_kb": 0,
                        "status": "error",
                        "error": f"JSON parse error: {e}",
                    }],
                })
        elif stdout.strip():
            # Try parsing stdout as JSON
            try:
                data = json.loads(stdout)
                all_results.append(data)
            except json.JSONDecodeError:
                log(f"  ERROR: no valid JSON output (rc={rc})")
        else:
            log(f"  ERROR: no output (rc={rc})")

    return all_results


def run_rust_benchmarks(scale, timeout):
    """Build and run Rust benchmark, return list of result dicts."""
    log("\n--- Rust benchmarks ---")

    cargo_toml = RUST_DIR / "Cargo.toml"
    if not cargo_toml.exists():
        log(f"  SKIP: {cargo_toml} not found")
        return []

    # Build
    log("  Building (cargo build --release)...")
    stdout, stderr, rc = run_subprocess(
        ["cargo", "build", "--release"],
        cwd=str(RUST_DIR),
        timeout=300,
        description="cargo build --release",
    )
    if rc != 0:
        log(f"  BUILD FAILED (rc={rc})")
        if stderr:
            for line in stderr.strip().split("\n")[-20:]:
                log(f"    {line}")
        return [{
            "library": "rust-all",
            "format": "mixed",
            "results": [{
                "test": "build",
                "scale": scale,
                "file": "",
                "file_size_bytes": 0,
                "times_s": [],
                "mean_s": 0,
                "stdev_s": 0,
                "memory_kb": 0,
                "status": "error",
                "error": f"cargo build failed (rc={rc})",
            }],
        }]

    log("  Build successful")

    # Run
    binary = RUST_DIR / "target" / "release" / "wave-bench"
    if not binary.exists():
        log(f"  ERROR: binary not found at {binary}")
        return []

    # Map scale to timeout for Rust
    scale_timeout_map = {"small": 60, "medium": 120, "large": 300}
    rust_timeout = scale_timeout_map.get(scale, 120)

    # Use scale-specific subdirectory if it exists
    scale_data_dir = DATA_DIR / scale
    effective_data_dir = str(scale_data_dir) if scale_data_dir.is_dir() else str(DATA_DIR)

    env = os.environ.copy()
    env["DATA_DIR"] = effective_data_dir
    env["TIMEOUT"] = str(rust_timeout)
    env["REPS"] = "3"

    log(f"  Running wave-bench (DATA_DIR={DATA_DIR}, TIMEOUT={rust_timeout}s)...")

    try:
        result = subprocess.run(
            [str(binary)],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = result.stdout
        stderr = result.stderr
        rc = result.returncode
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT after {timeout}s")
        return [{
            "library": "rust-all",
            "format": "mixed",
            "results": [{
                "test": "all",
                "scale": scale,
                "file": "",
                "file_size_bytes": 0,
                "times_s": [],
                "mean_s": 0,
                "stdev_s": 0,
                "memory_kb": 0,
                "status": "timeout",
                "error": f"Rust benchmark timed out after {timeout}s",
            }],
        }]

    if stderr:
        for line in stderr.strip().split("\n"):
            if line.strip():
                log(f"    {line}")

    # Parse JSON lines from stdout
    rust_results = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            rust_results.append(obj)
        except json.JSONDecodeError:
            pass

    # Save raw Rust results
    if rust_results:
        rust_output = RESULTS_DIR / "rust_bench.json"
        with open(rust_output, "w") as f:
            json.dump(rust_results, f, indent=2)
        log(f"  Done: {len(rust_results)} benchmark results collected")

    return rust_results


def main():
    parser = argparse.ArgumentParser(description="Run VCD/FST library benchmarks")
    parser.add_argument(
        "--scale",
        choices=["small", "medium", "large"],
        default="small",
        help="Benchmark scale (default: small)",
    )
    parser.add_argument("--skip-python", action="store_true", help="Skip Python benchmarks")
    parser.add_argument("--skip-rust", action="store_true", help="Skip Rust benchmarks")
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Override subprocess timeout in seconds (0=auto based on scale)",
    )
    args = parser.parse_args()

    scale = args.scale
    timeout = args.timeout or SCALE_TIMEOUTS.get(scale, 600)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    log("=" * 60)
    log("VCD/FST Library Benchmark Suite")
    log(f"  Scale: {scale}")
    log(f"  Timeout: {timeout}s")
    log(f"  Data dir: {DATA_DIR}")
    log(f"  Results dir: {RESULTS_DIR}")
    log("=" * 60)

    t_start = time.perf_counter()

    # Step 1: Ensure test data
    log("\n[Step 1] Ensuring test data...")
    datagen_python = find_datagen_python()
    log(f"  Using Python for datagen: {datagen_python}")
    if not ensure_test_data(scale, datagen_python):
        log("WARNING: Test data generation may have failed. Continuing anyway...")

    # Step 2: Python benchmarks
    python_results = []
    if not args.skip_python:
        log("\n[Step 2] Running Python benchmarks...")
        python_results = run_python_benchmarks(scale, timeout)
    else:
        log("\n[Step 2] Skipping Python benchmarks (--skip-python)")

    # Step 3: Rust benchmarks
    rust_results = []
    if not args.skip_rust:
        log("\n[Step 3] Running Rust benchmarks...")
        rust_results = run_rust_benchmarks(scale, timeout)
    else:
        log("\n[Step 3] Skipping Rust benchmarks (--skip-rust)")

    # Step 4: Save combined results
    log("\n[Step 4] Saving results...")
    combined = {
        "scale": scale,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python_results": python_results,
        "rust_results": rust_results,
    }
    combined_path = RESULTS_DIR / f"combined_{scale}.json"
    with open(combined_path, "w") as f:
        json.dump(combined, f, indent=2)
    log(f"  Combined results saved to {combined_path}")

    # Step 5: Generate report
    log("\n[Step 5] Generating report...")
    report_script = BENCH_DIR / "report.py"
    if report_script.exists():
        stdout, stderr, rc = run_subprocess(
            [sys.executable, str(report_script), "--results-dir", str(RESULTS_DIR), "--scale", scale],
            timeout=60,
            description="report.py",
        )
        if stderr:
            for line in stderr.strip().split("\n"):
                if line.strip():
                    log(f"    {line}")
        if rc != 0:
            log(f"  Report generation failed (rc={rc})")
    else:
        log(f"  WARNING: {report_script} not found, skipping report generation")

    elapsed = time.perf_counter() - t_start
    log(f"\n{'=' * 60}")
    log(f"Benchmark complete in {elapsed:.1f}s")
    log(f"Results: {RESULTS_DIR}")
    log(f"{'=' * 60}")


if __name__ == "__main__":
    main()
