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

APPEND-VERSIONED, ONE ROW PER (Portfolio Holder, reporting week):
  * Each PH has a task_id STEM (WLSP_<Name>_Leakage_Dashboard) derived from the filename.
    A weekly report is one row: task_id = <stem>-V{n}, version_level = n.
  * The reporting week = summary.report_date (previous Sunday) embedded in the HTML.
  * Per PH, compared against the latest existing version's embedded week:
        file week  >  latest  -> INSERT V(n+1); the previous week's row is FROZEN, untouched.
        file week  == latest  -> same week: idempotent UPDATE of that row's html
                                 (SKIP if a reviewer already actioned it — keep it frozen).
        file week  <  latest  -> stale backfill: SKIP (never create a lower version).
        no row yet            -> INSERT V1.
  * A new version is born 'released'; the reviewer later sets 'completed'. A completed
    (actioned) row is never rewritten — history is immutable. Only the NEW week's row
    carries the NEW week's html; last week's row keeps last week's html and status.
  * Assigned User is the ORIGINAL data name; the stem is filename-derived. The master
    (leakage_dashboard.html) maps to the Bietrick stem.
  * EVERY Portfolio Holder is processed by default. WLSP_IGNORE is an optional override.
  * One failing dashboard never stops the run; failures/skips are reported at the end.

New Portfolio Holders are supported automatically: drop a new *_leakage.html into
portfolio_holders/ and the next run INSERTs their V1 and verifies it — no code changes.

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

# --- master dashboard mapping (located by task_id STEM; the -V{n} suffix is per weekly run) ---
MASTER_USER = "Bietrick"
MASTER_STEM = "WLSP_Bietrick_Leakage_Dashboard"

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
FIRST_VERSION  = 1               # a PH's very first weekly report is V1; each later week is V(n+1)

# reporting-week key: summary.report_date (previous Sunday) embedded in the HTML. 'YYYY-MM-DD'
# sorts lexicographically == chronologically, so plain string comparison orders the weeks.
REPORT_DATE_RE = re.compile(r'"report_date"\s*:\s*"(\d{4}-\d{2}-\d{2})"')

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


def task_stem_for(name):
    """PH filename-name -> task_id STEM (no version suffix). Each weekly run appends -V1, -V2, ...
       so one Portfolio Holder accumulates one row per reporting week, previous weeks frozen."""
    return f"WLSP_{name}_Leakage_Dashboard"


def report_week_of(text):
    """The reporting-week key for a dashboard = summary.report_date (the previous Sunday) embedded
       in the HTML. Returns 'YYYY-MM-DD' or None if absent."""
    m = REPORT_DATE_RE.search(text)
    return m.group(1) if m else None


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
        items.append(("Master", "Master", MASTER_PATH, MASTER_USER, MASTER_STEM))
    else:
        print(f"WARNING: master not found: {MASTER_PATH}")
    for path in sorted(glob.glob(os.path.join(PH_DIR, "*.html"))):
        if os.path.basename(path) in IGNORE:
            continue
        # task_id STEM stays filename-derived (UNCHANGED). assigned_user is the ORIGINAL PH name
        # from the dashboard data (ph_category.user_name), NOT the filename .title().
        stem = task_stem_for(ph_name_from_filename(path))
        user = ph_name_from_data(path) or ph_name_from_filename(path)
        items.append(("PH", user, path, user, stem))
    return items


def _result(kind, display, op, rid, size, src, status, ver, vstatus, team, tid, error):
    return {"kind": kind, "display": display, "op": op, "id": rid, "size": size, "src": src,
            "status": status, "version": ver, "version_status": vstatus,
            "assigned_user_team": team, "task_id": tid, "error": error}


def upload_one(cur, kind, display, path, assigned_user, task_stem):
    """Append-versioned publish — ONE row per (Portfolio Holder, reporting week).

    The reporting week is summary.report_date embedded in the HTML. Given the latest existing
    version for this PH (highest -V{n}) and its embedded week:
      * no row yet                    -> INSERT V1
      * file week  >  latest week     -> INSERT V(n+1); the previous week's row is left frozen
      * file week  == latest week     -> same week: idempotent UPDATE of that row's html
                                         (but SKIP if a reviewer already actioned it — keep it frozen)
      * file week  <  latest week     -> stale backfill: SKIP (never create a lower version)

    A brand-new version is INSERTed with version_status='released'; the reviewer later moves it to
    'completed'. That completed row is never touched again — next week appends a fresh version."""
    with open(path, "rb") as f:
        raw = f.read()
    html      = raw.decode("utf-8")          # bound parameter -> byte-exact plain UTF-8
    src_bytes = len(raw)
    src_md5   = hashlib.md5(raw).hexdigest()

    file_week = report_week_of(html)
    if not file_week:
        return _result(kind, display, "-", "-", src_bytes, src_bytes, "FAIL", None, None, None,
                       None, "could not read summary.report_date from HTML (cannot key the week)")

    # latest existing version for this PH + its embedded reporting week (substring avoids a blob read)
    like_pat = task_stem.replace("\\", "\\\\").replace("_", "\\_").replace("%", "\\%") + "-V%"
    cur.execute("""
        SELECT id, task_id, version_level, version_status, action_took_by,
               substring(html_content from '"report_date"\\s*:\\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"')
          FROM tech_team_outputs.ph_task
         WHERE task_id LIKE %s ESCAPE '\\'
         ORDER BY version_level DESC NULLS LAST, id DESC
         LIMIT 1""", (like_pat,))
    latest = cur.fetchone()

    if latest is None:
        op, new_ver, target_tid = "INSERT", FIRST_VERSION, f"{task_stem}-V{FIRST_VERSION}"
    else:
        lid, ltid, lver, lstatus, lactor, lweek = latest
        lver = lver or 0
        if lweek is not None and file_week < lweek:
            return _result(kind, display, "SKIP", lid, 0, src_bytes, "SKIP", lver, lstatus, None,
                           ltid, f"stale: file week {file_week} < latest V{lver} week {lweek}; not appended")
        if lweek == file_week:                       # same reporting week -> idempotent re-run
            if lactor is not None:                   # reviewer already actioned this week -> freeze
                return _result(kind, display, "SKIP", lid, 0, src_bytes, "SKIP", lver, lstatus, None,
                               ltid, f"week {file_week} already published as V{lver} and actioned "
                                     f"({lstatus}); left frozen")
            op, target_tid = "UPDATE", ltid
        else:                                        # newer week -> append the next version
            op, new_ver, target_tid = "INSERT", lver + 1, f"{task_stem}-V{lver + 1}"

    if op == "UPDATE":
        # same-week refresh: replace only this week's html (+ team stamp). Never touch version_level,
        # version_status, created_at — the row's identity and any reviewer state stay put.
        cur.execute("""UPDATE tech_team_outputs.ph_task
                          SET html_content=%s, assigned_user_team=%s, updated_at=now()
                        WHERE task_id=%s""", (html, ASSIGNED_USER_TEAM, target_tid))
    else:                                            # INSERT a new weekly version
        cols = """(project_name, project_code, task_name, task_id, team, developer,
                   assigned_user, assigned_user_team, html_content, description,
                   phase_level, version_level, version_status, created_at, updated_at)"""
        vals = (PROJECT_NAME, PROJECT_CODE, TASK_NAME, target_tid, TEAM, DEVELOPER,
                assigned_user, ASSIGNED_USER_TEAM, html, DESCRIPTION,
                PHASE_LEVEL, new_ver, VERSION_STATUS)
        cur.execute("SAVEPOINT ins")
        try:
            cur.execute(f"""INSERT INTO tech_team_outputs.ph_task {cols}
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now())""", vals)
        except psycopg2.errors.UniqueViolation:
            # ph_task.id is GENERATED BY DEFAULT AS IDENTITY; when another team INSERTs an explicit
            # id the sequence falls behind max(id) and nextval collides. We lack UPDATE on the
            # sequence to setval it, so allocate the id ourselves. Weekly INSERTs make this likely.
            cur.execute("ROLLBACK TO SAVEPOINT ins")
            cur.execute(f"""INSERT INTO tech_team_outputs.ph_task
                            (id, {cols[1:]}
                            VALUES ((SELECT COALESCE(max(id),0)+1 FROM tech_team_outputs.ph_task),
                                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now())""", vals)

    # ---- verify the row we wrote (byte-exact html + schema columns) ----
    cur.execute("""SELECT id, version_level, assigned_user_team, version_status, action_took_by,
                          octet_length(html_content), md5(html_content)
                     FROM tech_team_outputs.ph_task WHERE task_id=%s""", (target_tid,))
    rid, r_ver, r_team, r_status, r_actor, size, r_md5 = cur.fetchone()

    actioned  = r_actor is not None                  # reviewer owns version_status from here on
    html_ok   = bool(size) and size > 0 and size == src_bytes and r_md5 == src_md5
    team_ok   = r_team == ASSIGNED_USER_TEAM
    status_ok = actioned or r_status == VERSION_STATUS
    ok = html_ok and team_ok and status_ok

    problems = []
    if not html_ok:
        problems.append(f"size {size}/{src_bytes}, md5 {'ok' if r_md5==src_md5 else 'MISMATCH'}")
    if not team_ok:
        problems.append(f"assigned_user_team {r_team!r} != {ASSIGNED_USER_TEAM!r}")
    if not status_ok:
        problems.append(f"version_status {r_status!r} != {VERSION_STATUS!r}")

    return _result(kind, display, op, rid, size, src_bytes, "PASS" if ok else "FAIL",
                   r_ver, r_status, r_team, target_tid, None if ok else "; ".join(problems))


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
    for kind, display, path, user, stem in work:
        cur = conn.cursor()
        try:
            r = upload_one(cur, kind, display, path, user, stem)
            conn.commit()                       # per-dashboard commit -> one failure can't roll back others
        except Exception as e:
            conn.rollback()
            r = _result(kind, display, "-", "-", 0, 0, "FAIL", None, None, None,
                        stem, str(e).splitlines()[0])
        finally:
            cur.close()
        results.append(r)
        vtag = f"V{r['version']}" if r.get("version") else "-"
        note = r['error'] if r['status'] in ('FAIL', 'SKIP') else ""
        print(f"  {r['status']:4}  {r['op']:6}  id={str(r['id']):<4} {vtag:<4} "
              f"{r['display']:<18} {str(r['size']):>7} bytes"
              + (f"   <- {note}" if note else ""))
    conn.close()

    # ---- summary table ----
    print("\n| Dashboard | Operation | Row ID | Version | HTML Size | version_status | Status |")
    print("|---|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r['display']} | {r['op']} | {r['id']} | {('V'+str(r['version'])) if r.get('version') else '-'} "
              f"| {r['size']} | {r.get('version_status') or '-'} | {r['status']} |")

    masters = [r for r in results if r["kind"] == "Master"]
    phs     = [r for r in results if r["kind"] == "PH"]
    ins     = sum(1 for r in results if r["op"] == "INSERT")
    upd     = sum(1 for r in results if r["op"] == "UPDATE")
    skip    = [r for r in results if r["status"] == "SKIP"]
    pas     = sum(1 for r in results if r["status"] == "PASS")
    fail    = [r for r in results if r["status"] == "FAIL"]
    print(f"\nTotal dashboards processed     : {len(results)}")
    print(f"Master dashboards processed    : {len(masters)}")
    print(f"Portfolio Holder dashboards    : {len(phs)}")
    print(f"INSERTS (new weekly versions)  : {ins}")
    print(f"UPDATES (same-week refresh)    : {upd}")
    print(f"SKIPPED (frozen / stale)       : {len(skip)}")
    print(f"PASS                           : {pas}")
    print(f"FAIL                           : {len(fail)}")
    if skip:
        print("Skipped dashboards:")
        for r in skip:
            print(f"  - {r['display']}: {r['error']}")
    if fail:
        print("Failed dashboards:")
        for r in fail:
            print(f"  - {r['display']}: {r['error']}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
