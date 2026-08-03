# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`fortvars` is a small Python package that detects and summarizes the variables and
parameters used in a Fortran compilation unit. It works by shelling out to `gfortran`
to produce a `-fdump-fortran-original` dump, then parsing that text dump to extract
symbol information. Requires `gfortran` to be installed and on `PATH` at runtime (it is
not a Python dependency — it's invoked as a subprocess).

The primary goal (see README.md) is surfacing IMPLICIT-typed variables and which
procedure/module they belong to — not just the CLI, but also a plain Python API
(`fortvars.analyze()`/`fortvars.compare()`) meant for interactive/notebook use, e.g.
comparing two versions of a Fortran file to spot a new or dropped implicit variable.

## Commands

Install in editable mode with the test extra:
```
pip install -e '.[test]'
```

Run the test suite:
```
pytest
pytest tests/test_parser_f90.py -k rename_use   # a single test
```

Tests that shell out to `gfortran` are skipped (not failed) when it isn't on
`PATH` (see `tests/conftest.py`'s `requires_gfortran` marker) — only the
pure-dataclass tests in `test_api.py` run without it.

Build the distribution (matches the release workflow in `.github/workflows/pypi.yml`):
```
python3 -m build
```

Run the CLI against a Fortran source file:
```
fortran_variables path/to/file.f90 -v                        # print variables/parameters to stdout
fortran_variables path/to/file.f90 -w --format combined-csv  # write a single combined CSV
fortran_variables path/to/file.f90 -j modfiles/ -o build/    # module-file and object dirs passed to gfortran
```

## Architecture

Everything lives in `src/fortvars/fortran_variables.py`, structured as a pipeline of
plain dataclasses (`Variable`, `Parameter`, `CompileDump`, `AnalysisResult`,
`ComparisonResult`) plus four functions:

1. **`run_gfortran_dump`** — runs `gfortran -fdump-fortran-original -c <sourcefile>`
   and returns a `CompileDump` with `stdout`/`stderr`/`returncode`, regardless of
   whether gfortran exited nonzero. This matters: gfortran still emits a complete,
   well-formed dump for every unit it successfully processed even when a *later* unit
   in the same file has a hard semantic error, so a naive `check=True` + "discard on
   any failure" approach throws away perfectly good data. `unrecognized_extension`
   flags source files whose extension gfortran doesn't recognize as Fortran at all
   (e.g. `.f77`, `.f18` — these silently produce empty stdout with return code 0,
   which would otherwise be indistinguishable from "genuinely zero variables").

2. **`parse_gfortran_dump`** — parses the dump text into a `ParseResult`. gfortran
   dumps *every* program unit in the file as its own
   `Namespace:`/`procedure name = X`/`symtree:`/`attributes:`/`code:` block, one after
   another, including nested `CONTAINS` units. The parser tracks a flat `current_unit`
   string that is simply reassigned on every `procedure name =` line, and a `pending`
   symbol name awaiting its `attributes:` line; a unit's own `code:` line clears
   `pending` but does **not** stop the scan — there is no need for indentation or a
   nesting stack, since `procedure name =` alone always identifies which unit owns the
   symbols that follow it. (The previous implementation `break`ed unconditionally on
   the first `code:` line in the whole file, so it only ever saw the first unit's
   declarations — this was the dominant bug driving the rewrite.)

   Within each symbol, `attrs[0]` classifies it (`VARIABLE`, `PARAMETER`, `PROCEDURE`,
   `DERIVED`, `MODULE`, `PROGRAM`, `BLOCK-DATA`, ...; only `VARIABLE`/`PARAMETER` are
   kept). Compiler-synthesized symbols (`__def_init_*`, `__vtab_*`, `__vtype_*`,
   `__copy_*`, ...) are filtered by name prefix and/or an `ARTIFICIAL` attribute —
   without this filter they get misclassified as ordinary user variables. For
   `USE mod, ONLY: local => original` renaming, the symtree line's local name and the
   `symbol:` origin name differ (case-insensitively); `origin_name` is only populated
   in that case, so the common (unrenamed) case doesn't carry a redundant column.
   `IMPLICIT-TYPE` in the attribute list is the exact signal for "this symbol has no
   explicit type declaration" — the primary thing this tool exists to surface.

   Because this is line/regex matching against gfortran's internal dump format (not a
   stable public API), any change here should be checked against real
   `-fdump-fortran-original` output for all three supported standards — see the
   fixtures under `tests/fixtures/{f77,f90,f03}/`.

3. **`analyze`** / **`compare`** — the public, notebook-friendly API (exported from
   `fortvars/__init__.py`). `analyze(sourcefile)` runs the two functions above and
   returns an `AnalysisResult` (`.variables_df()`, `.parameters_df()`,
   `.combined_df()`, `.to_json()`). `compare(a, b)` diffs two files' variables and
   parameters matched by `(unit, name)`, returning a `ComparisonResult` — a simple
   structural diff, not a semantic one (a renamed procedure shows as remove+add).

4. **`main`** — the CLI entry point (registered under `[project.scripts]` in
   `pyproject.toml`), built on `analyze()`. `-v`/`-w` always emit both the Variables
   and Parameters sections, even when empty; `--format` selects between two separate
   CSVs (default), one combined CSV with a `Kind` column, or JSON. Exit code is `1`
   only when gfortran produced no usable output at all; a partial dump recovered from
   a mid-file compile error still exits `0` with a warning on stderr.

## Licensing

Files carry SPDX headers (`SPDX-FileCopyrightText`, `SPDX-FileContributor`,
`SPDX-License-Identifier: MPL-2.0`). Preserve/add these headers consistent with the
existing files when creating or modifying source files.
