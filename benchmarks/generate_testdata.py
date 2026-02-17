#!/usr/bin/env python3
"""Generate synthetic VCD and FST waveform files for benchmarking.

Creates test data at three scales (small/medium/large) with a mix of
1-bit, 8-bit, and 32-bit signals. Also symlinks real-world files from
the wellen test inputs directory.

Usage:
    python generate_testdata.py                        # medium scale
    python generate_testdata.py --scale small
    python generate_testdata.py --scale large
    python generate_testdata.py --data-dir /tmp/bench
"""

import argparse
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Scale configurations
# ---------------------------------------------------------------------------
SCALE_CONFIG = {
    "small": {
        "num_signals": 50,
        "num_timesteps": 1000,
        "label": "~500KB",
    },
    "medium": {
        "num_signals": 200,
        "num_timesteps": 10000,
        "label": "~20MB",
    },
    "large": {
        "num_signals": 2000,
        "num_timesteps": 200000,
        "label": "~100MB+",
    },
}

# Real-world files to symlink (largest available in wellen inputs)
WELLEN_INPUTS = Path("/home/sdu/wave_parse/wellen/wellen/inputs")
REAL_WORLD_FILES = {
    "real_world_large.vcd": WELLEN_INPUTS / "icarus" / "gatelevel_netlist_large_hierarchy_wellen_pull_61.vcd",
    "real_world_medium.vcd": WELLEN_INPUTS / "verilator" / "swerv1.vcd",
    "real_world_large.fst": WELLEN_INPUTS / "verilator" / "verilator-incomplete.fst",
    "real_world_medium.fst": WELLEN_INPUTS / "xilinx_isim" / "test1.vcd.fst",
}


def format_size(size_bytes: int) -> str:
    """Format byte count to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


# ---------------------------------------------------------------------------
# VCD generation (uses pyvcd / VCDWriter)
# ---------------------------------------------------------------------------
def generate_vcd(path: str, num_signals: int, num_timesteps: int) -> int:
    """Generate a synthetic VCD file.

    Returns file size in bytes.
    """
    from vcd.writer import VCDWriter

    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        with VCDWriter(f, timescale="1ns", date="benchmark") as writer:
            signals = []
            for i in range(num_signals):
                if i % 3 == 0:
                    size = 1       # 1-bit
                elif i % 3 == 1:
                    size = 8       # 8-bit
                else:
                    size = 32      # 32-bit
                sig = writer.register_var(
                    "bench", f"sig_{i:04d}", "wire", size=size, init=0
                )
                signals.append((sig, size))

            # Use denser change pattern for larger files to reach target size.
            # For signals with high index, reduce the modulus to increase activity.
            dense = num_signals > 500
            for t in range(num_timesteps):
                timestamp = t * 10
                for i, (sig, size) in enumerate(signals):
                    mod = max(1, (i + 1) // 10) if dense else (i + 1)
                    if t % mod == 0:
                        if size == 1:
                            value = t % 2
                        else:
                            value = (t * (i + 1)) % (2 ** size)
                        writer.change(sig, timestamp, value)

    return Path(path).stat().st_size


# ---------------------------------------------------------------------------
# FST generation (uses pylibfst C API via cffi)
# ---------------------------------------------------------------------------
def generate_fst(path: str, num_signals: int, num_timesteps: int) -> int:
    """Generate a synthetic FST file.

    Returns file size in bytes.
    """
    import pylibfst
    from pylibfst import lib, ffi

    Path(path).parent.mkdir(parents=True, exist_ok=True)

    ctx = lib.fstWriterCreate(path.encode("utf-8"), 1)
    if ctx == ffi.NULL:
        raise RuntimeError("Failed to create FST writer")

    try:
        lib.fstWriterSetTimescale(ctx, -9)  # 1ns
        lib.fstWriterSetScope(ctx, lib.FST_ST_VCD_MODULE, b"bench", ffi.NULL)

        handles = []
        for i in range(num_signals):
            if i % 3 == 0:
                size = 1
            elif i % 3 == 1:
                size = 8
            else:
                size = 32
            name = f"sig_{i:04d}".encode("utf-8")
            handle = lib.fstWriterCreateVar(
                ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, size, name, 0
            )
            handles.append((handle, size))

        lib.fstWriterSetUpscope(ctx)

        # Initial values at time 0
        lib.fstWriterEmitTimeChange(ctx, 0)
        for handle, size in handles:
            lib.fstWriterEmitValueChange(ctx, handle, ("0" * size).encode("utf-8"))

        # Value changes (dense pattern for large files)
        dense = num_signals > 500
        for t in range(1, num_timesteps):
            timestamp = t * 10
            lib.fstWriterEmitTimeChange(ctx, timestamp)
            for i, (handle, size) in enumerate(handles):
                mod = max(1, (i + 1) // 10) if dense else (i + 1)
                if t % mod == 0:
                    if size == 1:
                        value = str(t % 2)
                    else:
                        int_val = (t * (i + 1)) % (2 ** size)
                        value = format(int_val, f"0{size}b")
                    lib.fstWriterEmitValueChange(ctx, handle, value.encode("utf-8"))
    finally:
        lib.fstWriterClose(ctx)

    return Path(path).stat().st_size


# ---------------------------------------------------------------------------
# Symlink real-world files
# ---------------------------------------------------------------------------
def symlink_real_world(data_dir: Path) -> None:
    """Create symlinks to real-world waveform files."""
    print("\nSymlinking real-world files...")
    for link_name, target in REAL_WORLD_FILES.items():
        link_path = data_dir / link_name
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        if target.exists():
            link_path.symlink_to(target)
            size = target.stat().st_size
            print(f"  {link_name} -> {target.name}  ({format_size(size)})")
        else:
            print(f"  WARNING: {target} not found, skipping {link_name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic waveform test data for benchmarking."
    )
    parser.add_argument(
        "--scale",
        choices=list(SCALE_CONFIG.keys()) + ["all"],
        default="medium",
        help="Data scale to generate (default: medium). Use 'all' for every scale.",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),
        help="Output directory for generated files.",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    scales = list(SCALE_CONFIG.keys()) if args.scale == "all" else [args.scale]

    print("=" * 60)
    print("Benchmark Test Data Generator")
    print(f"  Output directory : {data_dir}")
    print(f"  Scales           : {', '.join(scales)}")
    print("=" * 60)

    for scale in scales:
        cfg = SCALE_CONFIG[scale]
        ns = cfg["num_signals"]
        nt = cfg["num_timesteps"]
        print(f"\n--- {scale} ({ns} signals x {nt} steps, target {cfg['label']}) ---")

        # VCD
        vcd_path = str(data_dir / f"bench_{scale}.vcd")
        print(f"  Generating VCD ...", end=" ", flush=True)
        t0 = time.perf_counter()
        vcd_size = generate_vcd(vcd_path, ns, nt)
        dt = time.perf_counter() - t0
        print(f"{format_size(vcd_size)} in {dt:.2f}s")

        # FST
        fst_path = str(data_dir / f"bench_{scale}.fst")
        print(f"  Generating FST ...", end=" ", flush=True)
        t0 = time.perf_counter()
        try:
            fst_size = generate_fst(fst_path, ns, nt)
            dt = time.perf_counter() - t0
            print(f"{format_size(fst_size)} in {dt:.2f}s")
        except Exception as e:
            print(f"FAILED: {e}")
            print("  (pylibfst may not be installed; FST generation skipped)")

    # Symlink real-world files
    symlink_real_world(data_dir)

    print("\nDone. Files written to:", data_dir)


if __name__ == "__main__":
    main()
