# VCD/FST Library Benchmark Report

- **Scale**: small+medium+large
- **Date**: 2026-02-17 13:07:26
- **Total benchmarks**: 220
- **Passed**: 198, **Failed/Skipped**: 22

## 1. Full Parse Performance

### File: `bench_large.fst` (12.8MB)

| Library | Language | Format | Time | Throughput | Memory |
|---------|----------|--------|------|------------|--------|
| wellen | Rust | fst | 1.41ms | 9107.3 MB/s | 2099516KB |
| pywellen | Python | vcd+fst | 1.65ms | 7792.3 MB/s | N/A |
| pylibfst | Python | fst | 4.90ms | 2622.4 MB/s | 576KB |
| fstapi | Rust | fst | 276.72ms | 46.4 MB/s | 2099516KB |
| fst-reader | Rust | fst | 315.67ms | 40.7 MB/s | 2099516KB |

```
  wellen          |#| 1.41ms
  pywellen        |#| 1.65ms
  pylibfst        |#| 4.90ms
  fstapi          |##########################| 276.72ms
  fst-reader      |##############################| 315.67ms
```

### File: `bench_large.vcd` (175.7MB)

| Library | Language | Format | Time | Throughput | Memory |
|---------|----------|--------|------|------------|--------|
| pywellen | Python | vcd+fst | 139.97ms | 1255.4 MB/s | 237908KB |
| wellen | Rust | vcd | 143.32ms | 1226.1 MB/s | 1939912KB |
| rust-vcd | Rust | vcd | 1.452s | 121.0 MB/s | 1939912KB |
| vcdvcd | Python | vcd | 6.878s | 25.5 MB/s | 1394304KB |
| vcd-ng | Rust | vcd | 38.599s | 4.6 MB/s | 1939912KB |

```
  pywellen        |#| 139.97ms
  wellen          |#| 143.32ms
  rust-vcd        |#| 1.452s
  vcdvcd          |#####| 6.878s
  vcd-ng          |##############################| 38.599s
```

### File: `bench_medium.fst` (56.9KB)

| Library | Language | Format | Time | Throughput | Memory |
|---------|----------|--------|------|------------|--------|
| pywellen | Python | vcd+fst | 112.0us | 495.8 MB/s | N/A |
| wellen | Rust | fst | 217.0us | 255.9 MB/s | 1777292KB |
| pylibfst | Python | fst | 981.0us | 56.6 MB/s | 192KB |
| fstapi | Rust | fst | 1.44ms | 38.6 MB/s | 1777292KB |
| fst-reader | Rust | fst | 1.96ms | 28.4 MB/s | 1777292KB |

```
  pywellen        |#| 112.0us
  wellen          |###| 217.0us
  pylibfst        |###############| 981.0us
  fstapi          |######################| 1.44ms
  fst-reader      |##############################| 1.96ms
```

### File: `bench_medium.vcd` (636.9KB)

| Library | Language | Format | Time | Throughput | Memory |
|---------|----------|--------|------|------------|--------|
| wellen | Rust | vcd | 2.67ms | 233.3 MB/s | 1762684KB |
| pywellen | Python | vcd+fst | 2.76ms | 225.6 MB/s | 960KB |
| rust-vcd | Rust | vcd | 4.41ms | 140.9 MB/s | 1762684KB |
| vcdvcd | Python | vcd | 45.78ms | 13.6 MB/s | 8064KB |
| vcd-ng | Rust | vcd | 126.09ms | 4.9 MB/s | 1762684KB |

```
  wellen          |#| 2.67ms
  pywellen        |#| 2.76ms
  rust-vcd        |#| 4.41ms
  vcdvcd          |##########| 45.78ms
  vcd-ng          |##############################| 126.09ms
```

### File: `bench_small.fst` (5.5KB)

| Library | Language | Format | Time | Throughput | Memory |
|---------|----------|--------|------|------------|--------|
| pywellen | Python | vcd+fst | 63.0us | 84.6 MB/s | N/A |
| wellen | Rust | fst | 143.3us | 37.2 MB/s | 1760024KB |
| fst-reader | Rust | fst | 334.2us | 15.9 MB/s | 1760024KB |
| fstapi | Rust | fst | 334.8us | 15.9 MB/s | 1760024KB |
| pylibfst | Python | fst | 977.0us | 5.5 MB/s | 192KB |

```
  pywellen        |#| 63.0us
  wellen          |####| 143.3us
  fst-reader      |##########| 334.2us
  fstapi          |##########| 334.8us
  pylibfst        |##############################| 977.0us
```

### File: `bench_small.vcd` (43.8KB)

| Library | Language | Format | Time | Throughput | Memory |
|---------|----------|--------|------|------------|--------|
| rust-vcd | Rust | vcd | 401.0us | 106.6 MB/s | 1760024KB |
| wellen | Rust | vcd | 805.7us | 53.1 MB/s | 1760024KB |
| pywellen | Python | vcd+fst | 905.0us | 47.2 MB/s | 576KB |
| vcdvcd | Python | vcd | 8.17ms | 5.2 MB/s | 2304KB |
| vcd-ng | Rust | vcd | 10.14ms | 4.2 MB/s | 1760024KB |

```
  rust-vcd        |#| 401.0us
  wellen          |##| 805.7us
  pywellen        |##| 905.0us
  vcdvcd          |########################| 8.17ms
  vcd-ng          |##############################| 10.14ms
```

### File: `real_world_large.vcd` (48.7MB)

| Library | Language | Format | Time | Throughput | Memory |
|---------|----------|--------|------|------------|--------|
| pywellen | Python | vcd+fst | 342.44ms | 142.3 MB/s | 141764KB |
| rust-vcd | Rust | vcd | 366.61ms | 132.9 MB/s | 2099516KB |
| wellen | Rust | vcd | 408.55ms | 119.3 MB/s | 2099516KB |
| vcdvcd | Python | vcd | 5.591s | 8.7 MB/s | N/A |
| vcd-ng | Rust | vcd | 10.652s | 4.6 MB/s | 2099516KB |

```
  pywellen        |#| 342.44ms
  rust-vcd        |#| 366.61ms
  wellen          |#| 408.55ms
  vcdvcd          |###############| 5.591s
  vcd-ng          |##############################| 10.652s
```

### File: `real_world_medium.fst` (569.0KB)

| Library | Language | Format | Time | Throughput | Memory |
|---------|----------|--------|------|------------|--------|
| pywellen | Python | vcd+fst | 5.68ms | 97.8 MB/s | N/A |
| wellen | Rust | fst | 7.80ms | 71.3 MB/s | 1777292KB |
| fstapi | Rust | fst | 25.76ms | 21.6 MB/s | 1777292KB |
| fst-reader | Rust | fst | 28.74ms | 19.3 MB/s | 1777292KB |
| pylibfst | Python | fst | 47.45ms | 11.7 MB/s | 11844KB |

```
  pywellen        |###| 5.68ms
  wellen          |####| 7.80ms
  fstapi          |################| 25.76ms
  fst-reader      |##################| 28.74ms
  pylibfst        |##############################| 47.45ms
```

### File: `real_world_medium.vcd` (13.4MB)

| Library | Language | Format | Time | Throughput | Memory |
|---------|----------|--------|------|------------|--------|
| wellen | Rust | vcd | 19.03ms | 703.3 MB/s | 1777292KB |
| pywellen | Python | vcd+fst | 19.78ms | 676.6 MB/s | 31592KB |
| rust-vcd | Rust | vcd | 74.60ms | 179.4 MB/s | 1777292KB |
| vcdvcd | Python | vcd | 410.04ms | 32.6 MB/s | 69196KB |
| vcd-ng | Rust | vcd | 2.804s | 4.8 MB/s | 1777292KB |

```
  wellen          |#| 19.03ms
  pywellen        |#| 19.78ms
  rust-vcd        |#| 74.60ms
  vcdvcd          |####| 410.04ms
  vcd-ng          |##############################| 2.804s
```

## 2. Signal List Retrieval Performance

### File: `bench_large.fst`

| Library | Language | Time | Stdev |
|---------|----------|------|-------|
| fst-reader | Rust | 235.6us | 75.5us |
| fstapi | Rust | 644.0us | 60.7us |
| wellen | Rust | 961.4us | 124.1us |
| pywellen | Python | 2.16ms | 25.0us |
| pylibfst | Python | 3.72ms | 294.0us |

### File: `bench_large.vcd`

| Library | Language | Time | Stdev |
|---------|----------|------|-------|
| rust-vcd | Rust | 369.7us | 46.7us |
| vcd-ng | Rust | 11.30ms | 299.9us |
| pywellen | Python | 135.62ms | 3.22ms |
| wellen | Rust | 137.04ms | 3.94ms |
| vcdvcd | Python | 7.052s | 200.20ms |

### File: `bench_medium.fst`

| Library | Language | Time | Stdev |
|---------|----------|------|-------|
| fst-reader | Rust | 97.5us | 20.8us |
| pywellen | Python | 121.0us | 27.0us |
| wellen | Rust | 172.9us | 11.1us |
| fstapi | Rust | 234.4us | 71.0us |
| pylibfst | Python | 366.0us | 8.0us |

### File: `bench_medium.vcd`

| Library | Language | Time | Stdev |
|---------|----------|------|-------|
| rust-vcd | Rust | 163.9us | 38.7us |
| vcd-ng | Rust | 1.23ms | 49.5us |
| pywellen | Python | 1.91ms | 157.0us |
| wellen | Rust | 2.72ms | 1.15ms |
| vcdvcd | Python | 38.04ms | 11.74ms |

### File: `bench_small.fst`

| Library | Language | Time | Stdev |
|---------|----------|------|-------|
| pywellen | Python | 68.0us | 8.0us |
| wellen | Rust | 115.2us | 22.0us |
| fst-reader | Rust | 115.4us | 21.4us |
| fstapi | Rust | 151.4us | 38.7us |
| pylibfst | Python | 304.0us | 22.0us |

### File: `bench_small.vcd`

| Library | Language | Time | Stdev |
|---------|----------|------|-------|
| rust-vcd | Rust | 75.9us | 13.3us |
| vcd-ng | Rust | 363.1us | 15.3us |
| pywellen | Python | 421.0us | 11.0us |
| wellen | Rust | 432.9us | 37.2us |
| vcdvcd | Python | 3.11ms | 20.0us |

### File: `real_world_large.vcd`

| Library | Language | Time | Stdev |
|---------|----------|------|-------|
| wellen | Rust | 338.79ms | 5.55ms |
| rust-vcd | Rust | 401.66ms | 58.11ms |
| pywellen | Python | 632.08ms | 34.09ms |
| vcdvcd | Python | 5.627s | 201.76ms |
| vcd-ng | Rust | 10.836s | 324.34ms |

### File: `real_world_medium.fst`

| Library | Language | Time | Stdev |
|---------|----------|------|-------|
| fst-reader | Rust | 2.11ms | 33.0us |
| wellen | Rust | 6.81ms | 202.5us |
| pywellen | Python | 8.14ms | 129.0us |
| fstapi | Rust | 10.41ms | 347.5us |
| pylibfst | Python | 47.50ms | 1.35ms |

### File: `real_world_medium.vcd`

| Library | Language | Time | Stdev |
|---------|----------|------|-------|
| rust-vcd | Rust | 14.62ms | 734.7us |
| wellen | Rust | 18.18ms | 667.9us |
| pywellen | Python | 20.13ms | 820.0us |
| vcdvcd | Python | 300.00ms | 23.20ms |
| vcd-ng | Rust | 333.52ms | 19.50ms |

## 3. Value Query Performance

### File: `bench_large.fst` (12.8MB)

| Library | Language | Format | Time | Stdev | Memory |
|---------|----------|--------|------|-------|--------|
| fstapi | Rust | fst | 23.25ms | 741.9us | 2099516KB |
| fst-reader | Rust | fst | 29.47ms | 1.57ms | 2099516KB |
| wellen | Rust | fst | 78.63ms | 6.16ms | 2099516KB |
| pywellen | Python | vcd+fst | 80.21ms | 25.26ms | N/A |
| pylibfst | Python | fst | 221.90ms | 59.00ms | 2884KB |

```
  fstapi          |###| 23.25ms
  fst-reader      |###| 29.47ms
  wellen          |##########| 78.63ms
  pywellen        |##########| 80.21ms
  pylibfst        |##############################| 221.90ms
```

### File: `bench_large.vcd` (175.7MB)

| Library | Language | Format | Time | Stdev | Memory |
|---------|----------|--------|------|-------|--------|
| vcd-ng | Rust | vcd | 163.34ms | 41.40ms | 1939912KB |
| wellen | Rust | vcd | 174.72ms | 6.99ms | 1939912KB |
| pywellen | Python | vcd+fst | 183.07ms | 3.74ms | 1040KB |
| rust-vcd | Rust | vcd | 1.545s | 119.95ms | 1939912KB |
| vcdvcd | Python | vcd | 6.838s | 252.90ms | N/A |

```
  vcd-ng          |#| 163.34ms
  wellen          |#| 174.72ms
  pywellen        |#| 183.07ms
  rust-vcd        |######| 1.545s
  vcdvcd          |##############################| 6.838s
```

### File: `bench_medium.fst` (56.9KB)

| Library | Language | Format | Time | Stdev | Memory |
|---------|----------|--------|------|-------|--------|
| fstapi | Rust | fst | 566.8us | 12.4us | 1777292KB |
| fst-reader | Rust | fst | 585.1us | 27.8us | 1777292KB |
| wellen | Rust | fst | 1.27ms | 63.6us | 1777292KB |
| pywellen | Python | vcd+fst | 3.23ms | 53.0us | N/A |
| pylibfst | Python | fst | 7.73ms | 520.0us | 384KB |

```
  fstapi          |##| 566.8us
  fst-reader      |##| 585.1us
  wellen          |####| 1.27ms
  pywellen        |############| 3.23ms
  pylibfst        |##############################| 7.73ms
```

### File: `bench_medium.vcd` (636.9KB)

| Library | Language | Format | Time | Stdev | Memory |
|---------|----------|--------|------|-------|--------|
| wellen | Rust | vcd | 2.19ms | 160.6us | 1762684KB |
| vcd-ng | Rust | vcd | 2.21ms | 171.2us | 1763072KB |
| pywellen | Python | vcd+fst | 4.37ms | 156.0us | N/A |
| rust-vcd | Rust | vcd | 4.56ms | 75.9us | 1762684KB |
| vcdvcd | Python | vcd | 25.50ms | 3.08ms | N/A |

```
  wellen          |##| 2.19ms
  vcd-ng          |##| 2.21ms
  pywellen        |#####| 4.37ms
  rust-vcd        |#####| 4.56ms
  vcdvcd          |##############################| 25.50ms
```

### File: `bench_small.fst` (5.5KB)

| Library | Language | Format | Time | Stdev | Memory |
|---------|----------|--------|------|-------|--------|
| fstapi | Rust | fst | 210.9us | 4.8us | 1760024KB |
| wellen | Rust | fst | 289.2us | 21.4us | 1760024KB |
| fst-reader | Rust | fst | 509.9us | 582.8us | 1760024KB |
| pywellen | Python | vcd+fst | 876.0us | 548.0us | N/A |
| pylibfst | Python | fst | 1.40ms | 152.0us | N/A |

```
  fstapi          |####| 210.9us
  wellen          |######| 289.2us
  fst-reader      |##########| 509.9us
  pywellen        |##################| 876.0us
  pylibfst        |##############################| 1.40ms
```

### File: `bench_small.vcd` (43.8KB)

| Library | Language | Format | Time | Stdev | Memory |
|---------|----------|--------|------|-------|--------|
| rust-vcd | Rust | vcd | 382.7us | 5.3us | 1760024KB |
| vcd-ng | Rust | vcd | 751.8us | 530.9us | 1760024KB |
| pywellen | Python | vcd+fst | 812.0us | 21.0us | N/A |
| wellen | Rust | vcd | 813.9us | 572.6us | 1760024KB |
| vcdvcd | Python | vcd | 4.33ms | 245.0us | N/A |

```
  rust-vcd        |##| 382.7us
  vcd-ng          |#####| 751.8us
  pywellen        |#####| 812.0us
  wellen          |#####| 813.9us
  vcdvcd          |##############################| 4.33ms
```

### File: `real_world_large.vcd` (48.7MB)

| Library | Language | Format | Time | Stdev | Memory |
|---------|----------|--------|------|-------|--------|
| wellen | Rust | vcd | 349.60ms | 16.81ms | 2099516KB |
| rust-vcd | Rust | vcd | 391.59ms | 23.28ms | 2099516KB |
| pywellen | Python | vcd+fst | 455.19ms | 9.71ms | N/A |
| vcdvcd | Python | vcd | 5.681s | 31.66ms | N/A |
| vcd-ng | Rust | vcd | 11.295s | 365.69ms | 2099516KB |

```
  wellen          |#| 349.60ms
  rust-vcd        |#| 391.59ms
  pywellen        |#| 455.19ms
  vcdvcd          |###############| 5.681s
  vcd-ng          |##############################| 11.295s
```

### File: `real_world_medium.fst` (569.0KB)

| Library | Language | Format | Time | Stdev | Memory |
|---------|----------|--------|------|-------|--------|
| fst-reader | Rust | fst | 2.26ms | 32.1us | 1777292KB |
| pywellen | Python | vcd+fst | 7.93ms | 564.0us | N/A |
| wellen | Rust | fst | 8.29ms | 375.1us | 1777292KB |
| fstapi | Rust | fst | 10.45ms | 191.6us | 1777292KB |
| pylibfst | Python | fst | 50.66ms | 1.51ms | 2688KB |

```
  fst-reader      |#| 2.26ms
  pywellen        |####| 7.93ms
  wellen          |####| 8.29ms
  fstapi          |######| 10.45ms
  pylibfst        |##############################| 50.66ms
```

### File: `real_world_medium.vcd` (13.4MB)

| Library | Language | Format | Time | Stdev | Memory |
|---------|----------|--------|------|-------|--------|
| pywellen | Python | vcd+fst | 18.27ms | 416.0us | 1644KB |
| wellen | Rust | vcd | 18.38ms | 487.5us | 1777292KB |
| rust-vcd | Rust | vcd | 76.01ms | 13.72ms | 1777292KB |
| vcdvcd | Python | vcd | 353.44ms | 49.43ms | 40KB |
| vcd-ng | Rust | vcd | 361.73ms | 38.20ms | 1777292KB |

```
  pywellen        |#| 18.27ms
  wellen          |#| 18.38ms
  rust-vcd        |######| 76.01ms
  vcdvcd          |#############################| 353.44ms
  vcd-ng          |##############################| 361.73ms
```

## 4. Pipeline Performance (Load + Signal List + Time Range + Value Query)

### File: `bench_large.fst` (12.8MB)

| Library | Language | Format | Pipeline Time | Throughput | Memory |
|---------|----------|--------|---------------|------------|--------|
| fstapi | Rust | fst | 22.66ms | 566.8 MB/s | 2099516KB |
| fst-reader | Rust | fst | 28.58ms | 449.3 MB/s | 2099516KB |
| pywellen | Python | vcd+fst | 35.81ms | 358.6 MB/s | N/A |
| pylibfst | Python | fst | 52.03ms | 246.8 MB/s | N/A |
| wellen | Rust | fst | 74.76ms | 171.8 MB/s | 2099516KB |

```
  fstapi          |#########| 22.66ms
  fst-reader      |###########| 28.58ms
  pywellen        |##############| 35.81ms
  pylibfst        |####################| 52.03ms
  wellen          |##############################| 74.76ms
```

### File: `bench_large.vcd` (175.7MB)

| Library | Language | Format | Pipeline Time | Throughput | Memory |
|---------|----------|--------|---------------|------------|--------|
| pywellen | Python | vcd+fst | 166.25ms | 1057.0 MB/s | N/A |
| wellen | Rust | vcd | 175.49ms | 1001.3 MB/s | 1939912KB |
| vcd-ng | Rust | vcd | 180.82ms | 971.8 MB/s | 1939912KB |
| rust-vcd | Rust | vcd | 1.389s | 126.5 MB/s | 1939912KB |
| vcdvcd | Python | vcd | 6.773s | 25.9 MB/s | N/A |

```
  pywellen        |#| 166.25ms
  wellen          |#| 175.49ms
  vcd-ng          |#| 180.82ms
  rust-vcd        |######| 1.389s
  vcdvcd          |##############################| 6.773s
```

### File: `bench_medium.fst` (56.9KB)

| Library | Language | Format | Pipeline Time | Throughput | Memory |
|---------|----------|--------|---------------|------------|--------|
| fstapi | Rust | fst | 586.3us | 94.7 MB/s | 1777292KB |
| fst-reader | Rust | fst | 611.8us | 90.8 MB/s | 1777292KB |
| wellen | Rust | fst | 1.22ms | 45.4 MB/s | 1777292KB |
| pywellen | Python | vcd+fst | 1.81ms | 30.6 MB/s | N/A |
| pylibfst | Python | fst | 2.98ms | 18.6 MB/s | N/A |

```
  fstapi          |#####| 586.3us
  fst-reader      |######| 611.8us
  wellen          |############| 1.22ms
  pywellen        |##################| 1.81ms
  pylibfst        |##############################| 2.98ms
```

### File: `bench_medium.vcd` (636.9KB)

| Library | Language | Format | Pipeline Time | Throughput | Memory |
|---------|----------|--------|---------------|------------|--------|
| vcd-ng | Rust | vcd | 2.00ms | 311.5 MB/s | 1763072KB |
| wellen | Rust | vcd | 2.19ms | 284.6 MB/s | 1762684KB |
| pywellen | Python | vcd+fst | 3.26ms | 190.6 MB/s | N/A |
| rust-vcd | Rust | vcd | 4.52ms | 137.5 MB/s | 1762684KB |
| vcdvcd | Python | vcd | 20.76ms | 30.0 MB/s | 8KB |

```
  vcd-ng          |##| 2.00ms
  wellen          |###| 2.19ms
  pywellen        |####| 3.26ms
  rust-vcd        |######| 4.52ms
  vcdvcd          |##############################| 20.76ms
```

### File: `bench_small.fst` (5.5KB)

| Library | Language | Format | Pipeline Time | Throughput | Memory |
|---------|----------|--------|---------------|------------|--------|
| fstapi | Rust | fst | 183.7us | 29.0 MB/s | 1760024KB |
| fst-reader | Rust | fst | 246.4us | 21.6 MB/s | 1760024KB |
| wellen | Rust | fst | 296.8us | 18.0 MB/s | 1760024KB |
| pywellen | Python | vcd+fst | 328.0us | 16.3 MB/s | N/A |
| pylibfst | Python | fst | 695.0us | 7.7 MB/s | N/A |

```
  fstapi          |#######| 183.7us
  fst-reader      |##########| 246.4us
  wellen          |############| 296.8us
  pywellen        |##############| 328.0us
  pylibfst        |##############################| 695.0us
```

### File: `bench_small.vcd` (43.8KB)

| Library | Language | Format | Pipeline Time | Throughput | Memory |
|---------|----------|--------|---------------|------------|--------|
| vcd-ng | Rust | vcd | 521.2us | 82.0 MB/s | 1760024KB |
| wellen | Rust | vcd | 553.9us | 77.2 MB/s | 1760024KB |
| pywellen | Python | vcd+fst | 648.0us | 66.0 MB/s | N/A |
| rust-vcd | Rust | vcd | 758.4us | 56.4 MB/s | 1760024KB |
| vcdvcd | Python | vcd | 2.98ms | 14.3 MB/s | N/A |

```
  vcd-ng          |#####| 521.2us
  wellen          |#####| 553.9us
  pywellen        |######| 648.0us
  rust-vcd        |#######| 758.4us
  vcdvcd          |##############################| 2.98ms
```

### File: `real_world_large.vcd` (48.7MB)

| Library | Language | Format | Pipeline Time | Throughput | Memory |
|---------|----------|--------|---------------|------------|--------|
| wellen | Rust | vcd | 414.08ms | 117.7 MB/s | 2099516KB |
| rust-vcd | Rust | vcd | 459.60ms | 106.0 MB/s | 2099516KB |
| pywellen | Python | vcd+fst | 643.41ms | 75.8 MB/s | N/A |
| vcdvcd | Python | vcd | 5.724s | 8.5 MB/s | N/A |
| vcd-ng | Rust | vcd | 11.005s | 4.4 MB/s | 2099516KB |

```
  wellen          |#| 414.08ms
  rust-vcd        |#| 459.60ms
  pywellen        |#| 643.41ms
  vcdvcd          |###############| 5.724s
  vcd-ng          |##############################| 11.005s
```

### File: `real_world_medium.fst` (569.0KB)

| Library | Language | Format | Pipeline Time | Throughput | Memory |
|---------|----------|--------|---------------|------------|--------|
| fst-reader | Rust | fst | 2.23ms | 249.6 MB/s | 1777292KB |
| pywellen | Python | vcd+fst | 6.44ms | 86.3 MB/s | N/A |
| wellen | Rust | fst | 8.72ms | 63.8 MB/s | 1777292KB |
| fstapi | Rust | fst | 13.80ms | 40.3 MB/s | 1777292KB |
| pylibfst | Python | fst | 46.44ms | 12.0 MB/s | 64KB |

```
  fst-reader      |#| 2.23ms
  pywellen        |####| 6.44ms
  wellen          |#####| 8.72ms
  fstapi          |########| 13.80ms
  pylibfst        |##############################| 46.44ms
```

### File: `real_world_medium.vcd` (13.4MB)

| Library | Language | Format | Pipeline Time | Throughput | Memory |
|---------|----------|--------|---------------|------------|--------|
| pywellen | Python | vcd+fst | 18.71ms | 715.5 MB/s | 380KB |
| wellen | Rust | vcd | 18.85ms | 710.1 MB/s | 1777292KB |
| rust-vcd | Rust | vcd | 69.24ms | 193.3 MB/s | 1777292KB |
| vcdvcd | Python | vcd | 331.44ms | 40.4 MB/s | N/A |
| vcd-ng | Rust | vcd | 332.95ms | 40.2 MB/s | 1777292KB |

```
  pywellen        |#| 18.71ms
  wellen          |#| 18.85ms
  rust-vcd        |######| 69.24ms
  vcdvcd          |#############################| 331.44ms
  vcd-ng          |##############################| 332.95ms
```

## 5. Overall Ranking (by Full Parse Speed)

| Rank | Library | Avg Parse Time | Files Tested |
|------|---------|----------------|--------------|
| 1 | pylibfst (Python) (fastest) | 13.58ms | 4 |
| 2 | pywellen (Python) | 57.04ms | 9 |
| 3 | wellen (Rust) | 64.88ms | 9 |
| 4 | fstapi (Rust) | 76.06ms | 4 |
| 5 | fst-reader (Rust) | 86.68ms | 4 |
| 6 | rust-vcd (Rust) | 379.63ms | 5 |
| 7 | vcdvcd (Python) | 2.587s | 5 |
| 8 | vcd-ng (Rust) | 10.438s | 5 |

**Fastest**: pylibfst (Python) at 13.58ms average

- pywellen (Python): 4.2x slower
- wellen (Rust): 4.8x slower
- fstapi (Rust): 5.6x slower
- fst-reader (Rust): 6.4x slower
- rust-vcd (Rust): 28.0x slower
- vcdvcd (Python): 190.5x slower
- vcd-ng (Rust): 768.9x slower

## 6. Errors and Failures

| Library | Test | Status | Error |
|---------|------|--------|-------|
| pylibfst | full_parse | error | Failed to open FST file: /home/sdu/wave_parse/benchmarks/data/large/real_world_l |
| pylibfst | signal_list | error | Failed to open FST file: /home/sdu/wave_parse/benchmarks/data/large/real_world_l |
| pylibfst | time_range | error | Failed to open FST file: /home/sdu/wave_parse/benchmarks/data/large/real_world_l |
| pylibfst | value_query | error | Failed to open FST file: /home/sdu/wave_parse/benchmarks/data/large/real_world_l |
| pylibfst | pipeline | error | Failed to open FST file: /home/sdu/wave_parse/benchmarks/data/large/real_world_l |
| pywellen | full_parse_fst | error | io error |
| pywellen | signal_list_fst | error | io error |
| pywellen | time_range_fst | error | io error |
| pywellen | value_query_fst | error | io error |
| pywellen | pipeline_fst | error | io error |
| wellen | full_parse | error | io error |
| wellen | signal_list | error | io error |
| wellen | value_query | error | io error |
| wellen | pipeline | error | io error |
| fst-reader | full_parse | error | The FST file is incomplete: geometry block is missing. |
| fst-reader | signal_list | error | The FST file is incomplete: geometry block is missing. |
| fst-reader | value_query | error | The FST file is incomplete: geometry block is missing. |
| fst-reader | pipeline | error | The FST file is incomplete: geometry block is missing. |
| fstapi | full_parse | error | context creation error |
| fstapi | signal_list | error | context creation error |
| fstapi | value_query | error | context creation error |
| fstapi | pipeline | error | context creation error |

## 7. Summary

- **VCD libraries tested**: pywellen, rust-vcd, vcd-ng, vcdvcd, wellen
- **FST libraries tested**: fst-reader, fstapi, pylibfst, pywellen, wellen
- **Scale**: small+medium+large

### Key Takeaways

- Rust libraries generally parse faster than Python due to lower interpreter overhead
- FST format offers better compression but parse speed depends on implementation
- wellen provides the most comprehensive format support (VCD + FST + GHW)
- For VCD streaming use cases, rust-vcd and vcd-ng offer low-memory alternatives
- For FST, fst-reader (pure Rust) avoids C dependency unlike fstapi
