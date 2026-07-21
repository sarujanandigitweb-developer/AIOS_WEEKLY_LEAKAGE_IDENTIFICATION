#!/usr/bin/env python3
"""
WLSP — ONE production upload workflow for the Weekly Leakage Identification &
Stop-Loss Protocol.

A single uploader publishes BOTH:
  1. the master dashboard          dashboard/leakage_dashboard.html
  2. every Portfolio Holder file   dashboard/portfolio_holders/*.html

into tech_team_outputs.ph_task, using ONE code path. The complete HTML file is
stored as plain UTF-8 text via a BOUND PARAMETER (byte-exact — never executed,
parsed, compressed, minified, escaped, chunked, or Base64-encoded).

Rules (identical for master and every PH):
  * The record is located ONLY by task_id (never by a hardcoded row id).
  * task_id exists  -> UPDATE html_content + version_status + assigned_user_team
                       + updated_at. Identity/metadata (project, task, developer,
                       assigned_user, description, phase/version level) is untouched.
  * task_id missing -> INSERT full metadata; PostgreSQL generates the id (IDENTITY).
  * Assigned User + Task ID for PH files are DERIVED FROM THE FILENAME (no hardcoding):
        arudchelvi_leakage.html -> "Arudchelvi" -> WLSP_Arudchelvi_Leakage_Dashboard-V1
  * The master's identity (Bietrick / WLSP_Bietrick_Leakage_Dashboard-V1) is the one
    fixed mapping, because its file is named leakage_dashboard.html (not <name>_leakage.html).
  * By default EVERY Portfolio Holder is processed (no ignores). WLSP_IGNORE is an
    optional comma-separated env override only.
  * One failing dashboard never stops the run; failures are reported at the end.

New Portfolio Holders are supported automatically: drop a new *_leakage.html into
portfolio_holders/ and the next run detects it, derives its Task ID, INSERTs it,
and verifies it — no code changes required.

Weekly cron:
    0 6 * * 1 cd <repo> && python3 dashboard/refresh_dashboard.py >> log && \
              python3 dashboard/refresh_ph_dashboards.py >> log

Connection (env overrides the defaults): PGHOST PGPORT PGDATABASE PGUSER PGPASSWORD
Requires: pip install psycopg2-binary
"""

import os, sys, glob, hashlib, re, json
import psycopg2

HERE        = os.path.dirname(os.path.abspath(__file__))
MASTER_PATH = os.path.join(HERE, "leakage_dashboard.html")
PH_DIR      = os.path.join(HERE, "portfolio_holders")
SUFFIX      = "_leakage.html"

# --- master dashboard mapping (located ONLY by task_id; id=8 is never used) ---
MASTER_USER    = "Bietrick"
MASTER_TASK_ID = "WLSP_Bietrick_Leakage_Dashboard-V1"

DB_CONFIG = {
    "host":     os.getenv("PGHOST", "149.28.134.54"),
    "port":     os.getenv("PGPORT", "5435"),
    "dbname":   os.getenv("PGDATABASE", "order_management_copy"),
    "user":     os.getenv("PGUSER", "temp_user"),
    "password": os.getenv("PGPASSWORD", "12we34rt"),
    "connect_timeout": 15,
}

# Default: process EVERY dashboard (including abinayaa). WLSP_IGNORE is optional only.
IGNORE = {f.strip() for f in os.getenv("WLSP_IGNORE", "").split(",") if f.strip()}

# --- fixed metadata used ONLY for INSERTs (existing rows keep their metadata) ---
PROJECT_NAME   = "Weekly Leakage Identification & Stop-Loss Protocol"
PROJECT_CODE   = "WLSP"
TASK_NAME      = "Weekly Amazon FBM Leakage Action Results"
TEAM           = "Technical"
DEVELOPER      = "Sarujanan"
PHASE_LEVEL    = 1
VERSION_LEVEL  = 1

# --- publication state: re-asserted on every run, for INSERT and UPDATE alike ---
VERSION_STATUS     = "released"      # lowercase is the value the feed reads
ASSIGNED_USER_TEAM = "ph_priors"     # tech_team_outputs.ph_task.assigned_user_team
DESCRIPTION = (
    "Displays the latest Portfolio Holder leakage analysis results, including L1–L5 "
    "leakage categories, affected ASINs, account information, action recommendations, "
    "verification status, and weekly performance summaries. The dashboard is refreshed "
    "automatically every Monday using the previous Monday-to-Sunday reporting period to "
    "provide the latest validated weekly leakage results."
)


def ph_name_from_filename(fname):
    """arudchelvi_leakage.html -> 'Arudchelvi' ; tharsika_jaffna_leakage.html -> 'Tharsika_Jaffna'"""
    base = os.path.basename(fname)
    if base.endswith(SUFFIX):
        base = base[: -len(SUFFIX)]
    return base.title()


def task_id_for(name):
    return f"WLSP_{name}_Leakage_Dashboard-V1"


# marker block wrapping the embedded dashboardData in every generated HTML
DATA_START, DATA_END = "<!-- WLSP_DATA_START -->", "<!-- WLSP_DATA_END -->"


def ph_name_from_data(path):
    """Return the ORIGINAL Portfolio Holder name exactly as embedded in the dashboard data
       (the "ph" value, which came straight from ph_category.user_name) — preserving original
       case and characters such as parentheses. This is NOT derived from the filename.
       Returns None if the value cannot be read (caller falls back to the filename name)."""
    try:
        txt = open(path, encoding="utf-8").read()
        mb = re.search(re.escape(DATA_START) + r"(.*?)" + re.escape(DATA_END), txt, re.DOTALL)
        if not mb:
            return None
        mj = re.search(r"const\s+dashboardData\s*=\s*(\{.*\})\s*;", mb.group(1), re.DOTALL)
        if not mj:
            return None
        data = json.loads(mj.group(1))
        ps = data.get("ph_summary") or []
        if ps and ps[0].get("ph"):
            return ps[0]["ph"]
        for k in ("l1", "l2", "l3", "l4", "l5"):        # fallback: first flagged row's ph
            for r in data.get(k, []):
                if r.get("ph"):
                    return r["ph"]
    except Exception:
        return None
    return None


def build_worklist():
    """[(kind, display, path, assigned_user, task_id), ...] — master first, then every PH file."""
    items = []
    if os.path.isfile(MASTER_PATH):
        items.append(("Master", "Master", MASTER_PATH, MASTER_USER, MASTER_TASK_ID))
    else:
        print(f"WARNING: master not found: {MASTER_PATH}")
    for path in sorted(glob.glob(os.path.join(PH_DIR, "*.html"))):
        if os.path.basename(path) in IGNORE:
            continue
        # task_id + filename stay filename-derived (UNCHANGED). assigned_user is the ORIGINAL
        # PH name from the dashboard data (ph_category.user_name), NOT the filename .title().
        task_id = task_id_for(ph_name_from_filename(path))
        user    = ph_name_from_data(path) or ph_name_from_filename(path)
        items.append(("PH", user, path, user, task_id))
    return items


def upload_one(cur, kind, display, path, assigned_user, task_id):
    """ONE upsert path for master and PH alike. Located ONLY by task_id. Returns a result dict."""
    with open(path, "rb") as f:
        raw = f.read()
    html      = raw.decode("utf-8")          # bound parameter -> byte-exact plain UTF-8
    src_bytes = len(raw)
    src_md5   = hashlib.md5(raw).hexdigest()

    cur.execute("SELECT id FROM tech_team_outputs.ph_task WHERE task_id=%s", (task_id,))
    hit = cur.fetchone()

    if hit:  # ---- exists: UPDATE html_content + the publication-state columns ----
        op = "UPDATE"
        # version_status is the REVIEWER lifecycle field: once action_took_by is set the
        # holder has actioned this task (completed / rejected / active) and the weekly
        # refresh must never stomp that back to 'released'. Un-actioned rows are re-asserted.
        cur.execute("""UPDATE tech_team_outputs.ph_task
                          SET html_content=%s,
                              version_status = CASE WHEN action_took_by IS NULL
                                                    THEN %s ELSE version_status END,
                              assigned_user_team=%s,
                              updated_at=now()
                        WHERE task_id=%s""",
            (html, VERSION_STATUS, ASSIGNED_USER_TEAM, task_id))
    else:    # ---- missing: INSERT full metadata; id auto-generated by PostgreSQL ----
        op = "INSERT"
        cur.execute("""INSERT INTO tech_team_outputs.ph_task
              (project_name, project_code, task_name, task_id, team, developer,
               assigned_user, assigned_user_team, html_content, description,
               phase_level, version_level, version_status, created_at, updated_at)
              VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now())""",
            (PROJECT_NAME, PROJECT_CODE, TASK_NAME, task_id, TEAM, DEVELOPER,
             assigned_user, ASSIGNED_USER_TEAM, html, DESCRIPTION,
             PHASE_LEVEL, VERSION_LEVEL, VERSION_STATUS))

    # ---- verify (read back by task_id; byte-exact html + schema columns) ----
    cur.execute("""SELECT id, task_id, assigned_user, assigned_user_team, version_status,
                          action_took_by,
                          octet_length(html_content) AS html_size,
                          md5(html_content) AS html_md5, updated_at
                     FROM tech_team_outputs.ph_task WHERE task_id=%s""", (task_id,))
    rid, _tid, r_user, r_team, r_status, r_actor, size, r_md5, upd = cur.fetchone()

    actioned  = r_actor is not None      # reviewer owns version_status from here on
    html_ok   = bool(size) and size > 0 and size == src_bytes and r_md5 == src_md5
    status_ok = actioned or r_status == VERSION_STATUS
    team_ok   = r_team == ASSIGNED_USER_TEAM
    ok = html_ok and status_ok and team_ok

    problems = []
    if not html_ok:
        problems.append(f"size {size}/{src_bytes}, md5 {'ok' if r_md5==src_md5 else 'MISMATCH'}")
    if not status_ok:
        problems.append(f"version_status {r_status!r} != {VERSION_STATUS!r}")
    if not team_ok:
        problems.append(f"assigned_user_team {r_team!r} != {ASSIGNED_USER_TEAM!r}")

    return {"kind": kind, "display": display, "op": op, "id": rid, "size": size,
            "src": src_bytes, "status": "PASS" if ok else "FAIL",
            "version_status": r_status, "assigned_user_team": r_team,
            "error": None if ok else "; ".join(problems)}


def main():
    work = build_worklist()
    print(f"scan: master + {PH_DIR}")
    print(f"ignore override: {sorted(IGNORE) or 'none'} | dashboards to process: {len(work)}\n")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        sys.exit(f"FATAL: cannot connect to database: {e}")
    conn.autocommit = False

    results = []
    for kind, display, path, user, tid in work:
        cur = conn.cursor()
        try:
            r = upload_one(cur, kind, display, path, user, tid)
            conn.commit()                       # per-dashboard commit -> one failure can't roll back others
        except Exception as e:
            conn.rollback()
            r = {"kind": kind, "display": display, "op": "-", "id": "-", "size": 0,
                 "src": 0, "status": "FAIL", "version_status": None,
                 "assigned_user_team": None, "error": str(e).splitlines()[0]}
        finally:
            cur.close()
        results.append(r)
        print(f"  {r['status']:4}  {r['op']:6}  id={str(r['id']):<4} "
              f"{r['display']:<18} {str(r['size']):>7} bytes"
              + (f"   <- {r['error']}" if r['status'] == 'FAIL' else ""))
    conn.close()

    # ---- summary table ----
    print("\n| Dashboard | Operation | Row ID | HTML Size | version_status | assigned_user_team | Status |")
    print("|---|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r['display']} | {r['op']} | {r['id']} | {r['size']} "
              f"| {r.get('version_status') or '-'} | {r.get('assigned_user_team') or '-'} | {r['status']} |")

    masters = [r for r in results if r["kind"] == "Master"]
    phs     = [r for r in results if r["kind"] == "PH"]
    ins     = sum(1 for r in results if r["op"] == "INSERT")
    upd     = sum(1 for r in results if r["op"] == "UPDATE")
    pas     = sum(1 for r in results if r["status"] == "PASS")
    fail    = [r for r in results if r["status"] == "FAIL"]
    print(f"\nTotal dashboards processed     : {len(results)}")
    print(f"Master dashboards processed    : {len(masters)}")
    print(f"Portfolio Holder dashboards    : {len(phs)}")
    print(f"INSERTS                        : {ins}")
    print(f"UPDATES                        : {upd}")
    print(f"PASS                           : {pas}")
    print(f"FAIL                           : {len(fail)}")
    if fail:
        print("Failed dashboards:")
        for r in fail:
            print(f"  - {r['display']}: {r['error']}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
