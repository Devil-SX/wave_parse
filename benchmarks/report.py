#!/usr/bin/env python3
"""Generate a Markdown comparison report from benchmark results.

Reads JSON results from the results/ directory and produces a comprehensive
Markdown report with tables and ASCII bar charts.

Usage:
    python report.py --results-dir results/ --scale small
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


def log(msg):
    print(f"[report] {msg}", file=sys.stderr, flush=True)


def load_combined(results_dir, scale):
    """Load the combined results file."""
    path = Path(results_dir) / f"combined_{scale}.json"
    if not path.exists():
        log(f"Combined results not found: {path}")
        return None
    with open(path) as f:
        return json.load(f)


def normalize_results(combined):
    """Normalize Python and Rust results into a unified list of records.

    Each record: {library, format, file, test, mean_s, stdev_s, memory_kb, status, error, file_size_bytes}
    """
    records = []

    # Python results: list of {library, format, results: [{test, scale, file, ...}]}
    for lib_data in combined.get("python_results", []):
        library = lib_data.get("library", "unknown")
        fmt = lib_data.get("format", "unknown")
        for r in lib_data.get("results", []):
            records.append({
                "library": library,
                "language": "Python",
                "format": fmt,
                "file": r.get("file", ""),
                "test": r.get("test", ""),
                "mean_s": r.get("mean_s", 0),
                "stdev_s": r.get("stdev_s", 0),
                "memory_kb": r.get("memory_kb", 0),
                "status": r.get("status", "unknown"),
                "error": r.get("error", ""),
                "file_size_bytes": r.get("file_size_bytes", 0),
                "times_s": r.get("times_s", []),
            })

    # Rust results: list of {library, format, file, operation, mean, ...}
    for r in combined.get("rust_results", []):
        # Rust results may be a flat list of BenchResult objects
        if isinstance(r, dict) and "operation" in r:
            file_path = r.get("file", "")
            file_name = os.path.basename(file_path) if file_path else ""
            # Estimate file size from path
            file_size = 0
            if file_path and os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                except OSError:
                    pass
            records.append({
                "library": r.get("library", "unknown"),
                "language": "Rust",
                "format": r.get("format", "unknown"),
                "file": file_name,
                "test": r.get("operation", ""),
                "mean_s": r.get("mean", 0),
                "stdev_s": r.get("stdev", 0),
                "memory_kb": r.get("peak_memory_kb", 0),
                "status": r.get("status", "unknown"),
                "error": r.get("error", ""),
                "file_size_bytes": file_size,
                "times_s": r.get("times", []),
            })
        elif isinstance(r, dict) and "results" in r:
            # Wrapped format (from error cases)
            library = r.get("library", "unknown")
            for sub in r.get("results", []):
                records.append({
                    "library": library,
                    "language": "Rust",
                    "format": r.get("format", "unknown"),
                    "file": sub.get("file", ""),
                    "test": sub.get("test", ""),
                    "mean_s": sub.get("mean_s", 0),
                    "stdev_s": sub.get("stdev_s", 0),
                    "memory_kb": sub.get("memory_kb", 0),
                    "status": sub.get("status", "unknown"),
                    "error": sub.get("error", ""),
                    "file_size_bytes": sub.get("file_size_bytes", 0),
                    "times_s": sub.get("times_s", []),
                })

    return records


def format_time(seconds):
    """Format time to human-readable string."""
    if seconds <= 0:
        return "N/A"
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.1f}us"
    if seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    return f"{seconds:.3f}s"


def format_size(size_bytes):
    """Format bytes to human-readable."""
    if size_bytes <= 0:
        return "N/A"
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def throughput_mbs(file_size_bytes, mean_s):
    """Compute throughput in MB/s."""
    if mean_s <= 0 or file_size_bytes <= 0:
        return 0
    return (file_size_bytes / (1024 * 1024)) / mean_s


def ascii_bar(value, max_value, width=30):
    """Generate an ASCII bar chart segment."""
    if max_value <= 0 or value <= 0:
        return ""
    bar_len = int((value / max_value) * width)
    bar_len = max(1, min(bar_len, width))
    return "#" * bar_len


def generate_report(records, scale, output_path):
    """Generate a Markdown report from normalized records."""
    lines = []
    lines.append("# VCD/FST Library Benchmark Report\n")
    lines.append(f"- **Scale**: {scale}")
    lines.append(f"- **Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Total benchmarks**: {len(records)}")

    ok_records = [r for r in records if r["status"] == "ok"]
    err_records = [r for r in records if r["status"] != "ok"]
    lines.append(f"- **Passed**: {len(ok_records)}, **Failed/Skipped**: {len(err_records)}")
    lines.append("")

    # ----- Section 1: Full Parse Comparison -----
    lines.append("## 1. Full Parse Performance\n")
    parse_records = [r for r in ok_records if "full_parse" in r["test"]]

    if parse_records:
        # Group by file
        files = sorted(set(r["file"] for r in parse_records if r["file"]))
        for f in files:
            file_records = [r for r in parse_records if r["file"] == f]
            if not file_records:
                continue
            file_size = max(r["file_size_bytes"] for r in file_records)
            lines.append(f"### File: `{f}` ({format_size(file_size)})\n")
            lines.append("| Library | Language | Format | Time | Throughput | Memory |")
            lines.append("|---------|----------|--------|------|------------|--------|")

            sorted_recs = sorted(file_records, key=lambda r: r["mean_s"] if r["mean_s"] > 0 else 9999)
            for r in sorted_recs:
                tp = throughput_mbs(r["file_size_bytes"], r["mean_s"])
                tp_str = f"{tp:.1f} MB/s" if tp > 0 else "N/A"
                mem_str = f"{r['memory_kb']}KB" if r["memory_kb"] > 0 else "N/A"
                lines.append(
                    f"| {r['library']} | {r['language']} | {r['format']} | "
                    f"{format_time(r['mean_s'])} | {tp_str} | {mem_str} |"
                )
            lines.append("")

            # ASCII bar chart
            if len(sorted_recs) > 1:
                max_time = max(r["mean_s"] for r in sorted_recs if r["mean_s"] > 0)
                lines.append("```")
                for r in sorted_recs:
                    bar = ascii_bar(r["mean_s"], max_time)
                    lines.append(f"  {r['library']:15s} |{bar}| {format_time(r['mean_s'])}")
                lines.append("```")
                lines.append("")

    # ----- Section 2: Signal List Performance -----
    lines.append("## 2. Signal List Retrieval Performance\n")
    sig_records = [r for r in ok_records if "signal_list" in r["test"]]

    if sig_records:
        files = sorted(set(r["file"] for r in sig_records if r["file"]))
        for f in files:
            file_records = [r for r in sig_records if r["file"] == f]
            if not file_records:
                continue
            lines.append(f"### File: `{f}`\n")
            lines.append("| Library | Language | Time | Stdev |")
            lines.append("|---------|----------|------|-------|")
            sorted_recs = sorted(file_records, key=lambda r: r["mean_s"] if r["mean_s"] > 0 else 9999)
            for r in sorted_recs:
                lines.append(
                    f"| {r['library']} | {r['language']} | "
                    f"{format_time(r['mean_s'])} | {format_time(r['stdev_s'])} |"
                )
            lines.append("")

    # ----- Section 3: Value Query Performance -----
    lines.append("## 3. Value Query Performance\n")
    val_records = [r for r in ok_records if "value_query" in r["test"]]

    if val_records:
        files = sorted(set(r["file"] for r in val_records if r["file"]))
        for f in files:
            file_records = [r for r in val_records if r["file"] == f]
            if not file_records:
                continue
            file_size = max(r["file_size_bytes"] for r in file_records)
            lines.append(f"### File: `{f}` ({format_size(file_size)})\n")
            lines.append("| Library | Language | Format | Time | Stdev | Memory |")
            lines.append("|---------|----------|--------|------|-------|--------|")
            sorted_recs = sorted(file_records, key=lambda r: r["mean_s"] if r["mean_s"] > 0 else 9999)
            for r in sorted_recs:
                mem_str = f"{r['memory_kb']}KB" if r["memory_kb"] > 0 else "N/A"
                lines.append(
                    f"| {r['library']} | {r['language']} | {r['format']} | "
                    f"{format_time(r['mean_s'])} | {format_time(r['stdev_s'])} | {mem_str} |"
                )
            lines.append("")

            # ASCII bar chart
            if len(sorted_recs) > 1:
                max_time = max(r["mean_s"] for r in sorted_recs if r["mean_s"] > 0)
                lines.append("```")
                for r in sorted_recs:
                    bar = ascii_bar(r["mean_s"], max_time)
                    lines.append(f"  {r['library']:15s} |{bar}| {format_time(r['mean_s'])}")
                lines.append("```")
                lines.append("")

    # ----- Section 4: Pipeline (Continuous Operation) Performance -----
    lines.append("## 4. Pipeline Performance (Load + Signal List + Time Range + Value Query)\n")
    pipe_records = [r for r in ok_records if "pipeline" in r["test"]]

    if pipe_records:
        files = sorted(set(r["file"] for r in pipe_records if r["file"]))
        for f in files:
            file_records = [r for r in pipe_records if r["file"] == f]
            if not file_records:
                continue
            file_size = max(r["file_size_bytes"] for r in file_records)
            lines.append(f"### File: `{f}` ({format_size(file_size)})\n")
            lines.append("| Library | Language | Format | Pipeline Time | Throughput | Memory |")
            lines.append("|---------|----------|--------|---------------|------------|--------|")

            sorted_recs = sorted(file_records, key=lambda r: r["mean_s"] if r["mean_s"] > 0 else 9999)
            for r in sorted_recs:
                tp = throughput_mbs(r["file_size_bytes"], r["mean_s"])
                tp_str = f"{tp:.1f} MB/s" if tp > 0 else "N/A"
                mem_str = f"{r['memory_kb']}KB" if r["memory_kb"] > 0 else "N/A"
                lines.append(
                    f"| {r['library']} | {r['language']} | {r['format']} | "
                    f"{format_time(r['mean_s'])} | {tp_str} | {mem_str} |"
                )
            lines.append("")

            # ASCII bar chart
            if len(sorted_recs) > 1:
                max_time = max(r["mean_s"] for r in sorted_recs if r["mean_s"] > 0)
                lines.append("```")
                for r in sorted_recs:
                    bar = ascii_bar(r["mean_s"], max_time)
                    lines.append(f"  {r['library']:15s} |{bar}| {format_time(r['mean_s'])}")
                lines.append("```")
                lines.append("")
    else:
        lines.append("No pipeline benchmarks recorded.\n")

    # ----- Section 5: Overall Ranking -----
    lines.append("## 5. Overall Ranking (by Full Parse Speed)\n")

    if parse_records:
        # Aggregate: average mean_s per library across all files
        lib_times = {}
        for r in parse_records:
            lib = f"{r['library']} ({r['language']})"
            if lib not in lib_times:
                lib_times[lib] = []
            if r["mean_s"] > 0:
                lib_times[lib].append(r["mean_s"])

        ranking = []
        for lib, times in lib_times.items():
            if times:
                avg = sum(times) / len(times)
                ranking.append((lib, avg, len(times)))

        ranking.sort(key=lambda x: x[1])

        lines.append("| Rank | Library | Avg Parse Time | Files Tested |")
        lines.append("|------|---------|----------------|--------------|")
        for i, (lib, avg, count) in enumerate(ranking, 1):
            medal = {1: " (fastest)", 2: "", 3: ""}.get(i, "")
            lines.append(f"| {i} | {lib}{medal} | {format_time(avg)} | {count} |")
        lines.append("")

        if len(ranking) > 1 and ranking[0][1] > 0:
            fastest = ranking[0]
            lines.append(f"**Fastest**: {fastest[0]} at {format_time(fastest[1])} average\n")
            for lib, avg, _ in ranking[1:]:
                if fastest[1] > 0:
                    ratio = avg / fastest[1]
                    lines.append(f"- {lib}: {ratio:.1f}x slower")
            lines.append("")

    # ----- Section 6: Errors and Failures -----
    if err_records:
        lines.append("## 6. Errors and Failures\n")
        lines.append("| Library | Test | Status | Error |")
        lines.append("|---------|------|--------|-------|")
        for r in err_records:
            err_msg = r.get("error", "")[:80]
            lines.append(
                f"| {r['library']} | {r['test']} | {r['status']} | {err_msg} |"
            )
        lines.append("")

    # ----- Section 7: Summary -----
    lines.append("## 7. Summary\n")

    vcd_libs = set()
    fst_libs = set()
    for r in ok_records:
        if r["format"] in ("vcd", "vcd+fst"):
            vcd_libs.add(r["library"])
        if r["format"] in ("fst", "vcd+fst"):
            fst_libs.add(r["library"])

    lines.append(f"- **VCD libraries tested**: {', '.join(sorted(vcd_libs)) or 'none'}")
    lines.append(f"- **FST libraries tested**: {', '.join(sorted(fst_libs)) or 'none'}")
    lines.append(f"- **Scale**: {scale}")
    lines.append("")
    lines.append("### Key Takeaways\n")
    lines.append("- Rust libraries generally parse faster than Python due to lower interpreter overhead")
    lines.append("- FST format offers better compression but parse speed depends on implementation")
    lines.append("- wellen provides the most comprehensive format support (VCD + FST + GHW)")
    lines.append("- For VCD streaming use cases, rust-vcd and vcd-ng offer low-memory alternatives")
    lines.append("- For FST, fst-reader (pure Rust) avoids C dependency unlike fstapi")
    lines.append("")

    report_text = "\n".join(lines)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        f.write(report_text)

    log(f"Report written to {output}")
    return str(output)


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark comparison report")
    parser.add_argument("--results-dir", default="results", help="Directory with JSON results")
    parser.add_argument("--scale", default="all", help="Scale to report on (small/medium/large/all)")
    parser.add_argument(
        "--output",
        default="",
        help="Output file path (default: results/benchmark_report.md)",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        log(f"ERROR: Results directory not found: {results_dir}")
        sys.exit(1)

    all_records = []
    scales_found = []

    if args.scale == "all":
        for s in ["small", "medium", "large"]:
            combined = load_combined(results_dir, s)
            if combined is not None:
                recs = normalize_results(combined)
                # Tag each record with its scale
                for r in recs:
                    r["scale"] = s
                all_records.extend(recs)
                scales_found.append(s)
    else:
        combined = load_combined(results_dir, args.scale)
        if combined is not None:
            all_records = normalize_results(combined)
            scales_found.append(args.scale)

    if not all_records:
        log("No benchmark records found in results. Run run_all.py first.")
        sys.exit(1)

    scale_label = "+".join(scales_found) if len(scales_found) > 1 else (scales_found[0] if scales_found else "unknown")
    log(f"Loaded {len(all_records)} benchmark records from scales: {', '.join(scales_found)}")

    output_path = args.output or str(results_dir / "benchmark_report.md")
    generate_report(all_records, scale_label, output_path)


if __name__ == "__main__":
    main()
