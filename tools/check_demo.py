"""Compile a separate consumer ingot and check its real native stdout and exit."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--fe", default="fe")
parser.add_argument("--report", type=Path, default=Path("out/demo-verification.json"))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
compiler = shutil.which(args.fe) or str(Path(args.fe).resolve())
demo = root / "examples/demo"
out = root / "out/native-demo"
expected = """Checked Units: native demo
metres 42 -> millimetres: 42000
2500mm -> metres, exact: Inexact
fixed6 1.5*2.25, raw: 3375000
fixed6 1/3, ceiling, raw: 333334
5/2, nearest-even: 2
7/2, nearest-even: 4
max*max/max: 340282366920938463463374607431768211455
0*max/1: 0
max*2/1: Overflow
0/0: DivisionByZero
"""
build_command = [compiler, "build", "--backend", "native", "--emit", "executable",
                 "--out-dir", str(out), str(demo)]
build = subprocess.run(build_command, cwd=root, text=True, capture_output=True, timeout=180)
record = {"checked_utc": datetime.now(timezone.utc).isoformat(),
          "build_command": build_command, "build_exit": build.returncode,
          "build_output": build.stdout + build.stderr, "passed": False}
if build.returncode == 0:
    executable = out / "checked_units_demo"
    run = subprocess.run([str(executable)], cwd=root, text=True, capture_output=True, timeout=10)
    record.update({"run_exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
                   "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                   "passed": run.returncode == 0 and run.stdout == expected and run.stderr == ""})
destination = args.report if args.report.is_absolute() else root / args.report
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, indent=2))
if not record["passed"]:
    raise SystemExit(1)
