"""Positive control plus compiler-negative unit-safety tests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
compiler = sys.argv[1] if len(sys.argv) > 1 else "fe"
library = (root / "src/lib.fe").read_text(encoding="utf-8")
cases = {
    "same_unit_control": (True, """
fn example() {
    let a = Quantity::new(raw: 1, unit: Metre {})
    let b = Quantity::new(raw: 2, unit: Metre {})
    let result = a.checked_add(other: b)
    match result { Ok(_) => {}, Err(_) => {} }
}
"""),
    "length_plus_time": (False, """
fn example() {
    let a = Quantity::new(raw: 1, unit: Metre {})
    let b = Quantity::new(raw: 2, unit: Second {})
    let result = a.checked_add(other: b)
    match result { Ok(_) => {}, Err(_) => {} }
}
"""),
    "implicit_scale_change": (False, """
fn example() {
    let a = Quantity::new(raw: 1, unit: Metre {})
    let b = Quantity::new(raw: 1000, unit: Millimetre {})
    let result = a.checked_sub(other: b)
    match result { Ok(_) => {}, Err(_) => {} }
}
"""),
}
results = []
with tempfile.TemporaryDirectory(prefix="checked-units-types-") as tmp:
    for name, (should_pass, body) in cases.items():
        source = Path(tmp) / f"{name}.fe"
        source.write_text(library + "\n" + body, encoding="utf-8")
        run = subprocess.run([compiler, "--color", "never", "check", str(source)],
                             text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=60)
        output = run.stdout + run.stderr
        correct = run.returncode == 0 if should_pass else (
            run.returncode != 0 and "type mismatch" in output and "Quantity" in output)
        results.append({"case": name, "expected_compile": should_pass,
                        "exit_code": run.returncode, "passed": correct,
                        "diagnostics": output})
print(json.dumps(results, indent=2))
if not all(r["passed"] for r in results):
    raise SystemExit(1)
