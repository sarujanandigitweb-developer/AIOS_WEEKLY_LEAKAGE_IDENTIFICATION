# Prompt for the backup developer's machine - WLSP "add the automatic run schedule ONLY"

Open Claude Code INSIDE the cloned `AIOS_Weekly_Leakage_Identification` folder and paste the box below.
It installs only the WLSP weekly cron schedule. It does NOT change any code.

---

```text
Work ONLY inside this folder (the AIOS Weekly Leakage Identification project, code WLSP, my current directory).
Do not read, scan or touch any other project or folder on this machine.

TASK: add the automatic weekly run schedule (cron) for the WLSP leakage dashboards. Nothing else.

HARD RULES
1. DO NOT modify, create, rename or delete any file in this project (code, scripts, dashboards, docs, .env). The ONLY thing you may change is my user crontab.
2. First back up my crontab: `crontab -l > ~/crontab_backup_$(date +%Y%m%d_%H%M%S).txt` (if none exists, say so).
3. Never print or copy passwords, tokens, credentials or .env values. Only check that files exist.
4. Do NOT run dashboard/refresh_dashboard.py or dashboard/refresh_ph_dashboards.py. They call the Claude CLI, rewrite the HTML files and INSERT/UPDATE rows in the production database (tech_team_outputs.ph_task). Do not run `claude -p` either. Only read-only checks (`test -f`, `test -x`, `python3 -m py_compile`, `command -v`, `ls`).
5. Idempotent: put what you add between `# >>> WLSP-SCHEDULE BEGIN` and `# <<< WLSP-SCHEDULE END`; replace only that block if it exists; never duplicate or remove my other cron entries. Put the block at the END of the crontab.
6. Show me the exact block and wait for my "yes" before installing.

STEP 1 - Read-only checks (report as a small table)
- Let P = the absolute path of this folder (`pwd`).
- Exist: P/dashboard/refresh_dashboard.py, P/dashboard/refresh_ph_dashboards.py, P/dashboard/dashboard_refresh_prompt.md, P/dashboard/leakage_dashboard.html. `python3 -m py_compile` passes on both .py files (note: this may write __pycache__; if you want zero writes use `python3 -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" FILE` instead).
- The scripts use their own folder (`dashboard/`) for all paths, so no other hardcoded project folder is needed. The cron line does `cd P`. Confirm nothing else is required outside this folder; if any script path points outside it, tell me instead of reading it.
- P/logs/ exists. Cron's `>>` redirect fails if it does not (logs/ is git-ignored, so a fresh clone will NOT have it). If missing, tell me and ask me to create it; do not create it yourself.
- Binaries: `command -v python3` (the original cron uses /usr/bin/python3), `command -v claude` (record the absolute path; this is CLAUDE_BIN), `claude --version`. `python3 -c "import psycopg2"` must work (pip package psycopg2-binary). If any is missing, tell me.
- Claude login: check that ~/.claude/.credentials.json exists (existence only, never show it). The refresh uses the hosted claude.ai Postgres MCP connector, so this machine's Claude CLI must be logged in to the claude.ai account that has the Postgres connector for the order_management_copy database. You cannot verify the connector without running Claude, so just tell me to confirm it.
- DB env: the uploader reads PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD from the environment. The code also has built-in default values (a known security issue, do not print them). Tell me whether any of those variable NAMES are set in the cron environment (names only). Cron does not read ~/.bashrc or any .env; there is no .env loader in these scripts.
- `systemctl is-active cron`, and `timedatectl | grep "Time zone"`. The schedule is Monday 08:45 in Asia/Colombo (+05:30). If this machine is in another timezone, add `CRON_TZ=Asia/Colombo` as the first line of the block (warn me it also affects any entry after it, which is why the block must be last).

STEP 2 - The block to install (replace P with the real absolute path, CLAUDE_BIN_PATH with the output of `command -v claude`, CLAUDE_DIR with its folder)
  # >>> WLSP-SCHEDULE BEGIN
  # WLSP Weekly Leakage Dashboard Refresh - Mondays 08:45 (refresh, then publish to ph_task only if refresh succeeded)
  45 8 * * 1 cd P && PATH=CLAUDE_DIR:/usr/local/bin:/usr/bin:/bin CLAUDE_BIN=CLAUDE_BIN_PATH /usr/bin/python3 dashboard/refresh_dashboard.py >> logs/wlsp_refresh.log 2>&1 && PATH=CLAUDE_DIR:/usr/local/bin:/usr/bin:/bin CLAUDE_BIN=CLAUDE_BIN_PATH /usr/bin/python3 dashboard/refresh_ph_dashboards.py >> logs/wlsp_refresh.log 2>&1
  # <<< WLSP-SCHEDULE END

Why it differs from the developer's crontab: the developer's machine set `CLAUDE_BIN=/home/led-247/.local/bin/claude` as a global crontab line. That path no longer exists, so the runs on 2026-09-21 and 2026-10-05 failed immediately ("Claude CLI not found"). Here, CLAUDE_BIN must be the real path from `command -v claude` on THIS machine. I set PATH and CLAUDE_BIN inline on the command so they do not leak into my other cron jobs. If /usr/bin/python3 does not exist here, use the output of `command -v python3`.

Do NOT schedule anything else. Specifically: do not copy any other entries from the developer's crontab (other projects), and do not schedule the legacy helper scripts (dashboard/_wlsp_*.py, _wlsp_inject.js). The old docstrings in the scripts ("every 4 hours", "0 6 * * 1") are wrong; the real schedule is Monday 08:45.

STEP 3 - After my "yes", install (write the block file in /tmp, not in this project):
  (crontab -l 2>/dev/null | sed '/# >>> WLSP-SCHEDULE BEGIN/,/# <<< WLSP-SCHEDULE END/d'; cat /tmp/wlsp_block.txt) | crontab -

STEP 4 - Verify and report
- `crontab -l` shows the block exactly once, other entries intact.
- Tell me the next run time in plain words (next Monday 08:45 in the schedule's timezone), and the commands to watch it: `tail -f P/logs/wlsp_refresh.log` and `tail -f P/dashboard/refresh.log` (the refresh script also logs START / VALIDATION / RESULT lines there). A normal run takes about 5 to 20 minutes (hard cap 90 minutes).
- List anything still needed from a human: the Claude CLI login with the claude.ai Postgres connector authorised, database access/credentials (PG* variables, set in the crontab environment or fixed in code by the owner), network access to the database host, the git-ignored logs/ folder, and an always-on machine (cron only runs while the machine is on).
- Warn me: until a run logs "RESULT: PASS" in P/dashboard/refresh.log and the uploader prints PASS rows, the schedule is not proven. Connector renumbering ("blocked at the permission layer") and "unchanged after run" are known failure modes.
For how the job works and troubleshooting, point me to handover/aios_weekly_leakage_identification_handover.md (section 8, 10 and 12).
```

---

Notes
- Original schedule: developer's user crontab, `45 8 * * 1` (Monday 08:45, system timezone Asia/Colombo). Refresh runs first; the publish step runs only if it succeeds (`&&`).
- Last good run: 2026-09-14. Runs on 2026-09-21 and 2026-10-05 failed only because of the stale CLAUDE_BIN path.
- `dashboard/refresh_ph_dashboards.py` has default DB credentials hardcoded (git-committed). The owner should move them to environment variables and rotate the password.
- Credentials are not in git; get them from the team lead or the jobs will run and fail.
