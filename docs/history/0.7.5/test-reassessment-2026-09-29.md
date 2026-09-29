# 0.7.5 Pytest Selection Reassessment — 2026-09-29

This is a read-only reassessment of test selection. It does not reset the
`release-0.7.5` ledger, withdraw executed results, execute any new pytest case,
or change installed-client evidence.

## Recount

The repository interpreter's `--test-tier patch --collect-only -q` collected the
configured 30-case profile without execution. Comparing those exact node IDs
with `.tmp/test-budgets/release-0.7.5.json` gives:

| Set | Parameter-expanded unique node IDs |
| --- | ---: |
| Reserved in the one patch scope | 50 |
| Configured `dev` + `patch` profile | 30 |
| Exact node-ID intersection | 15 |
| Union requiring execution for both selections | **65** |
| Profile cases outside the ledger | **15** |

The earlier “17 unselected” count was true immediately after 48 cases had been
reserved. Two subsequently added cases were both in the configured profile,
raising its intersection with the ledger from 13 to 15. The post-50 count of 17
in the earlier evidence was an arithmetic carryover, not two missing cases.
The three parameterizations of `test_bad_import_files_leave_no_managed_files`
remain three distinct node IDs.

## Risk review of the 65-case union

“Defer” below means omit from a **fresh, release-specific proposed selection**;
it does not delete a test or change an earlier result. Every case in the union
is covered by this rule: retain all cases except the 20 named below.

| Test file | Union | Retain | Defer | Retained risk |
| --- | ---: | ---: | ---: | --- |
| `test_070_group_plans.py` | 18 | 18 | 0 | v3 contract, plan identity, verbatim save, import/export, activation, edited doses and rollback |
| `test_070_group_execution.py` | 7 | 7 | 0 | Side and result accuracy, transactional batch, pause/reopen, feedback, backup and frozen export |
| `test_070_group_execution_ui.py` | 2 | 2 | 0 | Blank/zero actuals and unknown feedback after resume |
| `test_070_removals.py` | 5 | 2 | 3 | Removed content cannot enter new work; frozen work and schema 23 lifecycle rows survive |
| `test_bootstrap.py` | 5 | 4 | 1 | Occupied destination, locator failure/reopen and expired-root refusal |
| `test_data_root.py` | 8 | 4 | 4 | Fresh root, corrupt database and expired/future schema refusal |
| `test_database.py` | 3 | 0 | 3 | Equivalent version-boundary and transaction risks are covered at the root/use-case layer |
| `test_one_time_reset.py` | 4 | 4 | 0 | Schema 22 deletion/retention, precommit rollback and cleanup recovery |
| `test_root_switch.py` | 8 | 4 | 4 | Root isolation, expired target, locator rollback and active-session guard |
| `test_070_catalog_storage.py` | 1 | 0 | 1 | Catalog source/package verification is recorded separately for this unchanged catalog |
| `test_070_library_workflow.py` | 3 | 0 | 3 | Independent library editing and review paths did not change in 0.7.5 |
| `test_main_window.py` | 1 | 0 | 1 | Navigation is outside the changed schema/plan/session paths |
| **Total** | **65** | **45** | **20** | |

The following 20 cases are deferred from that proposed selection. These are
independent tests, not duplicate node IDs; their relative risk is lower for the
0.7.5 changes. Parenthetical explanations state the retained coverage or the
reason for deferral.

- `test_data_root.py`: `test_describe_candidate_reads_one_path_without_opening_the_database`
  (occupied destination is covered in bootstrap);
  `test_open_rejects_unreadable_marker_without_leaking_the_filename`,
  `test_open_rejects_wrong_application_marker`,
  `test_open_rejects_future_config_version` (other invalid metadata forms;
  corrupt database and expired/future schema refusals remain selected).
- `test_bootstrap.py`: `test_cancel_after_failure_creates_nothing_and_keeps_locator`
  (chooser cancellation is an installed-client check still awaiting manual operation).
- `test_database.py`: `test_transaction_commits_and_rolls_back`,
  `test_database_prevents_multiple_active_sessions`,
  `test_below_window_root_is_refused_without_remigration` (generic or
  lower-level paths; reset rollback, batch rollback, and root expiry remain selected).
- `test_root_switch.py`: `test_candidate_window_failure_rolls_back`,
  `test_invalid_target_keeps_current_root_usable`,
  `test_settings_switch_blocked_while_other_window_visible`,
  `test_settings_switch_cancel_and_failure_feedback` (unchanged presentation and
  failure variants; round trip, expired target and locator failure remain selected).
- `test_070_removals.py`: `test_batch_remove_preserves_all_evidence_and_records_verbatim`,
  `test_batch_application_rolls_back_all_state_events_and_assets`,
  `test_restore_validates_images_does_not_enable_or_reactivate_plan` (unchanged
  lifecycle actions; removal versus frozen training and schema 23 reopen remain selected).
- `test_070_library_workflow.py`: `test_review_binding_edit_withdraw_and_original_answer_survive`,
  `test_batch_failure_rolls_back_reviews_selection_and_attachment`,
  `test_ui_editor_cancel_and_verbatim_save_do_not_change_selection` (unchanged
  independent review/editor paths).
- `test_070_catalog_storage.py`:
  `test_program_catalog_is_reproducible_readonly_and_cwd_independent`
  (unchanged catalog and separate catalog verification).
- `test_main_window.py`: `test_main_window_navigation_and_chinese_labels`
  (unchanged main navigation; installed navigation remains `not run` for the
  corrected candidate).

Eight profile cases outside the existing ledger should **enter** the fresh
risk-selected set: `test_backup_preserves_execution_batches_retractions_and_resume`,
`test_batch_failure_rolls_back_results_membership_and_version`,
`test_batch_targets_both_sides_unrecorded_members_and_retracts_only_its_facts`,
`test_feedback_uses_performed_snapshots_and_preserves_unanswered`,
`test_finish_requires_all_results_and_terminal_results_are_immutable`,
`test_actual_entry_is_blank_side_locked_invalid_preserved_and_cancel_safe`,
`test_hub_resume_and_frozen_history_feedback_do_not_infer_answers`, and
`test_import_registration_failure_cleans_file_and_rows`. They cover persisted
session facts, transactional result/import writes, backup continuity, and
blank/unknown UI behavior that source-only plan tests cannot certify.

Thus the fresh risk set is `50 - 13 + 8 = 45` cases. The 13 previously executed
cases removed by this review remain reserved and passed historically. Adding
the eight newly prioritized cases to the **existing** ledger would require
`50 + 8 = 58` unique reservations, beyond its unchanged patch ceiling of 50.
There is no legitimate recount of that ledger from zero. Running the full
configured profile would require all 15 missing cases and 65 reservations.
The workflow in force for 0.7.5 required the release profile. The prospective
risk-selected procedure adopted at closeout does not turn that historical
requirement into a pass or complete 0.7.5 acceptance.

## Remaining coverage gap

The schema 22 reset test verifies retained `body_area` and `library_reference`
rows and checks that synthetic image/review files remain. Its fixture does not
contain library review, selection, custom-content or removal-decision rows.
The [historical reset design](reset-design.md)
requires those independent library facts to survive. A focused synthetic reset
case with those rows, plus the candidate-specific manual installed upgrade
checks, is still needed before claiming that full retention requirement was
verified. The corrected candidate's installed-client checks remain `not run`.
