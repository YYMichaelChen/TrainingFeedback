# 0.7.5 Acceptance Test Selection — 2026-09-28

This is the risk selection for the single `release-0.7.5` patch scope. The user
directed that an additional case should run only when omitting it could allow a
serious application failure. The existing ledger is immutable: 48 affected cases
were already reserved before this review. This review added exactly two distinct
cases, reaching 50/50. It did not reset the ledger, change tier, or hide cases at
collection. A version change to 0.8.0 is not justified by this selection.
The 50/50 count consists solely of pytest node IDs. Installed client checks are
independent candidate evidence and consume no patch-scope case slots.

| Risk | Evidence selected | Reason |
| --- | --- | --- |
| Schema 22 one-time reset and refusal | Already reserved reset, rollback, resume, invalid-root, retained-root and root-switch cases; installed copy check | A defect can delete or alter the wrong data. |
| Plan identity, v3 wire and editor | Already reserved code classification, v3 import/export, hierarchy, invalid-input, save and rollback cases; added `test_normalized_save_reopen_and_unequal_group_doses_remain_verbatim` | A defect can alter a saved prescription or user text. |
| Frozen training after the schema 23 transition | Already reserved activation pin, frozen export and schema 23 reopen cases; added `test_pause_restart_keeps_position_and_frozen_work_after_catalog_replacement` | A defect can lose the active session or reinterpret its facts. |
| Package completeness | Complete payload hash check plus explicit `schema22.sql` and `schema23.sql` checks in `packaging/build.ps1`; installed schema 22 copy | Source-only migration success does not prove that the executable contains the migration inputs. |

The configured 30-case patch regression profile has 15 unique cases outside the
selected 50. It was **not run as a profile**. These cases remain independent,
but do not meet the added-case threshold for this version after the cases above:

| Deferred area | Cases and overlap assessment |
| --- | --- |
| Training result entry and feedback | `test_actual_entry_is_blank_side_locked_invalid_preserved_and_cancel_safe`, `test_batch_targets_both_sides_unrecorded_members_and_retracts_only_its_facts`, `test_feedback_uses_performed_snapshots_and_preserves_unanswered`, `test_finish_requires_all_results_and_terminal_results_are_immutable`, `test_hub_resume_and_frozen_history_feedback_do_not_infer_answers`: execution logic did not change; selected frozen export, paused restart and schema 23 reopen cover the version-sensitive boundary. |
| Training batch failure injection | `test_batch_failure_rolls_back_results_membership_and_version`: batch code did not change; selected activation and library rollback cases cover new writes, while installed representative workflow remains required. |
| Backup and library review/removal | `test_backup_preserves_execution_batches_retractions_and_resume`, `test_batch_application_rolls_back_all_state_events_and_assets`, `test_batch_failure_rolls_back_reviews_selection_and_attachment`, `test_restore_validates_images_does_not_enable_or_reactivate_plan`, `test_review_binding_edit_withdraw_and_original_answer_survive`: those implementations did not change; selected root switching, removal and frozen-pin cases cover affected interactions. |
| Catalog, legacy editor and v3 file registration | `test_program_catalog_is_reproducible_readonly_and_cwd_independent`, `test_ui_editor_cancel_and_verbatim_save_do_not_change_selection`, `test_import_registration_failure_cleans_file_and_rows`: the catalog is unchanged and separately verified; selected new-editor cancellation, malformed import and v3 import cases cover the changed paths. |
| Main navigation | `test_main_window_navigation_and_chinese_labels`: installed navigation is inspected directly. |

The user's risk-selection instruction does not turn the unrun configured profile
into a pass. The workflow in force during 0.7.5 required release baseline
evidence; record the actual 50-case selection and this explicit limitation at
release close. The later risk-selected procedure applies prospectively.
Installed checks have their own status in `local-candidate.md`.

The [2026-09-29 reassessment](test-reassessment-2026-09-29.md) corrects the
post-50 arithmetic, inventories the 65-case union and reviews a 45-case
risk-selected set. It does not change this scope's reservations or results.
