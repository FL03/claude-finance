-- myfi_toolkit/myctx/schema/migrations/0002_v_mem_recent_7d_updated_at.sql
-- Fix v_mem_recent_7d to filter/order by `updated_at` ("last touched") instead
-- of `created_at`, matching the semantics skills/improve/SKILL.md §Store/
-- §Where the mechanism lives has always promised: "pinned rows OR anything
-- touched in the last 7 days."
--
-- Bug this closes: hooks/scripts/adaptation_capture.sh's dedup-by-title
-- harvest refreshes ONLY `updated_at` on a recurring prior (see its UPDATE
-- mem_entries SET updated_at = ? branch) -- it never touches `created_at`.
-- 0001_init.sql's original view filtered/ordered by `created_at`, so a prior
-- first stored more than 7 days ago that keeps recurring (its `updated_at`
-- bumped every time) would never re-appear in this view again, silently
-- defeating the IMPROVE loop's dedup-refresh-then-reinject cycle.
--
-- Append-only migration per myctx/migrate.py's gap-fill runner: DROP VIEW IF
-- EXISTS + CREATE VIEW, no rows touched, no other object changed. The
-- unixepoch() 7-day window is unchanged, only the keyed column moves from
-- `created_at` to `updated_at`.
BEGIN;

DROP VIEW IF EXISTS v_mem_recent_7d;

CREATE VIEW v_mem_recent_7d AS
  SELECT * FROM mem_entries
  WHERE updated_at >= unixepoch() - 7 * 86400 OR pinned = 1
  ORDER BY pinned DESC, updated_at DESC;

COMMIT;
