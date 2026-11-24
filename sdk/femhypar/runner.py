"""Python and command-line entry points for the packaged native solver."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


def _command():
    executable = Path(__file__).resolve().parent / "bin" / "fem_solver"
    spec = importlib.util.find_spec("torch")
    if not spec or not spec.submodule_search_locations:
        raise RuntimeError("Install the CUDA 12.8 build of PyTorch 2.9.1 before running FemHyPar.")
    torch = Path(next(iter(spec.submodule_search_locations)))
    paths = [str(torch / "lib"), str(torch.parent / "nvidia" / "cuda_runtime" / "lib")]
    if os.environ.get("LD_LIBRARY_PATH"):
        paths.append(os.environ["LD_LIBRARY_PATH"])
    return str(executable), dict(os.environ, LD_LIBRARY_PATH=os.pathsep.join(paths))


def partition(graph, output, *, seed=21, epsilon=0.03, preset="default", device=0, q=2):
    """Write one block label per vertex to output and return the native score record."""
    if type(q) is not int or q < 2 or q & (q - 1):
        raise ValueError("q must be a power of two of at least 2")
    program, env = _command()
    args = [program, "--graph", os.fspath(graph), "--out", os.fspath(output),
            "--seed", str(seed), "--epsilon", str(epsilon), "--preset", preset,
            "--device", str(device), "--q", str(q)]
    return json.loads(subprocess.check_output(args, env=env, text=True))


def main():
    program, env = _command()
    os.execve(program, [program, *sys.argv[1:]], env)
