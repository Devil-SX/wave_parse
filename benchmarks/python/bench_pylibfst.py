#!/usr/bin/env python3
"""Benchmark script for pylibfst library (FST format parsing)."""

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


def find_fst_files(data_dir, scale):
    """Find FST files in the data directory for the given scale."""
    scale_dir = os.path.join(data_dir, scale)
    if not os.path.isdir(scale_dir):
        scale_dir = data_dir
    files = []
    for f in sorted(os.listdir(scale_dir)):
        if f.endswith(".fst"):
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
    """Open FST file and parse all scopes/signals."""
    import pylibfst
    fst = pylibfst.lib.fstReaderOpen(filepath.encode("utf-8"))
    if fst == pylibfst.ffi.NULL:
        raise RuntimeError(f"Failed to open FST file: {filepath}")
    try:
        _scopes, _signals = pylibfst.get_scopes_signals2(fst)
    finally:
        pylibfst.lib.fstReaderClose(fst)


def test_signal_list(filepath):
    """Open FST file and enumerate all signals."""
    import pylibfst
    fst = pylibfst.lib.fstReaderOpen(filepath.encode("utf-8"))
    if fst == pylibfst.ffi.NULL:
        raise RuntimeError(f"Failed to open FST file: {filepath}")
    try:
        _scopes, signals_info = pylibfst.get_scopes_signals2(fst)
        sig_names = list(signals_info.by_name.keys())
        _ = len(sig_names)
    finally:
        pylibfst.lib.fstReaderClose(fst)


def test_time_range(filepath):
    """Open FST file and read start/end times."""
    import pylibfst
    fst = pylibfst.lib.fstReaderOpen(filepath.encode("utf-8"))
    if fst == pylibfst.ffi.NULL:
        raise RuntimeError(f"Failed to open FST file: {filepath}")
    try:
        _ = pylibfst.lib.fstReaderGetStartTime(fst)
        _ = pylibfst.lib.fstReaderGetEndTime(fst)
    finally:
        pylibfst.lib.fstReaderClose(fst)


def test_value_query(filepath):
    """Open FST, select up to 3 signals, iterate value changes over 10%/50%/100% range."""
    import pylibfst
    fst = pylibfst.lib.fstReaderOpen(filepath.encode("utf-8"))
    if fst == pylibfst.ffi.NULL:
        raise RuntimeError(f"Failed to open FST file: {filepath}")
    try:
        _scopes, signals_info = pylibfst.get_scopes_signals2(fst)
        sig_items = list(signals_info.by_name.items())

        if not sig_items:
            return

        # Pick up to 3 signals spread across the list
        chosen = []
        for i in range(min(3, len(sig_items))):
            idx = i * len(sig_items) // min(3, len(sig_items))
            chosen.append(sig_items[idx])

        start_time = pylibfst.lib.fstReaderGetStartTime(fst)
        end_time = pylibfst.lib.fstReaderGetEndTime(fst)
        span = end_time - start_time
        if span <= 0:
            return

        chosen_handles = {sig.handle for _, sig in chosen}
        handle_to_name = {sig.handle: name for name, sig in chosen}

        for pct in (0.10, 0.50, 1.00):
            t_end = start_time + int(span * pct)

            # Clear all masks and set only chosen signals
            pylibfst.lib.fstReaderClrFacProcessMaskAll(fst)
            for handle in chosen_handles:
                pylibfst.lib.fstReaderSetFacProcessMask(fst, handle)

            collected = {name: 0 for name in handle_to_name.values()}

            def value_change_callback(_user_data, t, handle, value):
                if handle in chosen_handles and start_time <= t <= t_end:
                    name = handle_to_name.get(handle, "")
                    if name:
                        collected[name] += 1

            pylibfst.fstReaderIterBlocks(fst, value_change_callback)
            _ = collected

    finally:
        pylibfst.lib.fstReaderClose(fst)


def test_pipeline(filepath):
    """Continuous operation: load -> signal_list -> time_range -> value_query in one flow."""
    import pylibfst
    fst = pylibfst.lib.fstReaderOpen(filepath.encode("utf-8"))
    if fst == pylibfst.ffi.NULL:
        raise RuntimeError(f"Failed to open FST file: {filepath}")
    try:
        # 1. Full parse + signal list
        _scopes, signals_info = pylibfst.get_scopes_signals2(fst)
        sig_items = list(signals_info.by_name.items())

        if not sig_items:
            return

        # 2. Time range
        start_time = pylibfst.lib.fstReaderGetStartTime(fst)
        end_time = pylibfst.lib.fstReaderGetEndTime(fst)
        span = end_time - start_time
        if span <= 0:
            return

        # 3. Value query (3 signals, full range)
        chosen = []
        for i in range(min(3, len(sig_items))):
            idx = i * len(sig_items) // min(3, len(sig_items))
            chosen.append(sig_items[idx])

        chosen_handles = {sig.handle for _, sig in chosen}
        handle_to_name = {sig.handle: name for name, sig in chosen}

        pylibfst.lib.fstReaderClrFacProcessMaskAll(fst)
        for handle in chosen_handles:
            pylibfst.lib.fstReaderSetFacProcessMask(fst, handle)

        collected = {name: 0 for name in handle_to_name.values()}

        def value_change_callback(_user_data, t, handle, value):
            if handle in chosen_handles and start_time <= t <= end_time:
                name = handle_to_name.get(handle, "")
                if name:
                    collected[name] += 1

        pylibfst.fstReaderIterBlocks(fst, value_change_callback)
        _ = collected
    finally:
        pylibfst.lib.fstReaderClose(fst)


def run_benchmark(data_dir, scale, output_path):
    """Run all benchmark tests and produce JSON output."""
    timeout = SCALE_TIMEOUTS.get(scale, 120)
    fst_files = find_fst_files(data_dir, scale)

    if not fst_files:
        print(json.dumps({
            "library": "pylibfst",
            "format": "fst",
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
                "error": f"No FST files found in {data_dir}/{scale}"
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

    for fst_file in fst_files:
        file_size = os.path.getsize(fst_file)

        for test_name, test_func in tests.items():
            result = {
                "test": test_name,
                "scale": scale,
                "file": os.path.basename(fst_file),
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
                    elapsed, mem = run_test(lambda: test_func(fst_file), timeout)
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
        "library": "pylibfst",
        "format": "fst",
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
    parser = argparse.ArgumentParser(description="Benchmark pylibfst library")
    parser.add_argument("--data-dir", required=True, help="Path to benchmark data directory")
    parser.add_argument("--scale", choices=["small", "medium", "large"], default="small",
                        help="Benchmark scale (affects timeout and file selection)")
    parser.add_argument("--output", default="", help="Output JSON file path (stdout if empty)")
    args = parser.parse_args()

    run_benchmark(args.data_dir, args.scale, args.output)


if __name__ == "__main__":
    main()
