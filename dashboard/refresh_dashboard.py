#!/usr/bin/env python3
"""
WLSP Dashboard Refresh — ORCHESTRATOR (Claude-headless approach)
AIOS Weekly Leakage Identification · UK Amazon FBM · LEDSone + DCVoltage

Runs every 4 hours (cron). Each run:
  1. Launches Claude CLI non-interactively (`claude -p`) with dashboard_refresh_prompt.md.
  2. Claude queries live PostgreSQL via the MCP tool mcp__claude_ai_postgres__execute_sql ONCE,
     runs the approved WLSP L1-L5 calculations, builds dashboardData, and replaces ONLY the
     content between <!-- WLSP_DATA_START --> and <!-- WLSP_DATA_END --> in leakage_dashboard.html.
  3. This script WAITS for completion, then VALIDATES the master file was updated correctly.
  4. It then REUSES that single dashboardData to regenerate one standalone dashboard per
     Portfolio Holder under portfolio_holders/<name>_leakage.html — by copying the master and
     replacing ONLY the marker block with the PH-filtered data (no extra SQL, no business logic,
     no rendering code; everything outside the markers stays byte-identical to the master).
  5. Validates every PH dashboard (shell byte-identical + isolated to its PH) and appends to refresh.log.

PostgreSQL touches: exactly ONE query set, run by Claude in step 2. Python never touches the DB;
the per-PH dashboards in step 4 are pure data-filtering of the already-generated dashboardData.
Exit code 0 on success, non-zero on failure.

Prereqs (proven working in this environment):
  - `claude` CLI on PATH (or set CLAUDE_BIN).
  - A valid claude.ai credential (~/.claude/.credentials.json) so the claude.ai postgres MCP loads.
"""

import os, re, sys, json, hashlib, subprocess, datetime, time, glob

HERE        = os.path.dirname(os.path.abspath(__file__))
HTML        = os.path.join(HERE, "leakage_dashboard.html")
PH_DIR      = os.path.join(HERE, "portfolio_holders")   # per-Portfolio-Holder dashboards
ACCOUNTS    = ["LEDSone UK", "DCVoltage UK"]             # account filter must keep both
PROMPT      = os.path.join(HERE, "dashboard_refresh_prompt.md")
LOG         = os.path.join(HERE, "refresh.log")
CLAUDE_BIN  = os.environ.get("CLAUDE_BIN", "claude")
TIMEOUT_SEC = int(os.environ.get("WLSP_REFRESH_TIMEOUT", "5400"))     # 90 min hard cap
# NOTE: embedding ALL flagged rows (~536 detail objects, ~108 KB JSON) means the headless
# Claude hand-assembles a large block, which previously overran the old 1500 s (25 min) cap.
# Raised to 5400 s (90 min) — still well inside the 4-hour cron interval. Override per-run with
# WLSP_REFRESH_TIMEOUT. If runs still time out, switch to the single-consolidated-query design.
START, END  = "<!-- WLSP_DATA_START -->", "<!-- WLSP_DATA_END -->"
ALLOWED     = "mcp__claude_ai_postgres__execute_sql Read Edit Write Bash"
# Bash is REQUIRED: the embedded data block is ~108 KB, so the headless run generates it with
# one SQL query (result overflows to a file) and splices it in with a short Python script — that
# needs Bash. Without it every Bash call returns "This command requires approval" and, being
# non-interactive, is denied, so the file is never written (the prior timeout/"unchanged" fails).

# tables that must NEVER be referenced by the generated data block
FORBIDDEN = ["development.leakage_detection", "development.leakage_classification",
             "ph_action_board", "ph_daily_actions"]


def log(msg):
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def extract_block(text):
    m = re.search(re.escape(START) + r"(.*?)" + re.escape(END), text, re.DOTALL)
    return m.group(1) if m else None


def extract_data_json(block):
    """Pull the dashboardData object literal out of the marker block and JSON-parse it."""
    m = re.search(r"const\s+dashboardData\s*=\s*(\{.*\})\s*;", block, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def fail(msg):
    log("RESULT: FAIL — " + msg)
    sys.exit(1)


def ph_filename(ph):
    """abinayaa_leakage.html, tharsiga_nelli_leakage.html, ..."""
    return re.sub(r"[^a-z0-9]+", "_", ph.lower()).strip("_") + "_leakage.html"


def build_ph_data(data, ph):
    """Filter the master dashboardData to a single Portfolio Holder — NO database access.
       Returns the same schema (summary, account_summary, ph_summary, verification_summary,
       l1-l5) so the unchanged dashboard JS renders identically with only this PH's records."""
    l1 = [r for r in data["l1"] if r.get("ph") == ph]
    l2 = [r for r in data["l2"] if r.get("ph") == ph]
    l3 = [r for r in data["l3"] if r.get("ph") == ph]
    l4 = [r for r in data["l4"] if r.get("ph") == ph]
    l5 = [r for r in data["l5"] if r.get("ph") == ph]
    s = dict(data["summary"]); s["ph_count"] = 1
    s["counts"] = {"l1": len({r.get("asin") for r in l1}), "l2": len(l2), "l3": len(l3), "l4": len(l4),
                   "l5": len({r["ph"] for r in l5 if r.get("account") == "ALL" and r.get("declining")})}
    s["displayed"] = {"l1": len(l1), "l2": len(l2), "l3": len(l3), "l4": len(l4),
                      "l5": len({r["ph"] for r in l5 if r.get("account") == "ALL"})}
    asum = []
    for a in ACCOUNTS:  # keep BOTH accounts so the account filter still offers each one
        a1 = len({r.get("asin") for r in l1 if r.get("account") == a})
        a2 = len([r for r in l2 if r.get("account") == a])
        a3 = len([r for r in l3 if r.get("account") == a])
        a4 = len([r for r in l4 if r.get("account") == a])
        asum.append({"account": a, "l1": a1, "l2": a2, "l3": a3, "l4": a4, "total": a1 + a2 + a3 + a4})
    asum.sort(key=lambda x: (-x["total"], x["account"]))
    return {"summary": s, "l1": l1, "l2": l2, "l3": l3, "l4": l4, "l5": l5,
            "account_summary": asum,
            "ph_summary": [p for p in data["ph_summary"] if p.get("ph") == ph],
            "verification_summary": data.get("verification_summary", [])}


def generate_ph_dashboards(master_text, master_data):
    """Reuse the SINGLE already-generated dashboardData (master_data) to write one standalone
       dashboard per Portfolio Holder. Only the bytes between the markers change; the rest of the
       file is copied byte-for-byte from the freshly-refreshed master (so HTML/CSS/JS/layout/
       rendering are identical). No SQL, no business logic, no rendering code is duplicated here.
       Returns (list_of_(ph,filename), master_shell, elapsed_seconds)."""
    t0 = time.time()
    m = re.search(re.escape(START) + r"(.*?)" + re.escape(END), master_text, re.DOTALL)
    prefix, suffix = master_text[:m.start()], master_text[m.end():]
    master_shell = prefix + suffix      # everything outside the data block — must stay identical
    phs = sorted({r.get("ph") for k in ("l1", "l2", "l3", "l4", "l5")
                  for r in master_data.get(k, []) if r.get("ph") and r.get("ph") != "UNATTRIBUTED"})
    os.makedirs(PH_DIR, exist_ok=True)
    for old in glob.glob(os.path.join(PH_DIR, "*_leakage.html")):   # drop stale PHs
        os.remove(old)
    out = []
    for ph in phs:
        pretty = json.dumps(build_ph_data(master_data, ph), indent=2, ensure_ascii=False)
        block = (START + "\n<script>\nconst dashboardData = " + pretty +
                 ";\nwindow.dashboardData = dashboardData;\n</script>\n" + END)
        fn = ph_filename(ph)
        with open(os.path.join(PH_DIR, fn), "w", encoding="utf-8") as f:
            f.write(prefix + block + suffix)
        out.append((ph, fn))
    return out, master_shell, time.time() - t0


def main():
    t_start = time.time()
    for p in (HTML, PROMPT):
        if not os.path.isfile(p):
            fail(f"missing required file: {p}")

    before_hash = sha(HTML)
    before_block = extract_block(open(HTML, encoding="utf-8").read())
    if before_block is None:
        fail("markers not found in leakage_dashboard.html before run")

    log("START refresh — launching Claude CLI headless")
    cmd = [CLAUDE_BIN, "-p", open(PROMPT, encoding="utf-8").read(),
           "--allowedTools", *ALLOWED.split(), "--add-dir", HERE]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SEC, cwd=HERE)
    except subprocess.TimeoutExpired:
        fail(f"Claude CLI timed out after {TIMEOUT_SEC}s")
    except FileNotFoundError:
        fail(f"Claude CLI not found (CLAUDE_BIN={CLAUDE_BIN})")

    log(f"Claude exit={proc.returncode}; stdout tail: {proc.stdout.strip()[-300:]!r}")
    if proc.returncode != 0:
        fail(f"Claude CLI non-zero exit ({proc.returncode}); stderr: {proc.stderr.strip()[-300:]}")

    # ---- VALIDATION (this script's job: confirm the file was updated correctly) ----
    text = open(HTML, encoding="utf-8").read()

    # 1. file actually changed
    if sha(HTML) == before_hash:
        fail("leakage_dashboard.html unchanged after run")

    # 2. markers still present, single pair
    if text.count(START) != 1 or text.count(END) != 1:
        fail("marker count not exactly 1 each after run")

    # 3. data block parses as JSON with required keys
    block = extract_block(text)
    data = extract_data_json(block)
    if data is None:
        fail("dashboardData JSON between markers did not parse")
    required = ["summary", "l1", "l2", "l3", "l4", "l5",
                "account_summary", "ph_summary", "verification_summary"]
    missing = [k for k in required if k not in data]
    if missing:
        fail(f"dashboardData missing keys: {missing}")

    # 4. counts present and displayed lengths consistent
    c = data["summary"].get("counts", {})
    if not all(k in c for k in ("l1", "l2", "l3", "l4", "l5")):
        fail("summary.counts incomplete")
    # L2 is ASIN-grain, so its row count must not exceed counts.l2. L1 detail is ASIN+SKU+PH
    # grain while counts.l1 is COUNT(DISTINCT asin), so len(l1) may legitimately exceed counts.l1
    # (one ASIN with two SKUs) — L1 is validated by distinct-ASIN in guard #7, not by row length.
    if len(data["l2"]) > c["l2"]:
        fail("embedded L2 exceeds true count (cap broken)")

    # 5. no forbidden tables leaked into the DATA sections. verification_summary
    #    intentionally documents the EXCLUDED tables, so it is scanned out here —
    #    same data_only slice the D04 guards use in #7 (kept in sync below).
    data_only = json.dumps({k: data.get(k) for k in
                            ("l1", "l2", "l3", "l4", "l5", "account_summary", "ph_summary")}).lower()
    leaked = [t for t in FORBIDDEN if t in data_only]
    if leaked:
        fail(f"forbidden tables referenced in data block: {leaked}")

    # 6. no external data.js dependency reintroduced
    if 'src="data.js"' in text:
        fail("data.js dependency present — file is no longer self-contained")

    # 7. D04 REGRESSION GUARDS — Amazon-only marketplace + UNATTRIBUTED exclusion + L1 grain.
    #    Reuses data_only from #5 (DATA sections only; verification_summary excluded).
    for token in ("ebay", "shopify", "so_926407"):
        if token in data_only:
            fail(f"D04 regression: marketplace contamination — '{token}' found in dashboard data")
    if any((p.get("ph") == "UNATTRIBUTED") for p in data.get("ph_summary", [])):
        fail("D04 regression: UNATTRIBUTED present in ph_summary (must be assigned PHs only)")
    # counts.l1 must be distinct ASINs, not the L1 detail row count (ASIN+SKU+PH grain)
    l1_distinct_asin = len({(r.get("asin") or "") for r in data.get("l1", [])})
    if data.get("l1") and len(data["l1"]) < c["l1"]:
        # l1 detail is capped (top-N); cannot self-check distinct-ASIN beyond the cap — log only
        log(f"NOTE: L1 detail is capped ({len(data['l1'])}/{c['l1']}); distinct-ASIN guard limited to embedded rows")
    elif l1_distinct_asin and l1_distinct_asin != c["l1"]:
        fail(f"D04 regression: counts.l1={c['l1']} != distinct ASIN in L1 detail ({l1_distinct_asin})")

    log(f"VALIDATION OK (master) — counts L1={c['l1']} L2={c['l2']} L3={c['l3']} L4={c['l4']} L5={c['l5']}; "
        f"accounts={len(data['account_summary'])}; ph_rows={len(data['ph_summary'])}; "
        f"generated_at={data['summary'].get('generated_at')}")

    # ---- STEP 2: regenerate every Portfolio Holder dashboard from the SAME dashboardData ----
    #      (reuse master_data; NO extra PostgreSQL queries; only the marker block changes per file)
    ph_list, master_shell, ph_secs = generate_ph_dashboards(text, data)
    if not ph_list:
        fail("no Portfolio Holders found in dashboardData — 0 PH dashboards generated")
    bad_shell, bad_iso = [], []
    for ph, fn in ph_list:
        pt = open(os.path.join(PH_DIR, fn), encoding="utf-8").read()
        if pt[:pt.index(START)] + pt[pt.index(END) + len(END):] != master_shell:
            bad_shell.append(fn)                                   # HTML/CSS/JS drift outside the data block
        pd = extract_data_json(extract_block(pt))
        isolated = (pd is not None
                    and len(pd.get("ph_summary", [])) == 1 and pd["ph_summary"][0].get("ph") == ph
                    and all(r.get("ph") == ph for k in ("l1", "l2", "l3", "l4", "l5") for r in pd.get(k, [])))
        if not isolated:
            bad_iso.append(fn)
    if bad_shell:
        fail(f"PH dashboards differ from master outside the data block: {bad_shell[:5]} "
             f"(+{max(0, len(bad_shell) - 5)} more)")
    if bad_iso:
        fail(f"PH dashboards not isolated to their Portfolio Holder: {bad_iso[:5]}")
    log(f"PH dashboards OK — {len(ph_list)} regenerated in {ph_secs:.2f}s into "
        f"{os.path.relpath(PH_DIR, HERE)}/ (one dashboardData reused for all; shell byte-identical; each PH-isolated)")
    log(f"RESULT: PASS — leakage_dashboard.html + {len(ph_list)} PH dashboards refreshed "
        f"in {time.time() - t_start:.1f}s total")


if __name__ == "__main__":
    main()
