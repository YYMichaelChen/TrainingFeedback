"""Budget boundaries and persistent accounting, without executing nested test suites."""

import json

import pytest
from budget_plugin import LIMITS, check_budget, reserve_scope, scope_lock


@pytest.mark.parametrize("tier", list(LIMITS))
def test_budget_accepts_exact_limit_and_rejects_next_parameter_case(tier):
    cases = [f"test_sample[{i}]" for i in range(LIMITS[tier])]
    assert len(check_budget(tier, cases)) == LIMITS[tier]
    with pytest.raises(pytest.UsageError, match="budget exceeded"):
        check_budget(tier, ["test_sample[extra]"], cases)


def test_scope_accounts_union_retries_and_rejects_overflow_without_rewriting(tmp_path):
    path = tmp_path / "task.json"
    with scope_lock(path):
        assert reserve_scope(path, "dev", [f"case[{i}]" for i in range(29)]) == 29
        assert reserve_scope(path, "dev", ["case[0]", "case[29]"]) == 30
        before = path.read_bytes()
        with pytest.raises(pytest.UsageError, match="budget exceeded"):
            reserve_scope(path, "dev", ["case[30]"])
        assert path.read_bytes() == before
        with pytest.raises(pytest.UsageError, match="already running"):
            with scope_lock(path):
                pytest.fail("a second invocation must not acquire the scope")
    assert not path.with_suffix(".lock").exists()
    with scope_lock(path):
        assert reserve_scope(path, "dev", ["case[29]"]) == 30


def test_scope_rejects_changed_tier_and_invalid_ledger(tmp_path):
    path = tmp_path / "task.json"
    reserve_scope(path, "dev", ["first"])
    with pytest.raises(pytest.UsageError, match="cannot change tier"):
        reserve_scope(path, "major", ["second"])
    path.write_text(json.dumps({"tier": "dev", "nodeids": "invalid"}), encoding="utf-8")
    with pytest.raises(pytest.UsageError, match="Invalid test budget ledger"):
        reserve_scope(path, "dev", ["second"])
