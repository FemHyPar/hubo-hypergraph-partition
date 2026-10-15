"""Audit the initial public-release scaffold and every reachable commit."""
from pathlib import Path
import subprocess

ALLOWED = {"README.md", ".github/scripts/audit_tree.py", ".github/workflows/sync-hubo-release.yml"}

def git(*args):
    return subprocess.check_output(["git", *args]).decode()

roots = git("rev-list", "--max-parents=0", "HEAD").splitlines()
if len(roots) != 1:
    raise SystemExit("Public release must retain an independent, single-root history")
for commit in git("rev-list", "HEAD").splitlines():
    paths = git("ls-tree", "-r", "--name-only", commit).splitlines()
    unexpected = sorted(set(paths) - ALLOWED)
    if unexpected:
        raise SystemExit(f"Unreviewed public paths in {commit}: {unexpected}")
    modes = git("ls-tree", "-r", commit).splitlines()
    if any(line.split()[0] not in {"100644", "100755"} for line in modes):
        raise SystemExit("Symlinks and submodules are not allowed in the release scaffold")
if not all(Path(path).is_file() for path in ALLOWED):
    raise SystemExit("Incomplete release scaffold")
print("Public HUBO scaffold and complete history audited; no implementation is published")
