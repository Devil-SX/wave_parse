use serde::Serialize;
use std::env;
use std::fs;
use std::io::BufReader;
use std::panic;
use std::path::{Path, PathBuf};
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

// ---------------------------------------------------------------------------
// JSON output schema
// ---------------------------------------------------------------------------

#[derive(Serialize)]
struct BenchResult {
    library: String,
    format: String,
    file: String,
    operation: String,
    times: Vec<f64>,
    mean: f64,
    min: f64,
    max: f64,
    stdev: f64,
    peak_memory_kb: u64,
    status: String,
    error: Option<String>,
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn get_peak_memory_kb() -> u64 {
    if let Ok(content) = fs::read_to_string("/proc/self/status") {
        for line in content.lines() {
            if line.starts_with("VmPeak:") {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if parts.len() >= 2 {
                    return parts[1].parse().unwrap_or(0);
                }
            }
        }
    }
    0
}

fn stats(times: &[f64]) -> (f64, f64, f64, f64) {
    if times.is_empty() {
        return (0.0, 0.0, 0.0, 0.0);
    }
    let n = times.len() as f64;
    let mean = times.iter().sum::<f64>() / n;
    let min = times.iter().cloned().fold(f64::INFINITY, f64::min);
    let max = times.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let variance = if times.len() > 1 {
        times.iter().map(|t| (t - mean).powi(2)).sum::<f64>() / (n - 1.0)
    } else {
        0.0
    };
    let stdev = variance.sqrt();
    (mean, min, max, stdev)
}

/// Run a closure with panic catching and timeout.
fn run_with_timeout<F, R>(timeout_secs: u64, f: F) -> Result<R, String>
where
    F: FnOnce() -> R + Send + 'static,
    R: Send + 'static,
{
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        let result = panic::catch_unwind(panic::AssertUnwindSafe(f));
        let _ = tx.send(result);
    });
    match rx.recv_timeout(Duration::from_secs(timeout_secs)) {
        Ok(Ok(val)) => Ok(val),
        Ok(Err(panic_err)) => {
            let msg = if let Some(s) = panic_err.downcast_ref::<&str>() {
                s.to_string()
            } else if let Some(s) = panic_err.downcast_ref::<String>() {
                s.clone()
            } else {
                "unknown panic".to_string()
            };
            Err(format!("panic: {}", msg))
        }
        Err(_) => Err("timeout".to_string()),
    }
}

/// Run a benchmark function `reps` times, returning timing results.
fn benchmark<F>(reps: usize, timeout_secs: u64, f: F) -> BenchResult
where
    F: Fn() -> Result<(), String> + Send + Clone + 'static,
{
    let mut times = Vec::new();
    let mut last_error = None;
    for _ in 0..reps {
        let ff = f.clone();
        let start = Instant::now();
        let result = run_with_timeout(timeout_secs, move || ff());
        let elapsed = start.elapsed().as_secs_f64();
        match result {
            Ok(Ok(())) => times.push(elapsed),
            Ok(Err(e)) => {
                last_error = Some(e);
            }
            Err(e) => {
                last_error = Some(e);
            }
        }
    }
    let peak_mem = get_peak_memory_kb();
    if times.is_empty() {
        BenchResult {
            library: String::new(),
            format: String::new(),
            file: String::new(),
            operation: String::new(),
            times: vec![],
            mean: 0.0,
            min: 0.0,
            max: 0.0,
            stdev: 0.0,
            peak_memory_kb: peak_mem,
            status: "error".into(),
            error: last_error,
        }
    } else {
        let (mean, min, max, stdev) = stats(&times);
        BenchResult {
            library: String::new(),
            format: String::new(),
            file: String::new(),
            operation: String::new(),
            times,
            mean,
            min,
            max,
            stdev,
            peak_memory_kb: peak_mem,
            status: "ok".into(),
            error: None,
        }
    }
}

fn emit(mut result: BenchResult, library: &str, format: &str, file: &str, operation: &str) {
    result.library = library.to_string();
    result.format = format.to_string();
    result.file = file.to_string();
    result.operation = operation.to_string();
    println!("{}", serde_json::to_string(&result).unwrap());
}

// ---------------------------------------------------------------------------
// Helpers for counting vars from rust-vcd / vcd-ng Header
// ---------------------------------------------------------------------------

fn count_vcd_vars(items: &[vcd::ScopeItem]) -> usize {
    let mut count = 0;
    for item in items {
        match item {
            vcd::ScopeItem::Var(_) => count += 1,
            vcd::ScopeItem::Scope(scope) => count += count_vcd_vars(&scope.items),
            _ => {}
        }
    }
    count
}

fn collect_vcd_codes(items: &[vcd::ScopeItem], codes: &mut Vec<vcd::IdCode>) {
    for item in items {
        match item {
            vcd::ScopeItem::Var(v) => codes.push(v.code),
            vcd::ScopeItem::Scope(scope) => collect_vcd_codes(&scope.items, codes),
            _ => {}
        }
    }
}

fn count_vcdng_vars(items: &[vcd_ng::ScopeItem]) -> usize {
    let mut count = 0;
    for item in items {
        match item {
            vcd_ng::ScopeItem::Var(_) => count += 1,
            vcd_ng::ScopeItem::Scope(scope) => count += count_vcdng_vars(&scope.children),
            _ => {}
        }
    }
    count
}

fn collect_vcdng_codes(items: &[vcd_ng::ScopeItem], codes: &mut Vec<vcd_ng::IdCode>) {
    for item in items {
        match item {
            vcd_ng::ScopeItem::Var(v) => codes.push(v.code),
            vcd_ng::ScopeItem::Scope(scope) => collect_vcdng_codes(&scope.children, codes),
            _ => {}
        }
    }
}

// ---------------------------------------------------------------------------
// Benchmark: wellen (VCD + FST)
// ---------------------------------------------------------------------------

fn bench_wellen(file: &Path, format: &str, reps: usize, timeout: u64) {
    let file_str = file.to_string_lossy().to_string();
    let lib = "wellen";

    // full_parse
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let _wave = wellen::simple::read(&p).map_err(|e| format!("{}", e))?;
            Ok(())
        });
        emit(r, lib, format, &file_str, "full_parse");
    }

    // signal_list
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let wave = wellen::simple::read(&p).map_err(|e| format!("{}", e))?;
            let count = wave.hierarchy().iter_vars().count();
            if count == 0 {
                return Err("no variables found".into());
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "signal_list");
    }

    // value_query
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let mut wave = wellen::simple::read(&p).map_err(|e| format!("{}", e))?;
            // pick up to 10 signals
            let sig_refs: Vec<wellen::SignalRef> = wave
                .hierarchy()
                .iter_vars()
                .take(10)
                .map(|v| v.signal_ref())
                .collect();
            if sig_refs.is_empty() {
                return Err("no signals to query".into());
            }
            wave.load_signals(&sig_refs);
            for sr in &sig_refs {
                let _ = wave.get_signal(*sr);
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "value_query");
    }

    // pipeline: load -> signal_list -> time_range -> value_query in one flow
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            // 1. Full parse
            let mut wave = wellen::simple::read(&p).map_err(|e| format!("{}", e))?;
            // 2. Signal list
            let var_count = wave.hierarchy().iter_vars().count();
            if var_count == 0 {
                return Err("no variables found".into());
            }
            // 3. Time range
            let _time_table = wave.time_table();
            // 4. Value query (up to 10 signals)
            let sig_refs: Vec<wellen::SignalRef> = wave
                .hierarchy()
                .iter_vars()
                .take(10)
                .map(|v| v.signal_ref())
                .collect();
            if !sig_refs.is_empty() {
                wave.load_signals(&sig_refs);
                for sr in &sig_refs {
                    let _ = wave.get_signal(*sr);
                }
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "pipeline");
    }
}

// ---------------------------------------------------------------------------
// Benchmark: rust-vcd (VCD only, streaming parser)
// ---------------------------------------------------------------------------

fn bench_rust_vcd(file: &Path, reps: usize, timeout: u64) {
    let file_str = file.to_string_lossy().to_string();
    let lib = "rust-vcd";
    let format = "vcd";

    // full_parse: parse header + iterate all commands
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut parser = vcd::Parser::new(BufReader::new(f));
            let _header = parser.parse_header().map_err(|e| format!("{}", e))?;
            for cmd in parser {
                let _ = cmd.map_err(|e| format!("{}", e))?;
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "full_parse");
    }

    // signal_list: parse header and count variables
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut parser = vcd::Parser::new(BufReader::new(f));
            let header = parser.parse_header().map_err(|e| format!("{}", e))?;
            let count = count_vcd_vars(&header.items);
            if count == 0 {
                return Err("no variables found".into());
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "signal_list");
    }

    // value_query: parse header, then stream and filter first 10 signal codes
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut parser = vcd::Parser::new(BufReader::new(f));
            let header = parser.parse_header().map_err(|e| format!("{}", e))?;
            let mut codes = Vec::new();
            collect_vcd_codes(&header.items, &mut codes);
            codes.truncate(10);
            if codes.is_empty() {
                return Err("no signals to query".into());
            }
            let mut _match_count = 0u64;
            for cmd in parser {
                let cmd = cmd.map_err(|e| format!("{}", e))?;
                match &cmd {
                    vcd::Command::ChangeScalar(id, _)
                    | vcd::Command::ChangeVector(id, _)
                    | vcd::Command::ChangeReal(id, _)
                    | vcd::Command::ChangeString(id, _) => {
                        if codes.contains(id) {
                            _match_count += 1;
                        }
                    }
                    _ => {}
                }
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "value_query");
    }

    // pipeline: continuous operation
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut parser = vcd::Parser::new(BufReader::new(f));
            // 1+2. Parse header + signal list
            let header = parser.parse_header().map_err(|e| format!("{}", e))?;
            let mut codes = Vec::new();
            collect_vcd_codes(&header.items, &mut codes);
            codes.truncate(10);
            // 3+4. Stream and filter values
            let mut _match_count = 0u64;
            for cmd in parser {
                let cmd = cmd.map_err(|e| format!("{}", e))?;
                match &cmd {
                    vcd::Command::ChangeScalar(id, _)
                    | vcd::Command::ChangeVector(id, _)
                    | vcd::Command::ChangeReal(id, _)
                    | vcd::Command::ChangeString(id, _) => {
                        if codes.contains(id) {
                            _match_count += 1;
                        }
                    }
                    _ => {}
                }
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "pipeline");
    }
}

// ---------------------------------------------------------------------------
// Benchmark: vcd-ng Parser mode (VCD only)
// ---------------------------------------------------------------------------

fn bench_vcdng_parser(file: &Path, reps: usize, timeout: u64) {
    let file_str = file.to_string_lossy().to_string();
    let lib = "vcd-ng";
    let format = "vcd";

    // full_parse
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut parser = vcd_ng::Parser::new(f);
            let _header = parser.parse_header().map_err(|e| format!("{}", e))?;
            for cmd in parser {
                let _ = cmd.map_err(|e| format!("{}", e))?;
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "full_parse");
    }

    // signal_list
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut parser = vcd_ng::Parser::new(f);
            let header = parser.parse_header().map_err(|e| format!("{}", e))?;
            let count = count_vcdng_vars(&header.items);
            if count == 0 {
                return Err("no variables found".into());
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "signal_list");
    }

    // value_query using FastFlow
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            // First pass: parse header to get signal codes
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut parser = vcd_ng::Parser::new(f);
            let header = parser.parse_header().map_err(|e| format!("{}", e))?;
            let mut codes = Vec::new();
            collect_vcdng_codes(&header.items, &mut codes);
            codes.truncate(10);
            if codes.is_empty() {
                return Err("no signals to query".into());
            }

            // Second pass: use FastFlow for fast value streaming
            let f2 = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut ff = vcd_ng::FastFlow::new(f2, 1 << 20); // 1MB buffer
            let _ = ff.first_timestamp().map_err(|e| format!("{}", e))?;
            let mut _match_count = 0u64;
            loop {
                match ff.next_token() {
                    Ok(Some(vcd_ng::FastFlowToken::Value(vc))) => {
                        if codes.contains(&vc.id) {
                            _match_count += 1;
                        }
                    }
                    Ok(Some(_)) => {}
                    Ok(None) => break,
                    Err(e) => return Err(format!("{}", e)),
                }
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "value_query");
    }

    // pipeline: header parse + FastFlow value query
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            // 1+2. Parse header + signal list
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut parser = vcd_ng::Parser::new(f);
            let header = parser.parse_header().map_err(|e| format!("{}", e))?;
            let mut codes = Vec::new();
            collect_vcdng_codes(&header.items, &mut codes);
            codes.truncate(10);
            // 3+4. FastFlow streaming query
            let f2 = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut ff = vcd_ng::FastFlow::new(f2, 1 << 20);
            let _ = ff.first_timestamp().map_err(|e| format!("{}", e))?;
            let mut _match_count = 0u64;
            loop {
                match ff.next_token() {
                    Ok(Some(vcd_ng::FastFlowToken::Value(vc))) => {
                        if codes.contains(&vc.id) {
                            _match_count += 1;
                        }
                    }
                    Ok(Some(_)) => {}
                    Ok(None) => break,
                    Err(e) => return Err(format!("{}", e)),
                }
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "pipeline");
    }
}

// ---------------------------------------------------------------------------
// Benchmark: fst-reader (FST only, pure Rust)
// ---------------------------------------------------------------------------

fn bench_fst_reader(file: &Path, reps: usize, timeout: u64) {
    let file_str = file.to_string_lossy().to_string();
    let lib = "fst-reader";
    let format = "fst";

    // full_parse: open + read hierarchy + read all signals
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut reader =
                fst_reader::FstReader::open(BufReader::new(f)).map_err(|e| format!("{}", e))?;
            let mut _var_count = 0u64;
            reader
                .read_hierarchy(|entry| {
                    if let fst_reader::FstHierarchyEntry::Var { .. } = entry {
                        _var_count += 1;
                    }
                })
                .map_err(|e| format!("{}", e))?;
            let filter = fst_reader::FstFilter::all();
            let mut _change_count = 0u64;
            reader
                .read_signals(&filter, |_time, _handle, _value| {
                    _change_count += 1;
                })
                .map_err(|e| format!("{}", e))?;
            Ok(())
        });
        emit(r, lib, format, &file_str, "full_parse");
    }

    // signal_list
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut reader =
                fst_reader::FstReader::open(BufReader::new(f)).map_err(|e| format!("{}", e))?;
            let mut var_count = 0u64;
            reader
                .read_hierarchy(|entry| {
                    if let fst_reader::FstHierarchyEntry::Var { .. } = entry {
                        var_count += 1;
                    }
                })
                .map_err(|e| format!("{}", e))?;
            if var_count == 0 {
                return Err("no variables found".into());
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "signal_list");
    }

    // value_query: read first 10 signal handles
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut reader =
                fst_reader::FstReader::open(BufReader::new(f)).map_err(|e| format!("{}", e))?;
            let mut handles = Vec::new();
            reader
                .read_hierarchy(|entry| {
                    if let fst_reader::FstHierarchyEntry::Var { handle, .. } = entry {
                        if handles.len() < 10 {
                            handles.push(handle);
                        }
                    }
                })
                .map_err(|e| format!("{}", e))?;
            if handles.is_empty() {
                return Err("no signals to query".into());
            }
            let filter = fst_reader::FstFilter::filter_signals(handles);
            let mut _change_count = 0u64;
            reader
                .read_signals(&filter, |_time, _handle, _value| {
                    _change_count += 1;
                })
                .map_err(|e| format!("{}", e))?;
            Ok(())
        });
        emit(r, lib, format, &file_str, "value_query");
    }

    // pipeline
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let f = fs::File::open(&p).map_err(|e| format!("{}", e))?;
            let mut reader =
                fst_reader::FstReader::open(BufReader::new(f)).map_err(|e| format!("{}", e))?;
            // 1+2. Hierarchy + signal list
            let mut handles = Vec::new();
            reader
                .read_hierarchy(|entry| {
                    if let fst_reader::FstHierarchyEntry::Var { handle, .. } = entry {
                        if handles.len() < 10 {
                            handles.push(handle);
                        }
                    }
                })
                .map_err(|e| format!("{}", e))?;
            // 3+4. Read values for selected signals
            if !handles.is_empty() {
                let filter = fst_reader::FstFilter::filter_signals(handles);
                let mut _change_count = 0u64;
                reader
                    .read_signals(&filter, |_time, _handle, _value| {
                        _change_count += 1;
                    })
                    .map_err(|e| format!("{}", e))?;
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "pipeline");
    }
}

// ---------------------------------------------------------------------------
// Benchmark: fstapi (FST only, C bindings)
// ---------------------------------------------------------------------------

fn bench_fstapi(file: &Path, reps: usize, timeout: u64) {
    let file_str = file.to_string_lossy().to_string();
    let lib = "fstapi";
    let format = "fst";

    // full_parse: open + iterate vars + iterate all blocks
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let mut reader = fstapi::Reader::open(&p).map_err(|e| format!("{}", e))?;
            for var_result in reader.vars() {
                let _ = var_result.map_err(|e| format!("{}", e))?;
            }
            reader.set_mask_all();
            let mut _change_count = 0u64;
            reader
                .for_each_block(|_time, _handle, _value, _var_len| {
                    _change_count += 1;
                })
                .map_err(|e| format!("{}", e))?;
            Ok(())
        });
        emit(r, lib, format, &file_str, "full_parse");
    }

    // signal_list
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let mut reader = fstapi::Reader::open(&p).map_err(|e| format!("{}", e))?;
            let mut var_count = 0u64;
            for var_result in reader.vars() {
                let _ = var_result.map_err(|e| format!("{}", e))?;
                var_count += 1;
            }
            if var_count == 0 {
                return Err("no variables found".into());
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "signal_list");
    }

    // value_query: collect first 10 handles, mask them, iterate
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let mut reader = fstapi::Reader::open(&p).map_err(|e| format!("{}", e))?;
            let mut handles = Vec::new();
            for var_result in reader.vars() {
                let (_, var) = var_result.map_err(|e| format!("{}", e))?;
                if handles.len() < 10 {
                    handles.push(var.handle());
                }
            }
            if handles.is_empty() {
                return Err("no signals to query".into());
            }
            reader.clear_mask_all();
            for h in &handles {
                reader.set_mask(*h);
            }
            let mut _change_count = 0u64;
            reader
                .for_each_block(|_time, _handle, _value, _var_len| {
                    _change_count += 1;
                })
                .map_err(|e| format!("{}", e))?;
            Ok(())
        });
        emit(r, lib, format, &file_str, "value_query");
    }

    // pipeline
    {
        let p = file_str.clone();
        let r = benchmark(reps, timeout, move || {
            let mut reader = fstapi::Reader::open(&p).map_err(|e| format!("{}", e))?;
            // 1+2. Signal list
            let mut handles = Vec::new();
            for var_result in reader.vars() {
                let (_, var) = var_result.map_err(|e| format!("{}", e))?;
                if handles.len() < 10 {
                    handles.push(var.handle());
                }
            }
            // 3+4. Value query
            if !handles.is_empty() {
                reader.clear_mask_all();
                for h in &handles {
                    reader.set_mask(*h);
                }
                let mut _change_count = 0u64;
                reader
                    .for_each_block(|_time, _handle, _value, _var_len| {
                        _change_count += 1;
                    })
                    .map_err(|e| format!("{}", e))?;
            }
            Ok(())
        });
        emit(r, lib, format, &file_str, "pipeline");
    }
}

// ---------------------------------------------------------------------------
// Discover test files
// ---------------------------------------------------------------------------

fn discover_files(data_dir: &Path) -> (Vec<PathBuf>, Vec<PathBuf>) {
    let mut vcd_files = Vec::new();
    let mut fst_files = Vec::new();
    if let Ok(entries) = fs::read_dir(data_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if let Some(ext) = path.extension() {
                match ext.to_string_lossy().as_ref() {
                    "vcd" => vcd_files.push(path),
                    "fst" => fst_files.push(path),
                    _ => {}
                }
            }
        }
    }
    vcd_files.sort();
    fst_files.sort();
    (vcd_files, fst_files)
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

fn main() {
    let args: Vec<String> = env::args().collect();

    let data_dir = env::var("DATA_DIR")
        .or_else(|_| args.get(1).cloned().ok_or(()))
        .unwrap_or_else(|_| "data".to_string());

    let _scale: usize = env::var("SCALE")
        .ok()
        .and_then(|s| s.parse().ok())
        .or_else(|| args.get(2).and_then(|s| s.parse().ok()))
        .unwrap_or(1);

    let reps: usize = env::var("REPS")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(3);

    let timeout: u64 = env::var("TIMEOUT")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(300);

    let data_path = PathBuf::from(&data_dir);
    let (vcd_files, fst_files) = discover_files(&data_path);

    eprintln!(
        "wave-bench: data_dir={}, reps={}, timeout={}s",
        data_dir, reps, timeout
    );
    eprintln!(
        "  Found {} VCD files, {} FST files",
        vcd_files.len(),
        fst_files.len()
    );

    // --- VCD benchmarks ---
    for vcd_file in &vcd_files {
        eprintln!("  Benchmarking VCD: {}", vcd_file.display());

        eprintln!("    wellen...");
        bench_wellen(vcd_file, "vcd", reps, timeout);

        eprintln!("    rust-vcd...");
        bench_rust_vcd(vcd_file, reps, timeout);

        eprintln!("    vcd-ng...");
        bench_vcdng_parser(vcd_file, reps, timeout);
    }

    // --- FST benchmarks ---
    for fst_file in &fst_files {
        eprintln!("  Benchmarking FST: {}", fst_file.display());

        eprintln!("    wellen...");
        bench_wellen(fst_file, "fst", reps, timeout);

        eprintln!("    fst-reader...");
        bench_fst_reader(fst_file, reps, timeout);

        eprintln!("    fstapi...");
        bench_fstapi(fst_file, reps, timeout);
    }

    eprintln!("wave-bench: done.");
}
