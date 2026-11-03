# Checked Units

A small Fe library for unsigned quantities, checked arithmetic and explicit rounding.

Development prototype for the Fe Builders Challenge. First implementation: 3 November 2026.

## The problem

An integer can mean metres, millimetres, seconds or a scaled decimal. Plain integers let a caller accidentally mix these meanings. Intermediate multiplication can also overflow before division, even when the final answer fits. Silent rounding adds a further source of error.

This prototype separates the unit type from its raw magnitude. It returns arithmetic errors as values and makes callers choose a rounding policy.

## What works

- `Quantity<U>`: a `u128` magnitude and a unit marker. Addition and subtraction accept the same unit type only.
- Explicit conversions between whole metres and whole millimetres, and between seconds and milliseconds.
- `Fixed6`: a dimensionless unsigned decimal represented as integer millionths, with checked multiplication and division.
- `mul_div`: an exact `u256` intermediate product of two `u128` inputs, followed by division and checked narrowing.
- Four rounding policies: exact, floor, ceiling and nearest with ties to even.
- Distinct overflow, underflow, division-by-zero and inexact-result errors.

For example, `1_500_000` and `2_250_000` in `Fixed6` represent 1.5 and 2.25. Multiplication returns `3_375_000`, representing 3.375. Dividing 1.0 by 3.0 with ceiling returns `333_334`; exact mode returns `Inexact`.

Adding `Quantity<Metre>` to `Quantity<Second>` is a compiler error. Adding metres to millimetres also fails until the caller explicitly converts the scale. These checks prevent accidental misuse through this API; they do not establish that an input was measured or labelled correctly.

## Build and verify

Use the official Fe 26.5.0 release, currently tested as `fe 26.5.0 (3dab95f)`. The [official installation guide](https://fe-lang.org/getting-started/installation/) provides installation instructions. Keep the compiler outside the source repository.

From this directory:

```sh
fe check .
fe fmt --check .
fe test --backend native .
python3 tools/check_types.py /absolute/path/to/fe
```

Or run the complete sequence with a machine-readable report:

```sh
python3 tools/verify.py --fe /absolute/path/to/fe --backend native
```

This also builds and runs the separate native consumer in `examples/demo` and checks its full output. The consumer imports this library through a local path dependency; it does not copy the implementation.

## Native demonstration

On the supported Linux host, from this directory:

```sh
fe build --backend native --emit executable --out-dir out/native-demo examples/demo
./out/native-demo/checked_units_demo
```

The executable prints results produced by actual library calls: 42 metres becomes 42,000 millimetres; an exact conversion of 2,500 millimetres to whole metres returns `Inexact`; Fixed6 multiplication produces the raw value 3,375,000; and invalid arithmetic returns explicit errors. No network, wallet or external data is used.

For an automated build, output and exit-code check:

```sh
python3 tools/check_demo.py --fe /absolute/path/to/fe
```

The native test backend needs a supported host and a C linker. This prototype was run on x86-64 Ubuntu under WSL2 with the official Linux Fe binary and `build-essential`. The Windows binary can check and format the code and run the default Sonatina test backend; it cannot execute the native backend on Windows.

Optional cross-backend check:

```sh
fe test .
```

To regenerate the independent arithmetic test vectors:

```sh
python3 tools/generate_vectors.py
fe fmt .
fe test --backend native .
```

The Python generator uses arbitrary-precision integers, a fixed random seed and explicit boundary cases. It emits 516 expected outcomes across the four rounding policies. These are checked by 22 batched Fe tests, alongside 14 focused behavioural tests. All 36 tests passed on the native and Sonatina backends on 3 November 2026. The separate compiler check includes a valid same-unit control and two expected type failures. Run the verification script to produce a fresh report in `out/verification.json`.

## Arithmetic contract

Inputs are unsigned and bounded by `u128`. Their product is at most `(2^128 - 1)^2`, which fits `u256`. Division happens before narrowing. Any requested rounding increment is checked against the `u128` maximum. Narrowing itself is checked as well.

Error precedence is deliberate: a zero denominator produces `DivisionByZero`; exact mode with a remainder produces `Inexact`; otherwise an out-of-range rounded quotient produces `Overflow`. Nearest-even compares the remainder with `denominator - remainder`, avoiding a doubled remainder.

## Limitations and next work

This is not a general dimensional-analysis framework. It has no compound units, signed magnitudes, decimal parsing, persistence or external integrations. Metres and seconds use whole units; they are not implicitly `Fixed6`. User-defined marker types are possible, and callers remain responsible for the meaning of raw inputs and any manual re-labelling.

The library is not audited, production-ready or formally verified. Passing sampled tests does not prove correctness over the entire input domain. The two Fe backends share compiler infrastructure. No financial service, wallet, token or blockchain deployment is involved.

Next work: independent code review and more units. The separate demonstration checks use of the public API from another ingot.

## Provenance

Codex wrote the original library, tests, oracle generator and this documentation during the contest build window. No third-party project code or previous competition solution was copied. Official Fe documentation was consulted for language syntax, compiler commands and test APIs; the organiser's starter README was read for packaging requirements, but its vault contract and tests were not reused.

Development tools: official Fe compiler release; Python standard library; Ubuntu C toolchain. No paid API or cloud service was used.
