# VCD/FST 波形解析库综合对比

[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-blue)](https://devil-sx.github.io/waveform-bench/)

对 11 个 VCD/FST 波形解析库进行系统性性能对比，覆盖 Rust、Python、C 三种语言，包含 220 条基准测试记录。

## 在线演示

👉 **[https://devil-sx.github.io/waveform-bench/](https://devil-sx.github.io/waveform-bench/)**

交互式网页支持：
- VCD / FST 格式切换
- Large / Medium / Small 数据规模切换
- 合成数据 / 真实波形切换
- 相对性能对比（最快 = 1x 基准）
- 库特性标签对比（语言、格式、读写、多线程、I/O 模型等）

## 测试库

| 库 | 语言 | 格式 | 读/写 |
|---|---|---|---|
| [wellen](https://github.com/ekiwi/wellen) | Rust | VCD+FST+GHW | R |
| [rust-vcd](https://github.com/kevinmehall/rust-vcd) | Rust | VCD | R/W |
| vcd-ng | Rust | VCD | R/W |
| [fst-reader](https://github.com/ekiwi/fst-reader) | Rust | FST | R |
| [fst-writer](https://github.com/ekiwi/fst-writer) | Rust | FST | W |
| [fst-tools/fstapi](https://github.com/MaxXSoft/fst-tools) | Rust | FST | R/W |
| [gtkwave/libfst](https://github.com/gtkwave/gtkwave) | C | FST | R/W |
| [vcdvcd](https://github.com/cirosantilli/vcdvcd) | Python | VCD | R |
| [pylibfst](https://github.com/mschlaegl/pylibfst) | Python | FST | R/W |
| [vcd_rust](https://github.com/SeanMcLoughlin/vcd_rust) | Rust | VCD | R(仅header) |
| [EDA-Parsers](https://github.com/OSCC-Project/EDA-Parsers) | Rust | VCD | R |

## 基准测试项目

| 测试 | 说明 |
|---|---|
| **full_parse** | 完整加载并解析整个波形文件 |
| **signal_list** | 提取所有信号名称和层级结构 |
| **time_range** | 获取波形时间范围（起止时间） |
| **value_query** | 查询指定信号在指定时间点的值 |
| **pipeline** | 端到端流水线：加载 → 列信号 → 查时间 → 查值 |

测试数据规模：Large（175MB VCD / 12.8MB FST）、Medium（17MB / 1.3MB）、Small（1.7MB / 131KB）。

## 项目结构

```
waveform-bench/
├── benchmarks/           # 基准测试代码
│   ├── python/           # Python 测试脚本
│   ├── rust/             # Rust 测试代码
│   ├── data/             # 测试数据（git ignored）
│   ├── results/          # 测试结果 JSON
│   ├── generate_testdata.py
│   ├── run_all.py
│   └── report.py
├── docs/                 # GitHub Pages
│   ├── index.html        # 交互式对比网页
│   └── screenshots/      # Playwright 截图
├── tests/                # Playwright 端到端测试
│   └── webpage.spec.ts
├── VCD_FST_Library_Comparison_Report.md  # 详细对比报告
├── benchmark_report.md                   # 基准测试结果报告
├── wellen/               # git submodule
├── rust-vcd/             # git submodule
├── vcd-ng/               # 源码（无上游仓库）
├── fst-reader/           # git submodule
├── fst-writer/           # git submodule
├── fst-tools/            # git submodule
├── gtkwave/              # git submodule
├── vcdvcd/               # git submodule
├── pylibfst/             # git submodule
├── vcd_rust/             # git submodule
└── EDA-Parsers/          # git submodule
```

## 运行测试

### 生成测试数据

```bash
cd benchmarks
python generate_testdata.py
```

### 运行基准测试

```bash
python benchmarks/run_all.py
python benchmarks/report.py
```

### 运行网页端到端测试

```bash
npm install
npx playwright install chromium
npx playwright test
```

## 核心发现

1. **wellen** 凭借多线程 + rayon 并行在大文件 VCD 解析中以 ~320MB/s 领先
2. **vcd-ng** 采用双解析器策略（快速扫描 + 完整解析），信号列表提取极快
3. **FST 格式**天然支持块索引和信号过滤，局部查询性能远超 VCD
4. **缓存型库**（wellen/pywellen/fstapi/pylibfst）首次加载后的后续操作接近零开销，**重读型库**（rust-vcd/vcd-ng/fst-reader/vcdvcd）每次操作需重新 I/O

## License

MIT
