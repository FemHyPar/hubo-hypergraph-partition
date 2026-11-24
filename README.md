# FemHyPar

FemHyPar computes balanced partitions of a unit-weight hypergraph on an NVIDIA GPU. It minimizes the number of nets spanning multiple blocks. The `default` preset runs one multilevel search. The `quality` preset runs three cycles, uses agreement among candidate partitions for recoarsening, and applies a final reheating probe and collective refinement.

## Install

The [2026.11.24 wheel](artifacts/femhypar-2026.11.24-py3-none-linux_x86_64.whl) contains the Python interface and the compiled solver for **NVIDIA A100 (SM80), Linux x86-64**. The tested environment used Python 3.10, glibc 2.35, NVIDIA driver 550.90.07 and PyTorch 2.9.1+cu128 (C++11 ABI). Use the following commands from this checkout in a Python environment with access to the GPU.

```sh
python -m pip install 'torch==2.9.1' --index-url https://download.pytorch.org/whl/cu128
python -m pip install ./artifacts/femhypar-2026.11.24-py3-none-linux_x86_64.whl
```

## Partition a hypergraph

```sh
femhypar --graph examples/tiny.hgr --out partition.txt --preset default --seed 21 --epsilon 0
```

The example has two disconnected six-vertex components. At exact balance a cut of zero puts six vertices in each block. Each output line contains the zero-based block label of the corresponding vertex. The JSON output gives the cut, vertex count, size of block 1 (`ones`), maximum permitted block size (`bound`), and solve time in seconds. The input uses unweighted hMetis format: a header with the net and vertex counts, followed by one line of one-based vertex IDs per net.

Use `--preset quality` for the larger search budget, `--epsilon .03` for 3% imbalance tolerance or `--q 4` for four blocks. The native recursive path accepts powers of two up to the number of vertices. With `--batch`, supply one whitespace-separated set of options per input line using paths without spaces. Each job starts independently in the resident GPU process.

```python
from femhypar import partition

result = partition("examples/tiny.hgr", "partition.txt", preset="quality", epsilon=0)
print(result["cut"], result["bound"])
```

[Validation results](validation.json) include the wheel and executable SHA-256 digests and comparisons with archived solver outputs. Project terms are in [LICENSE](LICENSE) and [NOTICE](NOTICE).
