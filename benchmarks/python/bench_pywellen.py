#!/usr/bin/env python3
"""Benchmark script for pywellen library (VCD and FST format parsing via wellen Rust bindings)."""

import argparse
import gc
import json
import os
import resource
import signal
import statistics
import sys
import time


SCALE_TIMEOUTS = {"small": 60, "medium": 120, "large": 300}
REPETITIONS = 3


class TimeoutError(Exception):
    pass


def _timeout_handler(signum, frame):
    raise TimeoutError("Test timed out")


def get_peak_rss_kb():
    """Return peak RSS in KB from resource.getrusage."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss


def find_waveform_files(data_dir, scale):
    """Find VCD and FST files in the data directory for the given scale."""
    scale_dir = os.path.join(data_dir, scale)
    if not os.path.isdir(scale_dir):
        scale_dir = data_dir
    vcd_files = []
    fst_files = []
    for f in sorted(os.listdir(scale_dir)):
        full = os.path.join(scale_dir, f)
        if f.endswith(".vcd"):
            vcd_files.append(full)
        elif f.endswith(".fst"):
            fst_files.append(full)
    return vcd_files, fst_files


def run_test(test_func, timeout_s):
    """Run a test function with timeout, return (elapsed_s, peak_rss_kb) or raise."""
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout_s)
    try:
        gc.collect()
        rss_before = get_peak_rss_kb()
        t0 = time.perf_counter()
        test_func()
        t1 = time.perf_counter()
        rss_after = get_peak_rss_kb()
        return t1 - t0, max(rss_after - rss_before, 0)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# --- VCD tests ---

def test_full_parse_vcd(filepath):
    """Load and fully parse a VCD file via pywellen."""
    from pywellen import Waveform
    _w = Waveform(filepath)


def test_signal_list_vcd(filepath):
    """Load a VCD file and enumerate all variables."""
    from pywellen import Waveform
    w = Waveform(filepath)
    hier = w.hierarchy
    var_count = 0
    for var in hier.all_vars():
        _ = var.full_name(hier)
        var_count += 1
    _ = var_count


def test_time_range_vcd(filepath):
    """Load a VCD file and read the time table endpoints."""
    from pywellen import Waveform
    w = Waveform(filepath)
    tt = w.time_table
    _ = tt[0]
    _ = tt[-1]


def test_value_query_vcd(filepath):
    """Load VCD, select up to 3 signals, query values over 10%/50%/100% range."""
    from pywellen import Waveform
    w = Waveform(filepath)
    hier = w.hierarchy

    # Collect all vars
    all_vars = list(hier.all_vars())
    if not all_vars:
        return

    # Pick up to 3 vars spread across the list
    chosen = []
    for i in range(min(3, len(all_vars))):
        idx = i * len(all_vars) // min(3, len(all_vars))
        chosen.append(all_vars[idx])

    tt = w.time_table
    t_start = tt[0]
    t_end = tt[-1]
    if t_start is None or t_end is None:
        return
    span = t_end - t_start
    if span <= 0:
        return

    for pct in (0.10, 0.50, 1.00):
        query_end = t_start + int(span * pct)
        for var in chosen:
            sig = w.get_signal(var)
            count = 0
            for t, v in sig.all_changes():
                if t_start <= t <= query_end:
                    count += 1
                elif t > query_end:
                    break
            _ = count


# --- FST tests ---

def test_full_parse_fst(filepath):
    """Load and fully parse an FST file via pywellen."""
    from pywellen import Waveform
    _w = Waveform(filepath)


def test_signal_list_fst(filepath):
    """Load an FST file and enumerate all variables."""
    from pywellen import Waveform
    w = Waveform(filepath)
    hier = w.hierarchy
    var_count = 0
    for var in hier.all_vars():
        _ = var.full_name(hier)
        var_count += 1
    _ = var_count


def test_time_range_fst(filepath):
    """Load an FST file and read the time table endpoints."""
    from pywellen import Waveform
    w = Waveform(filepath)
    tt = w.time_table
    _ = tt[0]
    _ = tt[-1]


def test_value_query_fst(filepath):
    """Load FST, select up to 3 signals, query values over 10%/50%/100% range."""
    from pywellen import Waveform
    w = Waveform(filepath)
    hier = w.hierarchy

    all_vars = list(hier.all_vars())
    if not all_vars:
        return

    chosen = []
    for i in range(min(3, len(all_vars))):
        idx = i * len(all_vars) // min(3, len(all_vars))
        chosen.append(all_vars[idx])

    tt = w.time_table
    t_start = tt[0]
    t_end = tt[-1]
    if t_start is None or t_end is None:
        return
    span = t_end - t_start
    if span <= 0:
        return

    for pct in (0.10, 0.50, 1.00):
        query_end = t_start + int(span * pct)
        for var in chosen:
            sig = w.get_signal(var)
            count = 0
            for t, v in sig.all_changes():
                if t_start <= t <= query_end:
                    count += 1
                elif t > query_end:
                    break
            _ = count


def test_pipeline_vcd(filepath):
    """Continuous operation on VCD: load -> signal_list -> time_range -> value_query."""
    from pywellen import Waveform
    # 1. Load
    w = Waveform(filepath)
    hier = w.hierarchy

    # 2. Signal list
    all_vars = list(hier.all_vars())
    if not all_vars:
        return

    # 3. Time range
    tt = w.time_table
    t_start = tt[0]
    t_end = tt[-1]
    if t_start is None or t_end is None or t_end <= t_start:
        return

    # 4. Value query (3 signals, full range)
    chosen = []
    for i in range(min(3, len(all_vars))):
        idx = i * len(all_vars) // min(3, len(all_vars))
        chosen.append(all_vars[idx])

    for var in chosen:
        sig = w.get_signal(var)
        count = 0
        for t, v in sig.all_changes():
            if t_start <= t <= t_end:
                count += 1
        _ = count


def test_pipeline_fst(filepath):
    """Continuous operation on FST: load -> signal_list -> time_range -> value_query."""
    from pywellen import Waveform
    w = Waveform(filepath)
    hier = w.hierarchy

    all_vars = list(hier.all_vars())
    if not all_vars:
        return

    tt = w.time_table
    t_start = tt[0]
    t_end = tt[-1]
    if t_start is None or t_end is None or t_end <= t_start:
        return

    chosen = []
    for i in range(min(3, len(all_vars))):
        idx = i * len(all_vars) // min(3, len(all_vars))
        chosen.append(all_vars[idx])

    for var in chosen:
        sig = w.get_signal(var)
        count = 0
        for t, v in sig.all_changes():
            if t_start <= t <= t_end:
                count += 1
        _ = count


def run_benchmark_for_format(fmt, files, test_map, scale, timeout):
    """Run all tests for a specific format and return results list."""
    results = []
    for filepath in files:
        file_size = os.path.getsize(filepath)

        for test_name, test_func in test_map.items():
            result = {
                "test": test_name,
                "scale": scale,
                "file": os.path.basename(filepath),
                "file_size_bytes": file_size,
                "times_s": [],
                "mean_s": 0,
                "stdev_s": 0,
                "memory_kb": 0,
                "status": "ok",
                "error": "",
            }

            try:
                times = []
                peak_mem = 0
                for _ in range(REPETITIONS):
                    gc.collect()
                    elapsed, mem = run_test(lambda: test_func(filepath), timeout)
                    times.append(elapsed)
                    peak_mem = max(peak_mem, mem)

                result["times_s"] = [round(t, 6) for t in times]
                result["mean_s"] = round(statistics.mean(times), 6)
                result["stdev_s"] = round(statistics.stdev(times), 6) if len(times) > 1 else 0
                result["memory_kb"] = peak_mem

            except TimeoutError:
                result["status"] = "timeout"
                result["error"] = f"Timed out after {timeout}s"
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)

            results.append(result)
    return results


def run_benchmark(data_dir, scale, output_path):
    """Run all benchmark tests and produce JSON output."""
    # Early check for pywellen availability
    try:
        import pywellen  # noqa: F401
    except ImportError as e:
        output = {
            "library": "pywellen",
            "format": "vcd+fst",
            "results": [{
                "test": "import",
                "scale": scale,
                "file": "",
                "file_size_bytes": 0,
                "times_s": [],
                "mean_s": 0,
                "stdev_s": 0,
                "memory_kb": 0,
                "status": "error",
                "error": f"pywellen not available: {e}"
            }]
        }
        json_str = json.dumps(output, indent=2)
        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w") as f:
                f.write(json_str)
            print(f"Results written to {output_path}", file=sys.stderr)
        else:
            print(json_str)
        return

    timeout = SCALE_TIMEOUTS.get(scale, 120)
    vcd_files, fst_files = find_waveform_files(data_dir, scale)

    all_results = []

    if not vcd_files and not fst_files:
        all_results.append({
            "test": "find_files",
            "scale": scale,
            "file": "",
            "file_size_bytes": 0,
            "times_s": [],
            "mean_s": 0,
            "stdev_s": 0,
            "memory_kb": 0,
            "status": "error",
            "error": f"No VCD or FST files found in {data_dir}/{scale}"
        })

    # VCD tests
    if vcd_files:
        vcd_tests = {
            "full_parse_vcd": test_full_parse_vcd,
            "signal_list_vcd": test_signal_list_vcd,
            "time_range_vcd": test_time_range_vcd,
            "value_query_vcd": test_value_query_vcd,
            "pipeline_vcd": test_pipeline_vcd,
        }
        all_results.extend(
            run_benchmark_for_format("vcd", vcd_files, vcd_tests, scale, timeout)
        )

    # FST tests
    if fst_files:
        fst_tests = {
            "full_parse_fst": test_full_parse_fst,
            "signal_list_fst": test_signal_list_fst,
            "time_range_fst": test_time_range_fst,
            "value_query_fst": test_value_query_fst,
            "pipeline_fst": test_pipeline_fst,
        }
        all_results.extend(
            run_benchmark_for_format("fst", fst_files, fst_tests, scale, timeout)
        )

    output = {
        "library": "pywellen",
        "format": "vcd+fst",
        "results": all_results,
    }

    json_str = json.dumps(output, indent=2)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            f.write(json_str)
        print(f"Results written to {output_path}", file=sys.stderr)
    else:
        print(json_str)


def main():
    parser = argparse.ArgumentParser(description="Benchmark pywellen library (VCD + FST)")
    parser.add_argument("--data-dir", required=True, help="Path to benchmark data directory")
    parser.add_argument("--scale", choices=["small", "medium", "large"], default="small",
                        help="Benchmark scale (affects timeout and file selection)")
    parser.add_argument("--output", default="", help="Output JSON file path (stdout if empty)")
    args = parser.parse_args()

    run_benchmark(args.data_dir, args.scale, args.output)


if __name__ == "__main__":
    main()
