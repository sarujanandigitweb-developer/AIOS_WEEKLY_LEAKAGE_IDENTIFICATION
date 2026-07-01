#!/usr/bin/env python3
"""
WLSP — upload leakage_dashboard.html into tech_team_outputs.ph_task (row id=8).

CORRECT, byte-exact method: read the file and pass it to PostgreSQL as a BOUND
PARAMETER. The database driver transmits the exact bytes over the wire protocol —
the HTML is never rebuilt into SQL text, never split, never regenerated, never
retyped. One UPDATE. Only html_content + updated_at change.

Why the earlier chunk attempts corrupted the data:
    they reconstructed each chunk as literal SQL text that a human/LLM retyped,
    and a single dropped character broke the reconstruction. A bound parameter
    removes the transcription step entirely, so it cannot happen.

Run this from a host that can resolve the DB host `pg.severdigitweb.uk`
(the same place the other large ph_task rows, e.g. id 5 = 477 KB, were loaded).
It intentionally does NOT run from the sandboxed build box, where that host is
NXDOMAIN and no direct DB connection is possible.

Connection string resolution order:
    1. env var  WLSP_PG_DSN
    2. the postgres MCP server entry in ~/.claude.json  (postgresql://...)

Usage:
    python3 dashboard/upload_html_content.py
Exit code 0 = PASS (stored size == source size), non-zero = FAIL.
"""

import os, sys, json, glob

HERE       = os.path.dirname(os.path.abspath(__file__))
HTML_PATH  = os.path.join(HERE, "leakage_dashboard.html")
ROW_ID     = 8
PROJECT    = "wlsp"
TASK_ID    = "WLSP_Bietrick_Leakage_Dashboard-V1"


def find_dsn():
    dsn = os.environ.get("WLSP_PG_DSN")
    if dsn:
        return dsn
    # pull the postgres MCP connection string out of ~/.claude.json
    cfg_path = os.path.expanduser("~/.claude.json")
    try:
        cfg = json.load(open(cfg_path))
    except Exception:
        return None
    blob = json.dumps(cfg)
    import re
    m = re.search(r"postgresql://[^\s\"']+", blob)
    return m.group(0) if m else None


def main():
    if not os.path.isfile(HTML_PATH):
        sys.exit(f"FAIL: source file not found: {HTML_PATH}")

    # read the file EXACTLY — no transform, no split, no regeneration
    with open(HTML_PATH, "rb") as f:
        raw = f.read()
    html = raw.decode("utf-8")            # bound parameter (str -> UTF-8 on the wire)
    source_bytes = len(raw)
    print(f"source file : {HTML_PATH}")
    print(f"source bytes: {source_bytes}")

    dsn = find_dsn()
    if not dsn:
        sys.exit("FAIL: no DSN (set WLSP_PG_DSN or add the postgres MCP server to ~/.claude.json)")

    try:
        import psycopg2
    except ImportError:
        sys.exit("FAIL: psycopg2 not installed (pip install psycopg2-binary)")

    try:
        conn = psycopg2.connect(dsn)
    except Exception as e:
        sys.exit(f"FAIL: cannot connect to the database ({e}). "
                 f"Run this from a host that can resolve pg.severdigitweb.uk.")

    try:
        conn.autocommit = False
        cur = conn.cursor()

        # confirm the target row exists (do NOT create / delete)
        cur.execute("""SELECT 1 FROM tech_team_outputs.ph_task
                       WHERE id=%s AND project_code=%s AND task_id=%s""",
                    (ROW_ID, PROJECT, TASK_ID))
        if cur.fetchone() is None:
            conn.rollback()
            sys.exit(f"FAIL: row id={ROW_ID} ({PROJECT}/{TASK_ID}) not found — refusing to insert.")

        # single, byte-exact UPDATE via bound parameter — only html_content + updated_at
        cur.execute("""UPDATE tech_team_outputs.ph_task
                       SET html_content = %s, updated_at = now()
                       WHERE id = %s AND project_code = %s AND task_id = %s""",
                    (html, ROW_ID, PROJECT, TASK_ID))
        if cur.rowcount != 1:
            conn.rollback()
            sys.exit(f"FAIL: expected to update 1 row, updated {cur.rowcount} — rolled back.")
        conn.commit()

        # verify with octet_length (as required — no MD5/SHA)
        cur.execute("SELECT octet_length(html_content) FROM tech_team_outputs.ph_task WHERE id=%s",
                    (ROW_ID,))
        stored_bytes = cur.fetchone()[0]
        print(f"stored bytes: {stored_bytes}")
        cur.close()

        if stored_bytes == source_bytes:
            print(f"PASS: stored html_content ({stored_bytes} bytes) == source file ({source_bytes} bytes)")
            return 0
        else:
            sys.exit(f"FAIL: stored {stored_bytes} != source {source_bytes}")
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
