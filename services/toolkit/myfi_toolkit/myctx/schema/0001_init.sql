-- myfi_toolkit/myctx/schema/0001_init.sql
-- myfi v0.0.0 baseline schema for the per-project (`.myfi/myfi.db`) and
-- optional global (`~/.myfi/global.db`) context registry.
--
-- Shape mirrors shepherd's `skills/context/schema/0001_init.sql`, trimmed to
-- the tables the myfi IMPROVE/adaptation loop and harness hooks (Wave 4/6)
-- actually read and write: `projects` + `sessions` for the running-context
-- identity, `mem_entries` (with a `prior` kind baked in from the start, so
-- there is no shepherd-style 0011-style ALTER-TABLE-recreate debt later) for
-- doctrine/notes/decisions/harvested-priors, and `discovery_findings` /
-- `audit_findings` for the finance-domain discovery + audit loop.
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

BEGIN;

CREATE TABLE schema_versions (
  version    INTEGER PRIMARY KEY,
  applied_at INTEGER NOT NULL,
  checksum   TEXT NOT NULL
);

CREATE TABLE projects (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL DEFAULT '',
  root_path  TEXT NOT NULL DEFAULT '',
  metadata   TEXT CHECK(metadata IS NULL OR json_valid(metadata)),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE sessions (
  id          TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE,
  started_at  INTEGER NOT NULL,
  ended_at    INTEGER,
  agent_role  TEXT,
  metadata    TEXT CHECK(metadata IS NULL OR json_valid(metadata))
);
CREATE INDEX idx_sessions_project ON sessions(project_id);

CREATE TABLE mem_entries (
  id          TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE,
  kind        TEXT NOT NULL CHECK(kind IN
                ('doctrine','note','decision','incident','session','prior')),
  title       TEXT NOT NULL,
  body        TEXT NOT NULL,
  tags        TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(tags)),
  pinned      INTEGER NOT NULL DEFAULT 0,
  source_path TEXT,
  created_at  INTEGER NOT NULL,
  updated_at  INTEGER NOT NULL
);
CREATE INDEX idx_mem_project_kind   ON mem_entries(project_id, kind);
CREATE INDEX idx_mem_project_pinned ON mem_entries(project_id, pinned) WHERE pinned = 1;

CREATE TABLE discovery_findings (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id    TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE,
  sprint_branch TEXT,
  discovery_run TEXT NOT NULL,
  section       TEXT,
  title         TEXT NOT NULL,
  body          TEXT NOT NULL,
  sources       TEXT CHECK(sources IS NULL OR json_valid(sources)),
  created_at    INTEGER NOT NULL
);
CREATE INDEX idx_discovery_sprint_run
  ON discovery_findings(project_id, sprint_branch, discovery_run);

CREATE TABLE audit_findings (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id    TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE,
  sprint_branch TEXT,
  concern       TEXT NOT NULL,
  severity      TEXT NOT NULL CHECK(severity IN
                  ('info','low','medium','high','critical')),
  hypothesis    TEXT NOT NULL,
  finding       TEXT NOT NULL,
  evidence_refs TEXT CHECK(evidence_refs IS NULL OR json_valid(evidence_refs)),
  created_at    INTEGER NOT NULL
);
CREATE INDEX idx_audit_sprint_severity
  ON audit_findings(project_id, sprint_branch, severity);

CREATE VIEW v_mem_recent_7d AS
  SELECT * FROM mem_entries
  WHERE created_at >= unixepoch() - 7 * 86400 OR pinned = 1
  ORDER BY pinned DESC, created_at DESC;

-- The schema_versions row for this baseline is recorded by migrate.py, which
-- computes checksum = sha256(this file's bytes) uniformly for every applied
-- migration. Do NOT self-insert here (a literal would shadow the real hash and
-- migrate.py's INSERT OR IGNORE would silently no-op) -- see test_myctx.py.

COMMIT;
