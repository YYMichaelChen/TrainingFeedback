"""Historical profiles plus the current explicit-node, three-scenario guard."""

import json
import re
from contextlib import contextmanager
from pathlib import Path

import pytest

LIMITS = {"dev": 30, "patch": 50, "minor": 100, "major": 300}
TIERS = tuple(LIMITS)
CURRENT_POLICY = "startup-only-explicit-3"
CURRENT_LIMIT = 3


def pytest_addoption(parser):
    group = parser.getgroup("regression budget")
    group.addoption("--test-tier", choices=TIERS, default="dev",
                    help="Historical ledger tier; current execution is capped at 3 cases.")
    group.addoption("--test-scope", help="Stable task/release ID shared by every test command.")
    for tier in TIERS[:-1]:
        parser.addini(f"regression_{tier}", f"Additional {tier} profile test function names",
                      type="linelist")


def profile_names(config, tier):
    names = set()
    for level in TIERS[:TIERS.index(tier) + 1]:
        if level != "major":
            names.update(config.getini(f"regression_{level}"))
    return names


def check_budget(tier, nodeids, previous=()):
    combined = sorted(set(previous) | set(nodeids))
    if len(combined) > CURRENT_LIMIT:
        raise pytest.UsageError(
            f"Current test budget exceeded: {len(combined)} unique cases > {CURRENT_LIMIT}. "
            "Only explicit startup-risk nodes are allowed; do not split/reset the scope."
        )
    return combined


@contextmanager
def scope_lock(path):
    lock = path.with_suffix(".lock")
    try:
        stream = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise pytest.UsageError(f"Test scope is already running: {lock}") from exc
    try:
        with stream:
            yield
    finally:
        lock.unlink()


def reserve_scope(path, tier, nodeids):
    previous = []
    legacy = False
    if path.exists():
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            if saved["tier"] != tier:
                raise pytest.UsageError("A test scope cannot change tier; use its original stage.")
            previous = saved["nodeids"]
            if not isinstance(previous, list) or not all(isinstance(n, str) for n in previous):
                raise ValueError("nodeids must be a list of strings")
            legacy = saved.get("policy") != CURRENT_POLICY
        except (ValueError, KeyError, TypeError) as exc:
            raise pytest.UsageError(f"Invalid test budget ledger: {path}") from exc
    if legacy:
        added = sorted(set(nodeids) - set(previous))
        if added:
            raise pytest.UsageError(
                "A historical test scope may only rerun its recorded nodes; "
                "use one new scope for genuinely new work."
            )
        return len(set(previous))
    combined = check_budget(tier, nodeids, previous)
    staging = path.with_suffix(".new")
    staging.write_text(
        json.dumps(
            {"tier": tier, "policy": CURRENT_POLICY, "limit": CURRENT_LIMIT,
             "nodeids": combined},
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    staging.replace(path)
    return len(combined)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    # Built-in deselection must finish before counting the requested selection.
    yield
    tier = config.getoption("test_tier")
    collect_only = config.getoption("collectonly")
    explicit_nodes = (
        config.args_source == pytest.Config.ArgsSource.ARGS
        and bool(config.args)
        and all("::" in str(argument) for argument in config.args)
    )
    if not collect_only and not explicit_nodes:
        raise pytest.UsageError(
            "Execution requires explicit pytest node IDs containing '::'. "
            "Bare pytest, files, directories, default profiles and -k/-m-only selection "
            "are not permitted by the current startup-risk policy."
        )
    if not explicit_nodes:
        if len(items) > LIMITS["major"]:
            raise pytest.UsageError(
                f"Historical major collection exceeds its retained capacity: "
                f"{len(items)} cases > {LIMITS['major']}."
            )
        configured = profile_names(config, "minor")
        available = {item.originalname or item.name for item in items}
        missing = configured - available
        if missing:
            raise pytest.UsageError(f"Stale regression profile entries: {sorted(missing)}")
        if tier != "major":
            names = profile_names(config, tier)
            selected, deselected = [], []
            for item in items:
                (selected if (item.originalname or item.name) in names else deselected).append(item)
            config.hook.pytest_deselected(items=deselected)
            items[:] = selected
    if not collect_only:
        check_budget(tier, [item.nodeid for item in items])
    reporter = config.pluginmanager.getplugin("terminalreporter")
    if reporter:
        if collect_only:
            reporter.write_line(f"Historical collection profile: {tier} ({len(items)} nodes)")
        else:
            reporter.write_line(
                f"Current test budget: {len(items)}/{CURRENT_LIMIT} explicit nodes selected"
            )


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtestloop(session):
    config = session.config
    if config.getoption("collectonly") or session.testsfailed or not session.items:
        return (yield)
    scope = config.getoption("test_scope")
    if not scope or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", scope):
        raise pytest.UsageError("Execution requires --test-scope TASK-ID (letters/digits/._-).")
    path = Path(config.rootpath) / ".tmp" / "test-budgets" / f"{scope}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep the lock through execution, not just the write, to prevent parallel budget races.
    with scope_lock(path):
        count = reserve_scope(path, config.getoption("test_tier"),
                              [item.nodeid for item in session.items])
        reporter = config.pluginmanager.getplugin("terminalreporter")
        if reporter:
            reporter.write_line(f"Test scope: {scope}, {count} unique cases reserved")
        return (yield)
