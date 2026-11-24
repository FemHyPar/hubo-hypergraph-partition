"""Check the public Git history and packaged native executable before mirroring."""
import base64
import csv
from hashlib import sha256
from io import BytesIO, StringIO
import json
import stat
import subprocess
from zipfile import ZipFile

ROOT = "b179af73f4c9bf12e94bbe40908181d6b018e539"
WHEEL = "artifacts/femhypar-2026.11.24-py3-none-linux_x86_64.whl"
DIST = "femhypar-2026.11.24.dist-info"
SCAFFOLD = {"README.md", ".github/scripts/audit_tree.py", ".github/workflows/sync-hubo-release.yml"}
PUBLIC = SCAFFOLD | {"LICENSE", "NOTICE", "examples/tiny.hgr", "validation.json",
                     "sdk/femhypar/__init__.py", "sdk/femhypar/runner.py", WHEEL}
MEMBERS = {"femhypar/__init__.py", "femhypar/runner.py", "femhypar/bin/fem_solver"} | {
    f"{DIST}/{name}" for name in ("METADATA", "WHEEL", "entry_points.txt", "LICENSE", "NOTICE", "RECORD")}


def git(*args):
    return subprocess.check_output(["git", *args])


def check(condition, message):
    if not condition:
        raise SystemExit(message)


def check_wheel(commit):
    def blob(path):
        return git("show", f"{commit}:{path}")

    release = json.loads(blob("validation.json"))
    payload = blob(WHEEL)
    check(sha256(payload).hexdigest() == release["wheel_sha256"], "Wheel digest differs")
    with ZipFile(BytesIO(payload)) as wheel:
        check(len(wheel.namelist()) == len(MEMBERS) and set(wheel.namelist()) == MEMBERS,
              "Unexpected or missing wheel member")
        check(all(stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG)
                  for info in wheel.infolist()), "Non-regular wheel member")
        for name in ("__init__.py", "runner.py"):
            check(wheel.read("femhypar/" + name) == blob("sdk/femhypar/" + name), "SDK differs")
        for name in ("LICENSE", "NOTICE"):
            check(wheel.read(f"{DIST}/{name}") == blob(name), "License or notice differs")
        binary_name = "femhypar/bin/fem_solver"
        exe = wheel.read(binary_name)
        check(exe.startswith(b"\x7fELF\x02\x01") and sha256(exe).hexdigest() == release["executable_sha256"],
              "Unexpected executable")
        check(wheel.getinfo(binary_name).external_attr >> 16 & 0o111, "Solver lacks execute permission")
        record_name = f"{DIST}/RECORD"
        record = list(csv.reader(StringIO(wheel.read(record_name).decode())))
        check(len(record) == len(MEMBERS) and {r[0] for r in record} == MEMBERS, "Invalid RECORD")
        for path, checksum, length in record:
            if path == record_name:
                check((checksum, length) == ("", ""), "Invalid self-record")
                continue
            data = wheel.read(path)
            digest = base64.urlsafe_b64encode(sha256(data).digest()).rstrip(b"=").decode()
            check((checksum, length) == (f"sha256={digest}", str(len(data))), f"Invalid RECORD for {path}")


check(git("rev-list", "--max-parents=0", "HEAD").decode().splitlines() == [ROOT],
      "Release must descend only from the reviewed public root")
for commit in git("rev-list", "HEAD").decode().splitlines():
    paths = set()
    for entry in git("ls-tree", "-rz", commit).split(b"\0"):
        if not entry:
            continue
        header, name = entry.split(b"\t", 1)
        mode, kind, _ = header.split()
        check(mode in (b"100644", b"100755") and kind == b"blob", "Unexpected tree entry")
        paths.add(name.decode())
    check(paths == (SCAFFOLD if commit == ROOT else PUBLIC), f"Unexpected public paths in {commit}")
    if commit != ROOT:
        check_wheel(commit)
print("Public history, wheel contents, licenses and digests verified.")
