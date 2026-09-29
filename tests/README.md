# Running the regression suite

The [development workflow](../docs/development-workflow.md) owns when to verify
each affected risk. This file owns pytest tiers, limits, scopes and commands.
Tests use temporary databases, locators and synthetic assets only. Run these
commands in PowerShell 7 with the repository interpreter
(shown here as `python` after activating the project environment).

| Tier | Maximum parameter-expanded unique cases per scope |
| --- | ---: |
| `dev` | 30 |
| `patch` | 50 |
| `minor` | 100 |
| `major` | 300 |

The resident suite has at most 300 cases. These are ceilings, not targets.
Use one stable `--test-scope` and tier for the whole task or release, counting
unique cases across commands. Do not reset or split scopes, hide cases at
collection, or loop independent scenarios to evade a limit. A release uses its
one tier and scope from the first execution.

The budget counts only parameter-expanded pytest node IDs reserved under that
scope. Developer-operated client checks, including installed acceptance, do not
count toward a version-update tier limit. Record their `pass`, `fail` or `not run`
results separately against the exact candidate. Static package inspection,
Ruff and diff checks also do not consume pytest case slots; none substitutes for
an unrun pytest case or client check.
UI-focused tests run through pytest still count as pytest cases.

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

`--collect-only` does not execute or reserve cases. Stop after the relevant
checks pass; after a fix, rerun only failed or affected cases under the same
scope and tier.

`tests/budget_plugin.py` counts parameter-expanded unique node IDs across all
executions in `.tmp/test-budgets/<scope>.json`. Failed or interrupted cases stay
reserved; rerunning the same node after repair adds no new slot. An existing
scope cannot change tier. A `.lock` prevents concurrent execution: confirm a
crashed process has ended before removing a stale lock, and retain its JSON
ledger. Completed coverage exchanges and older release evidence remain available
in Git history.
