#!/usr/bin/env python3
"""Benchmark script for vcdvcd library (VCD format parsing)."""

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
    # On Linux, ru_maxrss is in KB
    return usage.ru_maxrss


def find_vcd_files(data_dir, scale):
    """Find VCD files in the data directory for the given scale."""
    scale_dir = os.path.join(data_dir, scale)
    if not os.path.isdir(scale_dir):
        # Fall back to flat directory
        scale_dir = data_dir
    files = []
    for f in sorted(os.listdir(scale_dir)):
        if f.endswith(".vcd"):
            files.append(os.path.join(scale_dir, f))
    return files


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


def test_full_parse(filepath):
    """Parse the entire VCD file."""
    from vcdvcd import VCDVCD
    _vcd = VCDVCD(filepath)


def test_signal_list(filepath):
    """Parse and iterate all signal names."""
    from vcdvcd import VCDVCD
    vcd = VCDVCD(filepath)
    sig_names = list(vcd.signals)
    _ = len(sig_names)


def test_time_range(filepath):
    """Parse and read time range."""
    from vcdvcd import VCDVCD
    vcd = VCDVCD(filepath)
    _ = vcd.begintime
    _ = vcd.endtime


def test_value_query(filepath):
    """Parse, select up to 3 signals, query values over 10%/50%/100% of the time range."""
    from vcdvcd import VCDVCD
    vcd = VCDVCD(filepath)

    sig_names = list(vcd.signals)
    if not sig_names:
        return

    # Pick up to 3 signals spread across the list
    chosen = []
    for i in range(min(3, len(sig_names))):
        idx = i * len(sig_names) // min(3, len(sig_names))
        chosen.append(sig_names[idx])

    begin = vcd.begintime
    end = vcd.endtime
    if begin is None or end is None:
        return
    span = end - begin
    if span <= 0:
        return

    # Query at 10%, 50%, 100% of the time range
    for pct in (0.10, 0.50, 1.00):
        t_end = begin + int(span * pct)
        for sname in chosen:
            sig_obj = vcd[sname]
            count = 0
            for t, v in sig_obj.tv:
                if begin <= t <= t_end:
                    count += 1
            _ = count


def test_pipeline(filepath):
    """Continuous operation: load -> signal_list -> time_range -> value_query in one flow."""
    from vcdvcd import VCDVCD

    # 1. Full parse
    vcd = VCDVCD(filepath)

    # 2. Signal list
    sig_names = list(vcd.signals)
    if not sig_names:
        return

    # 3. Time range
    begin = vcd.begintime
    end = vcd.endtime
    if begin is None or end is None:
        return
    span = end - begin
    if span <= 0:
        return

    # 4. Value query (3 signals, full range)
    chosen = []
    for i in range(min(3, len(sig_names))):
        idx = i * len(sig_names) // min(3, len(sig_names))
        chosen.append(sig_names[idx])

    for sname in chosen:
        sig_obj = vcd[sname]
        count = 0
        for t, v in sig_obj.tv:
            if begin <= t <= end:
                count += 1
        _ = count


def run_benchmark(data_dir, scale, output_path):
    """Run all benchmark tests and produce JSON output."""
    timeout = SCALE_TIMEOUTS.get(scale, 120)
    vcd_files = find_vcd_files(data_dir, scale)

    if not vcd_files:
        print(json.dumps({
            "library": "vcdvcd",
            "format": "vcd",
            "results": [{
                "test": "find_files",
                "scale": scale,
                "file": "",
                "file_size_bytes": 0,
                "times_s": [],
                "mean_s": 0,
                "stdev_s": 0,
                "memory_kb": 0,
                "status": "error",
                "error": f"No VCD files found in {data_dir}/{scale}"
            }]
        }, indent=2))
        return

    tests = {
        "full_parse": test_full_parse,
        "signal_list": test_signal_list,
        "time_range": test_time_range,
        "value_query": test_value_query,
        "pipeline": test_pipeline,
    }

    results = []

    for vcd_file in vcd_files:
        file_size = os.path.getsize(vcd_file)

        for test_name, test_func in tests.items():
            result = {
                "test": test_name,
                "scale": scale,
                "file": os.path.basename(vcd_file),
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
                    elapsed, mem = run_test(lambda: test_func(vcd_file), timeout)
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

    output = {
        "library": "vcdvcd",
        "format": "vcd",
        "results": results,
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
    parser = argparse.ArgumentParser(description="Benchmark vcdvcd library")
    parser.add_argument("--data-dir", required=True, help="Path to benchmark data directory")
    parser.add_argument("--scale", choices=["small", "medium", "large"], default="small",
                        help="Benchmark scale (affects timeout and file selection)")
    parser.add_argument("--output", default="", help="Output JSON file path (stdout if empty)")
    args = parser.parse_args()

    run_benchmark(args.data_dir, args.scale, args.output)


if __name__ == "__main__":
    main()
