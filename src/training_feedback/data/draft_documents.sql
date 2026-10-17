CREATE TABLE plan_edit_document (
    id TEXT PRIMARY KEY,
    format_version INTEGER NOT NULL CHECK(format_version = 1),
    edit_token INTEGER NOT NULL DEFAULT 1,
    purpose TEXT NOT NULL CHECK(purpose IN ('new','clone','edit','upgrade')),
    revision_id INTEGER UNIQUE REFERENCES group_plan_revision(id),
    source_revision_id INTEGER REFERENCES group_plan_revision(id),
    requested_base_number TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX one_edit_upgrade_source ON plan_edit_document(source_revision_id)
WHERE purpose='upgrade';
