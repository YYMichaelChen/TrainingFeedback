-- Fresh schema24 initialization after the explicit 0.7.5 schema22 plan/training reset.
-- Independent library selections, custom content, guidance, reviews and removals remain.

CREATE TABLE ai_export (
        id INTEGER PRIMARY KEY,
        session_id INTEGER REFERENCES training_session(id),
        format TEXT NOT NULL,
        file_path TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

CREATE TABLE body_area (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
    );

CREATE TABLE content_snapshot (sha256 TEXT PRIMARY KEY, content_json TEXT NOT NULL);

CREATE TABLE content_snapshot_asset (snapshot_sha256 TEXT NOT NULL REFERENCES content_snapshot(sha256), original_path TEXT NOT NULL, asset_sha256 TEXT NOT NULL REFERENCES snapshot_asset(sha256), PRIMARY KEY(snapshot_sha256, original_path));

CREATE TABLE conversion_mapping (source_table TEXT NOT NULL, source_key TEXT NOT NULL, target_kind TEXT NOT NULL, target_json TEXT NOT NULL, PRIMARY KEY(source_table,source_key,target_kind));

CREATE TABLE conversion_original (source_table TEXT NOT NULL, source_key TEXT NOT NULL, row_json TEXT NOT NULL, PRIMARY KEY(source_table,source_key));

CREATE TABLE conversion_registration (kind TEXT NOT NULL CHECK(kind IN ('import','export')), id INTEGER NOT NULL, revision_id INTEGER REFERENCES group_plan_revision(id), session_id INTEGER REFERENCES group_session(id), facts_json TEXT NOT NULL, PRIMARY KEY(kind,id));

CREATE TABLE conversion_run (id INTEGER PRIMARY KEY CHECK(id=1), source_schema INTEGER NOT NULL, source_sha256 TEXT NOT NULL, converted_at TEXT NOT NULL, manifest_json TEXT NOT NULL);

CREATE TABLE exercise (
        id INTEGER PRIMARY KEY,
        canonical_name TEXT NOT NULL UNIQUE,
        active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    , category TEXT NOT NULL DEFAULT 'general', equipment_summary TEXT NOT NULL DEFAULT '', active_guidance_revision_id INTEGER REFERENCES exercise_guidance_revision(id), bundled_exercise_key TEXT);

CREATE TABLE exercise_alias (
        id INTEGER PRIMARY KEY,
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        alias TEXT NOT NULL UNIQUE
    );

CREATE TABLE exercise_body_area (
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        body_area_id INTEGER NOT NULL REFERENCES body_area(id),
        is_primary INTEGER NOT NULL CHECK (is_primary IN (0, 1)),
        PRIMARY KEY (exercise_id, body_area_id)
    );

CREATE TABLE exercise_guidance_revision (
        id INTEGER PRIMARY KEY,
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        revision_number INTEGER NOT NULL,
        guidance_json TEXT NOT NULL,
        created_at TEXT NOT NULL, bundled_content_id TEXT, bundled_content_version INTEGER CHECK (bundled_content_version IS NULL OR bundled_content_version > 0),
        UNIQUE (exercise_id, revision_number)
    );

CREATE TABLE "group_actual_set" (occurrence_id INTEGER NOT NULL REFERENCES group_occurrence_result(occurrence_id), set_order INTEGER NOT NULL, value REAL, unit TEXT, side TEXT CHECK(side IN ('left','right')), note TEXT NOT NULL, provenance TEXT NOT NULL, per_side INTEGER CHECK(per_side IN (0,1) OR per_side IS NULL), PRIMARY KEY(occurrence_id,set_order));

CREATE TABLE "group_occurrence_result" (occurrence_id INTEGER PRIMARY KEY REFERENCES group_session_occurrence(id), result TEXT NOT NULL CHECK(result IN ('completed','exceeded','partial','not_completed')), note TEXT, recorded_at TEXT, batch_id INTEGER REFERENCES group_session_batch(id));

CREATE TABLE group_plan (id INTEGER PRIMARY KEY, base_number INTEGER NOT NULL UNIQUE CHECK(base_number BETWEEN 1 AND 999), name TEXT NOT NULL UNIQUE, active_revision_id INTEGER, created_at TEXT NOT NULL);

CREATE TABLE group_plan_day (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL REFERENCES group_plan_revision(id), day_order INTEGER NOT NULL, UNIQUE(revision_id,day_order));

CREATE TABLE group_plan_export (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL REFERENCES group_plan_revision(id), directory TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE TABLE group_plan_import (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL UNIQUE REFERENCES group_plan_revision(id), source_path TEXT NOT NULL, sha256 TEXT NOT NULL, original_payload TEXT NOT NULL, imported_at TEXT NOT NULL);

CREATE TABLE group_plan_item (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL REFERENCES group_plan_revision(id), day_id INTEGER NOT NULL REFERENCES group_plan_day(id), parent_id INTEGER REFERENCES group_plan_item(id), item_key TEXT NOT NULL, item_order INTEGER NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('action','group','member')), fields_json TEXT NOT NULL, UNIQUE(revision_id,item_key));

CREATE TABLE group_plan_pin (item_id INTEGER PRIMARY KEY REFERENCES group_plan_item(id), content_id INTEGER NOT NULL REFERENCES library_content(id), review_json TEXT NOT NULL, pinned_at TEXT NOT NULL);

CREATE TABLE group_plan_revision (id INTEGER PRIMARY KEY, plan_id INTEGER NOT NULL REFERENCES group_plan(id), revision_number INTEGER NOT NULL, plan_code TEXT NOT NULL UNIQUE, change_description TEXT NOT NULL DEFAULT '', upgrade_source_revision_id INTEGER REFERENCES group_plan_revision(id), status TEXT NOT NULL CHECK(status IN ('draft','active','superseded')), name TEXT NOT NULL, purpose TEXT NOT NULL, target_plan_name TEXT, rationale TEXT NOT NULL, source_json TEXT NOT NULL, created_at TEXT NOT NULL, activated_at TEXT, edit_token INTEGER NOT NULL DEFAULT 1, migration_json TEXT, UNIQUE(plan_id,revision_number));

CREATE TABLE "group_plan_set" (id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL REFERENCES group_plan_item(id), set_order INTEGER NOT NULL, value REAL, unit TEXT NOT NULL, per_side INTEGER NOT NULL CHECK(per_side IN (0,1)), note TEXT NOT NULL, rest_after_set_seconds REAL, UNIQUE(item_id,set_order));

CREATE TABLE group_session (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL REFERENCES group_plan_revision(id), training_date TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('open','paused','completed','partial','aborted')), position INTEGER NOT NULL DEFAULT 0 CHECK(position>=0), version INTEGER NOT NULL DEFAULT 1, snapshot_json TEXT NOT NULL, started_at TEXT NOT NULL, paused_at TEXT, ended_at TEXT, abort_reason TEXT, abort_note TEXT);

CREATE TABLE group_session_batch (id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES group_session(id), preview_token TEXT NOT NULL UNIQUE, members_json TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE TABLE group_session_event (id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES group_session(id), kind TEXT NOT NULL, occurred_at TEXT NOT NULL, facts_json TEXT NOT NULL);

CREATE TABLE group_session_export (export_id INTEGER PRIMARY KEY REFERENCES group_plan_export(id), session_id INTEGER NOT NULL REFERENCES group_session(id));

CREATE TABLE "group_session_feedback" (session_id INTEGER PRIMARY KEY REFERENCES group_session(id), overall_note TEXT, submitted_at TEXT NOT NULL);

CREATE TABLE "group_session_feedback_area" (session_id INTEGER NOT NULL REFERENCES group_session_feedback(session_id), name TEXT NOT NULL, value TEXT, PRIMARY KEY(session_id,name));

CREATE TABLE group_session_occurrence (id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES group_session(id), position INTEGER NOT NULL, content_id INTEGER NOT NULL REFERENCES library_content(id), snapshot_json TEXT NOT NULL, UNIQUE(session_id,position));

CREATE TABLE library_content (id INTEGER PRIMARY KEY, reference_id INTEGER NOT NULL REFERENCES library_reference(id), content_id TEXT NOT NULL, version INTEGER NOT NULL CHECK(version>0), snapshot_sha256 TEXT NOT NULL REFERENCES content_snapshot(sha256), origin TEXT NOT NULL CHECK(origin IN ('bundled','custom','override')), provenance_json TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(reference_id, content_id, version), UNIQUE(id, reference_id));

CREATE TABLE library_lifecycle_event (id INTEGER PRIMARY KEY, request_id INTEGER NOT NULL REFERENCES library_lifecycle_request(id), kind TEXT NOT NULL CHECK(kind IN ('requested','under_review','approved','applied','rejected','cancelled')), source TEXT NOT NULL, occurred_at TEXT NOT NULL, confirmed_at TEXT NOT NULL, note TEXT NOT NULL, preview_json TEXT NOT NULL);

CREATE TABLE library_lifecycle_request (id INTEGER PRIMARY KEY, operation TEXT NOT NULL CHECK(operation IN ('remove','restore')), reason TEXT NOT NULL, requested_at TEXT NOT NULL, preview_json TEXT NOT NULL);

CREATE TABLE library_plan_invalidation (revision_id INTEGER NOT NULL REFERENCES group_plan_revision(id), reference_id INTEGER NOT NULL REFERENCES library_reference(id), lifecycle_event_id INTEGER REFERENCES library_lifecycle_event(id), publisher_event_id INTEGER REFERENCES library_publisher_event(id), PRIMARY KEY(revision_id,reference_id), CHECK((lifecycle_event_id IS NULL)!=(publisher_event_id IS NULL)));

CREATE TABLE library_publisher_event (id INTEGER PRIMARY KEY, reference_id INTEGER NOT NULL REFERENCES library_reference(id), catalog_version TEXT NOT NULL, manifest_sha256 TEXT NOT NULL, disposition TEXT NOT NULL CHECK(disposition IN ('available','withdrawn','missing')), content_reference_json TEXT, observed_at TEXT NOT NULL);

CREATE TABLE library_reference (id INTEGER PRIMARY KEY, source TEXT NOT NULL CHECK(source IN ('bundled','custom')), stable_key TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(source, stable_key));

CREATE TABLE library_review_event (id INTEGER PRIMARY KEY, content_id INTEGER NOT NULL REFERENCES library_content(id), event_type TEXT NOT NULL CHECK(event_type IN ('approved','withdrawn')), content_sha256 TEXT NOT NULL REFERENCES content_snapshot(sha256), image_hashes_json TEXT NOT NULL, reviewer_type TEXT NOT NULL, review_source TEXT NOT NULL, reviewed_at TEXT, confirmed_at TEXT NOT NULL, note TEXT NOT NULL, attachment_json TEXT);

CREATE TABLE library_state (reference_id INTEGER PRIMARY KEY REFERENCES library_reference(id), selected_content_id INTEGER, enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)), FOREIGN KEY(selected_content_id, reference_id) REFERENCES library_content(id,reference_id));

CREATE TABLE library_tombstone (reference_id INTEGER PRIMARY KEY REFERENCES library_reference(id), disposition TEXT NOT NULL CHECK(disposition IN ('removed','restored')), event_id INTEGER NOT NULL REFERENCES library_lifecycle_event(id));

CREATE TABLE next_day_feedback (
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL UNIQUE REFERENCES training_session(id),
        overall_note TEXT,
        submitted_at TEXT NOT NULL
    );

CREATE TABLE next_day_feedback_area (
        id INTEGER PRIMARY KEY,
        feedback_id INTEGER NOT NULL REFERENCES next_day_feedback(id),
        body_area_name_snapshot TEXT NOT NULL,
        value TEXT,
        UNIQUE (feedback_id, body_area_name_snapshot)
    );

CREATE TABLE note_correction_audit (
            id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES training_session(id),
            feedback_id INTEGER REFERENCES next_day_feedback(id),
            session_action_id INTEGER REFERENCES training_session_action(id),
            target TEXT NOT NULL,
            old_value TEXT NOT NULL,
            new_value TEXT NOT NULL,
            corrected_at TEXT NOT NULL,
            operation TEXT NOT NULL
        );

CREATE TABLE plan_import (
        id INTEGER PRIMARY KEY,
        source_path TEXT NOT NULL,
        rationale TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    , plan_id INTEGER REFERENCES training_plan(id), revision_id INTEGER REFERENCES training_plan_revision(id), previous_revision_id INTEGER REFERENCES training_plan_revision(id), source_session_id INTEGER REFERENCES training_session(id), source_export_id INTEGER REFERENCES ai_export(id), confirmed_at TEXT);

CREATE TABLE schema_migration (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);

CREATE TABLE one_time_reset_journal (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        operation TEXT NOT NULL CHECK (operation = 'reset-v0.7.5'),
        path_inventory_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

CREATE TABLE session_event (
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES training_session(id),
        event_type TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        reason TEXT,
        note TEXT
    );

CREATE TABLE session_result_retraction (id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES training_session(id), session_action_id INTEGER NOT NULL REFERENCES training_session_action(id), previous_action_json TEXT NOT NULL, retracted_at TEXT NOT NULL);

CREATE TABLE snapshot_asset (sha256 TEXT PRIMARY KEY, byte_count INTEGER NOT NULL);

CREATE TABLE training_plan (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        -- 故意不加 REFERENCES：training_plan 与 training_plan_revision 互相引用，
        -- 循环外键无法在建表时表达，由激活流程保证指向有效版本。
        active_revision_id INTEGER,
        created_at TEXT NOT NULL
    );

CREATE TABLE training_plan_action (
        id INTEGER PRIMARY KEY,
        day_id INTEGER NOT NULL REFERENCES training_plan_day(id),
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        action_order INTEGER NOT NULL,
        phase TEXT NOT NULL,
        rest_seconds INTEGER,
        note TEXT NOT NULL DEFAULT '',
        UNIQUE (day_id, action_order)
    );

CREATE TABLE training_plan_day (
        id INTEGER PRIMARY KEY,
        revision_id INTEGER NOT NULL REFERENCES training_plan_revision(id),
        day_order INTEGER NOT NULL,
        UNIQUE (revision_id, day_order)
    );

CREATE TABLE training_plan_revision (
        id INTEGER PRIMARY KEY,
        plan_id INTEGER NOT NULL REFERENCES training_plan(id),
        revision_number INTEGER NOT NULL,
        status TEXT NOT NULL,
        purpose TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        UNIQUE (plan_id, revision_number)
    );

CREATE TABLE training_plan_set (
        id INTEGER PRIMARY KEY,
        action_id INTEGER NOT NULL REFERENCES training_plan_action(id),
        set_order INTEGER NOT NULL,
        value REAL,
        unit TEXT NOT NULL,
        per_side INTEGER NOT NULL DEFAULT 0 CHECK (per_side IN (0, 1)), note TEXT NOT NULL DEFAULT '',
        UNIQUE (action_id, set_order)
    );

CREATE TABLE training_session (
        id INTEGER PRIMARY KEY,
        plan_revision_id INTEGER NOT NULL REFERENCES training_plan_revision(id),
        training_date TEXT NOT NULL,
        status TEXT NOT NULL,
        started_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        finished_at TEXT,
        abort_reason TEXT,
        abort_note TEXT,
        plan_day_order INTEGER NOT NULL DEFAULT 1
    );

CREATE TABLE training_session_action (
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES training_session(id),
        action_order INTEGER NOT NULL,
        exercise_name_snapshot TEXT NOT NULL,
        body_areas_snapshot_json TEXT NOT NULL,
        guidance_revision_id INTEGER,
        result TEXT,
        note TEXT, exercise_id INTEGER REFERENCES exercise(id), plan_day_order INTEGER NOT NULL DEFAULT 1, plan_action_order INTEGER NOT NULL DEFAULT 1, phase_snapshot TEXT NOT NULL DEFAULT 'main', rest_seconds_snapshot REAL NOT NULL DEFAULT 0, plan_note_snapshot TEXT NOT NULL DEFAULT '', guidance_reviewed_snapshot INTEGER,
        UNIQUE (session_id, action_order)
    );

CREATE TABLE training_session_actual_set (
            id INTEGER PRIMARY KEY,
            session_action_id INTEGER NOT NULL
                REFERENCES training_session_action(id),
            actual_order INTEGER NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            per_side INTEGER NOT NULL CHECK (per_side IN (0, 1)),
            UNIQUE (session_action_id, actual_order)
        );

CREATE TABLE training_session_set (
        id INTEGER PRIMARY KEY,
        session_action_id INTEGER NOT NULL REFERENCES training_session_action(id),
        set_order INTEGER NOT NULL,
        planned_value REAL,
        planned_unit TEXT NOT NULL,
        planned_per_side INTEGER NOT NULL CHECK (planned_per_side IN (0, 1)),
        actual_value REAL,
        actual_unit TEXT,
        actual_per_side INTEGER, plan_note_snapshot TEXT NOT NULL DEFAULT '',
        UNIQUE (session_action_id, set_order)
    );

CREATE UNIQUE INDEX bundled_exercise_identity ON exercise(bundled_exercise_key) WHERE bundled_exercise_key IS NOT NULL;

CREATE UNIQUE INDEX bundled_guidance_delivery ON exercise_guidance_revision(exercise_id, bundled_content_id, bundled_content_version) WHERE bundled_content_id IS NOT NULL AND bundled_content_version IS NOT NULL;

CREATE INDEX lifecycle_events_by_request ON library_lifecycle_event(request_id,id);

CREATE UNIQUE INDEX one_active_group_plan_revision ON group_plan_revision(plan_id) WHERE status='active';

CREATE UNIQUE INDEX one_active_group_session ON group_session((1)) WHERE status IN ('open','paused');

CREATE UNIQUE INDEX one_active_training_session ON training_session((1)) WHERE status IN ('open', 'paused');

CREATE UNIQUE INDEX plan_import_revision ON plan_import(revision_id) WHERE revision_id IS NOT NULL;

CREATE INDEX publisher_events_by_reference ON library_publisher_event(reference_id,id);

CREATE UNIQUE INDEX training_session_action_plan_position ON training_session_action(session_id, plan_day_order, plan_action_order);

CREATE UNIQUE INDEX training_session_action_session_day_order ON training_session_action(session_id, plan_day_order, action_order);

CREATE TRIGGER draft_only_group_plan_pin BEFORE INSERT ON group_plan_pin WHEN (SELECT r.status FROM group_plan_revision r JOIN group_plan_item i ON i.revision_id=r.id WHERE i.id=NEW.item_id)!='draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER draft_plan_action_only
        BEFORE INSERT ON training_plan_action
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              WHERE d.id = NEW.day_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER draft_plan_day_only
        BEFORE INSERT ON training_plan_day
        WHEN (SELECT status FROM training_plan_revision WHERE id = NEW.revision_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER draft_plan_set_only
        BEFORE INSERT ON training_plan_set
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              JOIN training_plan_action a ON a.day_id = d.id
              WHERE a.id = NEW.action_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER guard_group_actual_set_delete BEFORE DELETE ON group_actual_set WHEN (SELECT s.status FROM group_session s JOIN group_session_occurrence o ON s.id=o.session_id WHERE o.id=OLD.occurrence_id)!='open' BEGIN SELECT RAISE(ABORT, 'Only open sessions accept result changes.'); END;

CREATE TRIGGER guard_group_actual_set_insert BEFORE INSERT ON group_actual_set WHEN (SELECT s.status FROM group_session s JOIN group_session_occurrence o ON s.id=o.session_id WHERE o.id=NEW.occurrence_id)!='open' BEGIN SELECT RAISE(ABORT, 'Only open sessions accept result changes.'); END;

CREATE TRIGGER guard_group_actual_set_update BEFORE UPDATE ON group_actual_set WHEN (SELECT s.status FROM group_session s JOIN group_session_occurrence o ON s.id=o.session_id WHERE o.id=OLD.occurrence_id)!='open' OR (SELECT s.status FROM group_session s JOIN group_session_occurrence o ON s.id=o.session_id WHERE o.id=NEW.occurrence_id)!='open' BEGIN SELECT RAISE(ABORT, 'Only open sessions accept result changes.'); END;

CREATE TRIGGER guard_group_occurrence_result_delete BEFORE DELETE ON group_occurrence_result WHEN (SELECT s.status FROM group_session s JOIN group_session_occurrence o ON s.id=o.session_id WHERE o.id=OLD.occurrence_id)!='open' BEGIN SELECT RAISE(ABORT, 'Only open sessions accept result changes.'); END;

CREATE TRIGGER guard_group_occurrence_result_insert BEFORE INSERT ON group_occurrence_result WHEN (SELECT s.status FROM group_session s JOIN group_session_occurrence o ON s.id=o.session_id WHERE o.id=NEW.occurrence_id)!='open' BEGIN SELECT RAISE(ABORT, 'Only open sessions accept result changes.'); END;

CREATE TRIGGER guard_group_occurrence_result_update BEFORE UPDATE ON group_occurrence_result WHEN (SELECT s.status FROM group_session s JOIN group_session_occurrence o ON s.id=o.session_id WHERE o.id=OLD.occurrence_id)!='open' OR (SELECT s.status FROM group_session s JOIN group_session_occurrence o ON s.id=o.session_id WHERE o.id=NEW.occurrence_id)!='open' BEGIN SELECT RAISE(ABORT, 'Only open sessions accept result changes.'); END;

CREATE TRIGGER guard_group_plan_day_delete BEFORE DELETE ON group_plan_day WHEN (SELECT status FROM group_plan_revision WHERE id=OLD.revision_id) != 'draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER guard_group_plan_day_insert BEFORE INSERT ON group_plan_day WHEN (SELECT status FROM group_plan_revision WHERE id=NEW.revision_id) != 'draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER guard_group_plan_day_update BEFORE UPDATE ON group_plan_day WHEN (SELECT status FROM group_plan_revision WHERE id=OLD.revision_id) != 'draft' OR (SELECT status FROM group_plan_revision WHERE id=NEW.revision_id) != 'draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER guard_group_plan_item_delete BEFORE DELETE ON group_plan_item WHEN (SELECT status FROM group_plan_revision WHERE id=OLD.revision_id) != 'draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER guard_group_plan_item_insert BEFORE INSERT ON group_plan_item WHEN (SELECT status FROM group_plan_revision WHERE id=NEW.revision_id) != 'draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER guard_group_plan_item_update BEFORE UPDATE ON group_plan_item WHEN (SELECT status FROM group_plan_revision WHERE id=OLD.revision_id) != 'draft' OR (SELECT status FROM group_plan_revision WHERE id=NEW.revision_id) != 'draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER guard_group_plan_set_delete BEFORE DELETE ON group_plan_set WHEN (SELECT r.status FROM group_plan_revision r JOIN group_plan_item i ON i.revision_id=r.id WHERE i.id=OLD.item_id) != 'draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER guard_group_plan_set_insert BEFORE INSERT ON group_plan_set WHEN (SELECT r.status FROM group_plan_revision r JOIN group_plan_item i ON i.revision_id=r.id WHERE i.id=NEW.item_id) != 'draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER guard_group_plan_set_update BEFORE UPDATE ON group_plan_set WHEN (SELECT r.status FROM group_plan_revision r JOIN group_plan_item i ON i.revision_id=r.id WHERE i.id=OLD.item_id) != 'draft' OR (SELECT r.status FROM group_plan_revision r JOIN group_plan_item i ON i.revision_id=r.id WHERE i.id=NEW.item_id) != 'draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER immutable_content_snapshot_asset_delete BEFORE DELETE ON content_snapshot_asset BEGIN SELECT RAISE(ABORT, 'Retained catalog evidence is immutable.'); END;

CREATE TRIGGER immutable_content_snapshot_asset_update BEFORE UPDATE ON content_snapshot_asset BEGIN SELECT RAISE(ABORT, 'Retained catalog evidence is immutable.'); END;

CREATE TRIGGER immutable_content_snapshot_delete BEFORE DELETE ON content_snapshot BEGIN SELECT RAISE(ABORT, 'Retained catalog evidence is immutable.'); END;

CREATE TRIGGER immutable_content_snapshot_update BEFORE UPDATE ON content_snapshot BEGIN SELECT RAISE(ABORT, 'Retained catalog evidence is immutable.'); END;

CREATE TRIGGER immutable_conversion_mapping_delete BEFORE DELETE ON conversion_mapping BEGIN SELECT RAISE(ABORT, 'Conversion evidence is immutable.'); END;

CREATE TRIGGER immutable_conversion_mapping_update BEFORE UPDATE ON conversion_mapping BEGIN SELECT RAISE(ABORT, 'Conversion evidence is immutable.'); END;

CREATE TRIGGER immutable_conversion_original_delete BEFORE DELETE ON conversion_original BEGIN SELECT RAISE(ABORT, 'Conversion evidence is immutable.'); END;

CREATE TRIGGER immutable_conversion_original_update BEFORE UPDATE ON conversion_original BEGIN SELECT RAISE(ABORT, 'Conversion evidence is immutable.'); END;

CREATE TRIGGER immutable_conversion_registration_delete BEFORE DELETE ON conversion_registration BEGIN SELECT RAISE(ABORT, 'Conversion evidence is immutable.'); END;

CREATE TRIGGER immutable_conversion_registration_update BEFORE UPDATE ON conversion_registration BEGIN SELECT RAISE(ABORT, 'Conversion evidence is immutable.'); END;

CREATE TRIGGER immutable_conversion_run_delete BEFORE DELETE ON conversion_run BEGIN SELECT RAISE(ABORT, 'Conversion evidence is immutable.'); END;

CREATE TRIGGER immutable_conversion_run_update BEFORE UPDATE ON conversion_run BEGIN SELECT RAISE(ABORT, 'Conversion evidence is immutable.'); END;

CREATE TRIGGER immutable_group_plan_export_delete BEFORE DELETE ON group_plan_export BEGIN SELECT RAISE(ABORT, 'Plan evidence is immutable.'); END;

CREATE TRIGGER immutable_group_plan_export_update BEFORE UPDATE ON group_plan_export BEGIN SELECT RAISE(ABORT, 'Plan evidence is immutable.'); END;

CREATE TRIGGER immutable_group_plan_import_delete BEFORE DELETE ON group_plan_import BEGIN SELECT RAISE(ABORT, 'Plan evidence is immutable.'); END;

CREATE TRIGGER immutable_group_plan_import_update BEFORE UPDATE ON group_plan_import BEGIN SELECT RAISE(ABORT, 'Plan evidence is immutable.'); END;

CREATE TRIGGER immutable_group_plan_pin_delete BEFORE DELETE ON group_plan_pin BEGIN SELECT RAISE(ABORT, 'Plan evidence is immutable.'); END;

CREATE TRIGGER immutable_group_plan_pin_update BEFORE UPDATE ON group_plan_pin BEGIN SELECT RAISE(ABORT, 'Plan evidence is immutable.'); END;

CREATE TRIGGER immutable_group_plan_revision BEFORE UPDATE ON group_plan_revision WHEN OLD.status!='draft' AND (NEW.plan_id!=OLD.plan_id OR NEW.revision_number!=OLD.revision_number OR NEW.name!=OLD.name OR NEW.purpose!=OLD.purpose OR NEW.target_plan_name IS NOT OLD.target_plan_name OR NEW.rationale!=OLD.rationale OR NEW.source_json!=OLD.source_json OR NEW.created_at!=OLD.created_at OR NEW.activated_at IS NOT OLD.activated_at OR NEW.edit_token!=OLD.edit_token OR NOT (OLD.status='active' AND NEW.status='superseded')) BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER immutable_group_plan_revision_delete BEFORE DELETE ON group_plan_revision WHEN OLD.status!='draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END;

CREATE TRIGGER immutable_group_session_batch_delete BEFORE DELETE ON group_session_batch BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_batch_update BEFORE UPDATE ON group_session_batch BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_delete BEFORE DELETE ON group_session BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_event_delete BEFORE DELETE ON group_session_event BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_event_update BEFORE UPDATE ON group_session_event BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_export_delete BEFORE DELETE ON group_session_export BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_export_update BEFORE UPDATE ON group_session_export BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_feedback_area_delete BEFORE DELETE ON group_session_feedback_area BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_feedback_area_update BEFORE UPDATE ON group_session_feedback_area BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_feedback_delete BEFORE DELETE ON group_session_feedback BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_feedback_update BEFORE UPDATE ON group_session_feedback BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_occurrence_delete BEFORE DELETE ON group_session_occurrence BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_occurrence_update BEFORE UPDATE ON group_session_occurrence BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END;

CREATE TRIGGER immutable_group_session_snapshot BEFORE UPDATE ON group_session WHEN NEW.revision_id!=OLD.revision_id OR NEW.training_date!=OLD.training_date OR NEW.snapshot_json!=OLD.snapshot_json OR NEW.started_at!=OLD.started_at OR OLD.status NOT IN ('open','paused') BEGIN SELECT RAISE(ABORT, 'Session snapshot or terminal state is immutable.'); END;

CREATE TRIGGER immutable_library_content_delete BEFORE DELETE ON library_content BEGIN SELECT RAISE(ABORT, 'Retained catalog evidence is immutable.'); END;

CREATE TRIGGER immutable_library_content_update BEFORE UPDATE ON library_content BEGIN SELECT RAISE(ABORT, 'Retained catalog evidence is immutable.'); END;

CREATE TRIGGER immutable_library_lifecycle_event_delete BEFORE DELETE ON library_lifecycle_event BEGIN SELECT RAISE(ABORT, 'Lifecycle evidence is immutable.'); END;

CREATE TRIGGER immutable_library_lifecycle_event_update BEFORE UPDATE ON library_lifecycle_event BEGIN SELECT RAISE(ABORT, 'Lifecycle evidence is immutable.'); END;

CREATE TRIGGER immutable_library_lifecycle_request_delete BEFORE DELETE ON library_lifecycle_request BEGIN SELECT RAISE(ABORT, 'Lifecycle evidence is immutable.'); END;

CREATE TRIGGER immutable_library_lifecycle_request_update BEFORE UPDATE ON library_lifecycle_request BEGIN SELECT RAISE(ABORT, 'Lifecycle evidence is immutable.'); END;

CREATE TRIGGER immutable_library_plan_invalidation_delete BEFORE DELETE ON library_plan_invalidation BEGIN SELECT RAISE(ABORT, 'Lifecycle evidence is immutable.'); END;

CREATE TRIGGER immutable_library_plan_invalidation_update BEFORE UPDATE ON library_plan_invalidation BEGIN SELECT RAISE(ABORT, 'Lifecycle evidence is immutable.'); END;

CREATE TRIGGER immutable_library_publisher_event_delete BEFORE DELETE ON library_publisher_event BEGIN SELECT RAISE(ABORT, 'Lifecycle evidence is immutable.'); END;

CREATE TRIGGER immutable_library_publisher_event_update BEFORE UPDATE ON library_publisher_event BEGIN SELECT RAISE(ABORT, 'Lifecycle evidence is immutable.'); END;

CREATE TRIGGER immutable_library_review_delete BEFORE DELETE ON library_review_event BEGIN SELECT RAISE(ABORT, 'Review events are immutable.'); END;

CREATE TRIGGER immutable_library_review_update BEFORE UPDATE ON library_review_event BEGIN SELECT RAISE(ABORT, 'Review events are immutable.'); END;

CREATE TRIGGER immutable_plan_action_delete
        BEFORE DELETE ON training_plan_action
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              WHERE d.id = OLD.day_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER immutable_plan_action_update
        BEFORE UPDATE ON training_plan_action
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              WHERE d.id = OLD.day_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER immutable_plan_day_delete
        BEFORE DELETE ON training_plan_day
        WHEN (SELECT status FROM training_plan_revision WHERE id = OLD.revision_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER immutable_plan_day_update
        BEFORE UPDATE ON training_plan_day
        WHEN (SELECT status FROM training_plan_revision WHERE id = OLD.revision_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER immutable_plan_migration_provenance BEFORE UPDATE ON group_plan_revision WHEN NEW.migration_json IS NOT OLD.migration_json BEGIN SELECT RAISE(ABORT, 'Conversion provenance is immutable.'); END;

CREATE TRIGGER immutable_plan_revision_content
        BEFORE UPDATE ON training_plan_revision
        WHEN OLD.status != 'draft' AND (
            NEW.plan_id != OLD.plan_id OR
            NEW.revision_number != OLD.revision_number OR
            NEW.purpose != OLD.purpose OR
            NEW.created_at != OLD.created_at
        )
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER immutable_plan_revision_delete
        BEFORE DELETE ON training_plan_revision
        WHEN OLD.status != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER immutable_plan_set_delete
        BEFORE DELETE ON training_plan_set
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              JOIN training_plan_action a ON a.day_id = d.id
              WHERE a.id = OLD.action_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER immutable_plan_set_update
        BEFORE UPDATE ON training_plan_set
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              JOIN training_plan_action a ON a.day_id = d.id
              WHERE a.id = OLD.action_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

CREATE TRIGGER immutable_snapshot_asset_delete BEFORE DELETE ON snapshot_asset BEGIN SELECT RAISE(ABORT, 'Retained catalog evidence is immutable.'); END;

CREATE TRIGGER immutable_snapshot_asset_update BEFORE UPDATE ON snapshot_asset BEGIN SELECT RAISE(ABORT, 'Retained catalog evidence is immutable.'); END;

