# Policy: Quality gates

Every change to this repository passes three checks before it can merge. They run in
this order and the first failure stops the rest.

1. **`ruff check src/filegit tests`** — no lint errors. Line length is 88.
2. **`mypy src/filegit`** — strict mode. No function may be left without a return
   annotation.
3. **`pytest`** — all tests pass and coverage stays at or above **90%**.

The threshold is enforced by `--cov-fail-under` in `pyproject.toml`, not by convention.

## Why this is a policy and not a preference

On 2026-09-02 this repository pushed a commit whose CI failed at step 1 and never ran a
single test. The failure stayed red for three days without anyone noticing, because
nothing required the check to be green. A quality gate that nobody is obliged to respect
is documentation, not a gate.
