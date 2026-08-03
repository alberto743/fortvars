<!--
SPDX-FileCopyrightText: 2026 ENEA
SPDX-FileContributor: Alberto P

SPDX-License-Identifier: MPL-2.0
-->


# Fortran variables detector

Detect and summarize the variables and parameters used in a Fortran
compilation unit, using `gfortran`'s own internal symbol table as ground
truth rather than a hand-rolled Fortran parser.

## Why this exists

Implicit typing is one of Fortran's oldest footguns: without `IMPLICIT NONE`,
a typo'd variable name doesn't cause a compile error — it silently declares a
brand-new variable following the default (or a custom `IMPLICIT`) typing
rule. This class of bug is easy to introduce during a refactor and easy to
miss in review, because nothing about the source *looks* wrong.

**Surfacing every IMPLICIT-typed variable, and which procedure, function,
program, or module it belongs to, is the primary goal of this tool** — not
just "does this file have implicit variables somewhere", but "which unit,
so I know where to look". Everything else (parameters, dummy arguments,
`USE`-association tracking) exists to give that finding proper context.

## Installation

```
pip install fortvars
```

`gfortran` must be available on `PATH` at runtime — it is invoked as a
subprocess, not linked as a Python dependency.

For running the test suite:

```
pip install fortvars[test]
```

## CLI usage

```
fortran_variables path/to/file.f90 -v
fortran_variables path/to/file.f90 -w
fortran_variables path/to/file.f90 -j modfiles/ -o build/
```

| Flag | Meaning |
|---|---|
| `-v`, `--verbose` | Print the extracted tables to stdout |
| `-w`, `--write` | Write the extracted tables to file(s) |
| `-j`, `--modfiles-dir` | Directory passed to `gfortran -J` for `.mod` files |
| `-o`, `--output-dir` | Directory for the compiled object file |
| `--format {csv,combined-csv,json}` | Output shape for `-v`/`-w` (default `csv`) |

`-v` and `-w` always emit **both** the Variables and Parameters sections,
even when one of them is empty — a script or notebook parsing the output
never has to special-case "nothing found".

| `--format` | `-v` output | `-w` output |
|---|---|---|
| `csv` (default) | Two printed tables | `<stem>.variables.csv` + `<stem>.parameters.csv` |
| `combined-csv` | One table with a `Kind` column | Single `<stem>.fortvars.csv` with a `Kind` column |
| `json` | `{"variables": [...], "parameters": [...], "warnings": [...]}` | Single `<stem>.fortvars.json` |

The exit code is `1` only when `gfortran` produced no usable output at all
(e.g. the file doesn't exist, or fails to compile before any unit is
processed). If `gfortran` errors out partway through a file, whatever units
it did manage to dump are still parsed and reported — the CLI exits `0` and
prints a warning to stderr instead of discarding that data.

## Python / Jupyter usage

The same analysis is available as a plain Python API, so it can be used
interactively in a notebook — for example, to load two versions of a
Fortran module and compare their variables to spot a new or dropped
IMPLICIT declaration:

```python
import fortvars

result = fortvars.analyze("legacy_solver.f90")
df = result.variables_df()
df[df.Implicit]          # every implicitly-typed variable, with its Unit column
```

```python
diff = fortvars.compare("solver_v1.f90", "solver_v2.f90")
print(diff.summary())    # e.g. "2 variable(s) added, 1 removed; 0 parameter(s) added, 0 removed"
diff.to_dataframe()
```

`analyze()` returns an `AnalysisResult` with `.variables_df()`,
`.parameters_df()`, `.combined_df()`, and `.to_json()`. `compare()` matches
variables and parameters by `(unit, name)` between the two files — see
Known limitations below for what that means for renamed procedures.

## Output columns reference

**Variables** — `Name`, `Unit` (enclosing module/subroutine/function/program),
`Dummy` (is a dummy argument), `Intent` (`IN`/`OUT`/`INOUT`/`None`), `Module`
(origin module if `USE`-associated), `OriginName` (pre-rename name, for
`USE ... ONLY: local => original`), `Implicit` (has no explicit type
declaration — the primary signal this tool exists to surface).

**Parameters** — `Name`, `Unit`, `Module`, `OriginName` (same meaning as above).

## Known limitations

- No source line or column numbers are available: `gfortran
  -fdump-fortran-original` carries no locus information at all, so
  attribution stops at the enclosing unit, not a specific line.
- `compare()` matches by `(unit, name)`; a renamed procedure or variable
  shows up as a full remove+add rather than a matched rename.
- Requires `gfortran` on `PATH`.
- File extension matters: `gfortran` picks fixed- vs. free-form parsing (and
  whether to run the C preprocessor) from the file extension, not its
  content. Use `.f`/`.for`/`.ftn` for fixed-form and `.f90`/`.f95`/`.f03`/`.f08`
  for free-form. **Avoid `.f77` and `.f18`** — `gfortran` doesn't recognize
  either as Fortran source and will silently produce no output at all.
- Compiler-synthesized symbols (`__def_init_*`, `__vtab_*`, `__vtype_*`,
  `__copy_*`, and similar) are automatically filtered out of the results.

## License

SPDX-License-Identifier: MPL-2.0. See `LICENSES/MPL-2.0.txt`.
