#!/usr/bin/env python3
"""
WLSP Dashboard Refresh — ORCHESTRATOR (Claude-headless approach)
AIOS Weekly Leakage Identification · UK Amazon FBM · LEDSone + DCVoltage

Runs every 4 hours (cron). Each run:
  1. Launches Claude CLI non-interactively (`claude -p`) with dashboard_refresh_prompt.md.
  2. Claude queries live PostgreSQL via the MCP tool mcp__claude_ai_postgres__execute_sql,
     runs the approved WLSP L1-L5 calculations, builds dashboardData, and replaces ONLY the
     content between <!-- WLSP_DATA_START --> and <!-- WLSP_DATA_END --> in leakage_dashboard.html.
  3. This script WAITS for completion, then VALIDATES the file was updated correctly.
  4. Appends a line to refresh.log.

This script itself NEVER touches PostgreSQL and never edits the HTML — Claude does the work;
this is purely launch + wait + validate + log. Exit code 0 on success, non-zero on failure.

Prereqs (proven working in this environment):
  - `claude` CLI on PATH (or set CLAUDE_BIN).
  - A valid claude.ai credential (~/.claude/.credentials.json) so the claude.ai postgres MCP loads.
"""

import os, re, sys, json, hashlib, subprocess, datetime

HERE        = os.path.dirname(os.path.abspath(__file__))
HTML        = os.path.join(HERE, "leakage_dashboard.html")
PROMPT      = os.path.join(HERE, "dashboard_refresh_prompt.md")
LOG         = os.path.join(HERE, "refresh.log")
CLAUDE_BIN  = os.environ.get("CLAUDE_BIN", "claude")
TIMEOUT_SEC = int(os.environ.get("WLSP_REFRESH_TIMEOUT", "900"))     # 15 min hard cap
START, END  = "<!-- WLSP_DATA_START -->", "<!-- WLSP_DATA_END -->"
ALLOWED     = "mcp__claude_ai_postgres__execute_sql Read Edit Write"

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


def main():
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
    if len(data["l1"]) > c["l1"] or len(data["l2"]) > c["l2"]:
        fail("embedded L1/L2 exceed true counts (cap broken)")

    # 5. no forbidden tables leaked into the data block
    low = block.lower()
    leaked = [t for t in FORBIDDEN if t in low]
    if leaked:
        fail(f"forbidden tables referenced in data block: {leaked}")

    # 6. no external data.js dependency reintroduced
    if 'src="data.js"' in text:
        fail("data.js dependency present — file is no longer self-contained")

    log(f"VALIDATION OK — counts L1={c['l1']} L2={c['l2']} L3={c['l3']} L4={c['l4']} L5={c['l5']}; "
        f"accounts={len(data['account_summary'])}; ph_rows={len(data['ph_summary'])}; "
        f"generated_at={data['summary'].get('generated_at')}")
    log("RESULT: PASS — leakage_dashboard.html refreshed")


if __name__ == "__main__":
    main()
