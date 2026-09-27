# Running the regression suite

The [development workflow](../docs/development-workflow.md) owns verification
policy and stage budgets. Tests use temporary databases, locators and synthetic
assets only. Run these commands in PowerShell 7 with the repository interpreter
(shown here as `python` after activating the project environment).

For an ordinary change, select affected tests explicitly and keep one task scope:

```powershell
python -m pytest tests/test_database.py --test-tier dev --test-scope TASK-ID --basetemp .tmp/pytest-TASK-ID
python -m ruff check src tests packaging
git diff --check
```

Paths, node IDs, `-k` and `-m` select the requested cases instead of the default
profile. Without an explicit selector, `dev` runs the small smoke profile in
`pyproject.toml`; `patch` and `minor` add their nested baseline profiles, while
`major` selects the full resident suite. Run a release profile and any affected
cases under the **same release scope and tier**; do not run the profiles in
sequence. For example:

```powershell
python -m pytest --test-tier patch --test-scope release-X.Y.Z --basetemp .tmp/pytest-release-X.Y.Z
python -m pytest tests/test_root_switch.py --test-tier patch --test-scope release-X.Y.Z --basetemp .tmp/pytest-release-X.Y.Z
```

Collection inventories without execution or budget reservation:

```powershell
python -m pytest --test-tier major --collect-only -q
```

`tests/budget_plugin.py` counts parameter-expanded unique node IDs across all
executions in `.tmp/test-budgets/<scope>.json`. Failed or interrupted cases stay
reserved; rerunning the same node after repair adds no new slot. An existing
scope cannot change tier. A `.lock` prevents concurrent execution: confirm a
crashed process has ended before removing a stale lock, and retain its JSON
ledger. See the [versioned test-maintenance history](../docs/history/0.7.0/test-maintenance.md)
for completed coverage exchanges and older release evidence.
