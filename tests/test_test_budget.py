"""Budget boundaries and persistent accounting, without executing nested test suites."""

import json

import pytest
from budget_plugin import CURRENT_LIMIT, LIMITS, check_budget, reserve_scope, scope_lock


@pytest.mark.parametrize("tier", list(LIMITS))
def test_current_budget_accepts_three_and_rejects_next_parameter_case(tier):
    cases = [f"test_sample[{i}]" for i in range(CURRENT_LIMIT)]
    assert len(check_budget(tier, cases)) == CURRENT_LIMIT
    with pytest.raises(pytest.UsageError, match="budget exceeded"):
        check_budget(tier, ["test_sample[extra]"], cases)


def test_scope_accounts_union_retries_and_rejects_overflow_without_rewriting(tmp_path):
    path = tmp_path / "task.json"
    with scope_lock(path):
        assert reserve_scope(path, "dev", ["case[0]", "case[1]"]) == 2
        assert reserve_scope(path, "dev", ["case[0]", "case[2]"]) == 3
        before = path.read_bytes()
        with pytest.raises(pytest.UsageError, match="budget exceeded"):
            reserve_scope(path, "dev", ["case[3]"])
        assert path.read_bytes() == before
        with pytest.raises(pytest.UsageError, match="already running"):
            with scope_lock(path):
                pytest.fail("a second invocation must not acquire the scope")
    assert not path.with_suffix(".lock").exists()
    with scope_lock(path):
        assert reserve_scope(path, "dev", ["case[2]"]) == 3


def test_scope_rejects_changed_tier_and_invalid_ledger(tmp_path):
    path = tmp_path / "task.json"
    reserve_scope(path, "dev", ["first"])
    with pytest.raises(pytest.UsageError, match="cannot change tier"):
        reserve_scope(path, "major", ["second"])
    path.write_text(json.dumps({"tier": "dev", "nodeids": "invalid"}), encoding="utf-8")
    with pytest.raises(pytest.UsageError, match="Invalid test budget ledger"):
        reserve_scope(path, "dev", ["second"])


def test_legacy_scope_preserves_history_and_allows_only_recorded_retries(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps({"tier": "dev", "nodeids": ["old[0]", "old[1]", "old[2]", "old[3]"]}),
        encoding="utf-8",
    )
    before = path.read_bytes()

    assert reserve_scope(path, "dev", ["old[1]"]) == 4
    assert path.read_bytes() == before
    with pytest.raises(pytest.UsageError, match="historical test scope"):
        reserve_scope(path, "dev", ["new"])
    assert path.read_bytes() == before
