#!/usr/bin/env bash
# myfi hook -- Stop: mechanize the IMPROVE loop's harvest+store step
#
# Implements the "harness's dispatch-time hooks... are the mechanized writer
# that turns a fresh audit_findings/discovery_findings row into a harvested
# mem_entries(kind='prior') row without a human doing it by hand" contract
# from skills/improve/SKILL.md §Where the mechanism lives.
#
# Deterministic half only (CLAUDE.md's latent/deterministic split): promoting
# a HIGH/CRITICAL audit_findings row to a mem_entries(kind='prior') prior is a
# same-input-same-output decision (severity is an enum column), so it is done
# here in SQL, not by an LLM. skills/improve/SKILL.md also names
# discovery_findings as a harvest source ("discovery insights that name a
# durable pattern (not an incidental typo)") -- but "durable pattern vs
# incidental typo" is a judgment call with no deterministic proxy in the
# discovery_findings schema (no severity-equivalent column), so promoting it
# here would be exactly the "latent work smuggled into a shell script"
# CLAUDE.md warns against. That half of the loop is intentionally left to a
# future LLM-mediated harvest pass, not silently done wrong in bash.
#
# Schema (myfi_toolkit/myctx/schema/0001_init.sql):
#   audit_findings(id, project_id, sprint_branch, concern, severity, hypothesis, finding, evidence_refs, created_at)
#   mem_entries(id, project_id, kind, title, body, tags, pinned, source_path, created_at, updated_at)
#
# Harvest rule (skills/improve/SKILL.md §Harvest/§Store, mechanically applied):
#   - candidate: audit_findings.severity IN ('high','critical') AND not yet harvested
#     (no existing mem_entries row with source_path = 'audit_findings:<id>')
#   - title := "prior: <concern>"; dedup BY TITLE (not by source row) -- a
#     recurring concern from a NEW audit_findings row refreshes updated_at on
#     the existing prior instead of growing a duplicate.
#   - bounded: only info/low/medium-excluded, dedup-by-title rows ever land --
#     never a firehose (skills/improve/SKILL.md §Bounded, not a firehose).
#
# Bootstraps the schema "via bin/myfi-toolkit" (skills/improve/SKILL.md
# §Where the mechanism lives + this unit's [EVALS]) before touching the db:
# bin/myfi-toolkit db init is the packaged gap-fill entry point, and its
# underlying myctx.db module is stdlib-only, so this works even without
# poetry installed (bin/myfi-toolkit's own PYTHONPATH fallback). No CLI verb
# exists (or may be added -- services/toolkit/** is this unit's
# must_not_touch) to INSERT a row, so the actual read/harvest/write runs
# through python3's stdlib sqlite3 directly against the bootstrapped db --
# the same pattern shepherd's own hooks/scripts/session_open.sh uses to query
# its registry directly rather than shelling through its CLI wrapper.
#
# Input  (stdin): Stop JSON -- consumed; the sweep is a blind DB pass, not a
#   parse of the just-finished turn's transcript.
# Output (stdout): {"systemMessage":"..."} when something was harvested or
#   refreshed; exit 0 silently otherwise. Never blocks the stop (no
#   "decision" field is ever emitted).

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/_lib.sh"

cat >/dev/null  # consume the Stop payload; the sweep doesn't parse it

is_myfi_project || exit 0

repo_root=$(myfi_repo_root)
db_path=$(myfi_db_path "$repo_root")

# Bootstrap the schema via bin/myfi-toolkit, but only when the db doesn't
# exist yet -- a Stop hook fires on every turn, and re-forking a python3
# process to gap-fill migrations that (for a db that already exists) are
# almost always already current is pure overhead. Real gap-fill across a
# future schema bump happens through normal agent use: `@advisor`/`@quant`/
# `@worker` all carry the `mcp__plugin_myfi_myfi-toolkit__db_migrate` tool
# (skills/myfi/SKILL.md §TOOLKIT reference) -- this hook only needs to cover
# the FIRST-ever Stop in a project that has no db at all yet. Best-effort:
# a missing bin/ (true inside a minimal test sandbox) or a poetry-less
# environment must not break Stop -- db init's own PYTHONPATH fallback covers
# the poetry-less case, so this only truly no-ops when bin/myfi-toolkit
# itself is absent.
bin="$repo_root/bin/myfi-toolkit"
if [[ ! -f "$db_path" && -x "$bin" ]]; then
  ( cd "$repo_root" && PWD="$repo_root" "$bin" db init >/dev/null 2>&1 ) || true
fi

[[ -f "$db_path" ]] || pass_silent "adaptation_capture" "" ""

result=$(python3 - "$db_path" "$repo_root" <<'PY' 2>/dev/null || true
import json
import sqlite3
import sys
import time
import uuid

db_path, repo_root = sys.argv[1], sys.argv[2]

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
conn.row_factory = sqlite3.Row
try:
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if not {"projects", "mem_entries", "audit_findings"} <= tables:
        # Schema not bootstrapped (db init failed/unavailable) -- nothing to do.
        print(json.dumps({"harvested": 0, "recurred": 0}))
        raise SystemExit(0)

    project_id = repo_root
    now = int(time.time())

    if conn.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone() is None:
        conn.execute(
            "INSERT INTO projects (id, name, root_path, metadata, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?)",
            (project_id, "myfi", repo_root, None, now, now),
        )

    already_harvested_ids = {
        row[0].split(":", 1)[1]
        for row in conn.execute(
            "SELECT source_path FROM mem_entries "
            "WHERE kind='prior' AND source_path LIKE 'audit_findings:%'"
        ).fetchall()
        if row[0]
    }

    candidates = conn.execute(
        "SELECT id, sprint_branch, concern, severity, finding FROM audit_findings "
        "WHERE project_id = ? AND severity IN ('high','critical') ORDER BY id",
        (project_id,),
    ).fetchall()

    harvested = 0
    recurred = 0
    for row in candidates:
        fid = str(row["id"])
        if fid in already_harvested_ids:
            continue
        title = "prior: {}".format(row["concern"])
        existing = conn.execute(
            "SELECT id FROM mem_entries WHERE project_id = ? AND kind='prior' AND title = ?",
            (project_id, title),
        ).fetchone()
        if existing is not None:
            conn.execute(
                "UPDATE mem_entries SET updated_at = ? WHERE id = ?", (now, existing["id"])
            )
            recurred += 1
        else:
            body = (
                "{finding}\n\nseverity: {severity}\nsprint: {sprint}\n"
                "harvested_from: audit_findings:{fid}"
            ).format(
                finding=row["finding"],
                severity=row["severity"],
                sprint=row["sprint_branch"] or "unknown",
                fid=fid,
            )
            tags = json.dumps([row["severity"], "audit-harvest"])
            conn.execute(
                "INSERT INTO mem_entries "
                "(id, project_id, kind, title, body, tags, pinned, source_path, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,0,?,?,?)",
                (
                    uuid.uuid4().hex,
                    project_id,
                    "prior",
                    title,
                    body,
                    tags,
                    "audit_findings:{}".format(fid),
                    now,
                    now,
                ),
            )
            harvested += 1
        already_harvested_ids.add(fid)

    conn.commit()
    print(json.dumps({"harvested": harvested, "recurred": recurred}))
finally:
    conn.close()
PY
)

[[ -z "$result" ]] && pass_silent "adaptation_capture" "" ""

harvested=$(printf '%s' "$result" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("harvested",0))' 2>/dev/null || echo 0)
recurred=$(printf '%s' "$result" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("recurred",0))' 2>/dev/null || echo 0)

if [[ "${harvested:-0}" -eq 0 && "${recurred:-0}" -eq 0 ]]; then
  pass_silent "adaptation_capture" "" ""
fi

msg="[myfi] IMPROVE harvest: ${harvested:-0} new prior(s), ${recurred:-0} recurring concern(s) refreshed."$'\n'
msg+="  Store: $db_path (mem_entries, kind='prior')"$'\n'
msg+="  See skills/improve/SKILL.md §Harvest/§Store."

log_event "adaptation_capture" "harvest" "" "" \
  "$(emit_json_obj harvested "${harvested:-0}" recurred "${recurred:-0}")"
emit_message "$msg" "" "" ""
