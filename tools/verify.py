"""Run the documented compiler/test checks, failing on any unsuccessful step."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--fe", default="fe")
parser.add_argument("--backend", choices=["native", "sonatina"], default="native")
parser.add_argument("--report", type=Path, default=Path("out/verification.json"))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
compiler = shutil.which(args.fe) or str(Path(args.fe).resolve())
commands = [
    [compiler, "--version"],
    [compiler, "fmt", "--check", str(root)],
    [compiler, "check", str(root)],
    [os.sys.executable, str(root / "tools/check_types.py"), compiler],
    [compiler, "test", "--backend", args.backend, str(root)],
]
if args.backend == "native":
    commands.append([os.sys.executable, str(root / "tools/check_demo.py"), "--fe", compiler])
steps = []
for command in commands:
    completed = subprocess.run(command, cwd=root, text=True, encoding="utf-8",
                               errors="replace", capture_output=True, timeout=180)
    steps.append({"command": command, "returncode": completed.returncode,
                  "stdout": completed.stdout, "stderr": completed.stderr})
    if completed.returncode:
        break
source_files = sorted(root.glob("src/*.fe")) + sorted(root.glob("tools/*.py")) + [root / "fe.toml"]
source_files += sorted(root.glob("examples/*/src/*.fe")) + sorted(root.glob("examples/*/fe.toml"))
report = {"checked_utc": datetime.now(timezone.utc).isoformat(), "backend": args.backend,
          "passed": all(s["returncode"] == 0 for s in steps) and len(steps) == len(commands),
          "steps": steps,
          "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in source_files}}
destination = args.report if args.report.is_absolute() else root / args.report
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": report["passed"], "steps": len(steps), "report": str(destination)}))
if not report["passed"]:
    print(steps[-1]["stdout"] + steps[-1]["stderr"])
    raise SystemExit(1)
