---
name: secdevai-dast
description: Dynamic Application Security Testing (DAST) using RapiDAST and OWASP ZAP. Use when the user wants to scan a running web app or API for security vulnerabilities, run a DAST scan, test a service endpoint, use RapiDAST or ZAP, or says "/secdevai dast" or "/secdevai-dast". Auto-detects Dockerfile/Compose for containerized targets, finds OpenAPI specs, guides the full scan workflow from target setup through SARIF result export, and — uniquely — traces each DAST finding back to the exact source file and line that is the root cause.
---

# SecDevAI DAST Command

## Description

Performs Dynamic Application Security Testing (DAST) against a running web application or API using [RapiDAST](https://github.com/RedHatProductSecurity/rapidast) (which wraps OWASP ZAP). All scans run via the `quay.io/redhatproductsecurity/rapidast:latest` container image — no local ZAP installation required.

The workflow auto-detects the target (Dockerfile/Compose or user-supplied URL), discovers OpenAPI specs, asks about authentication, runs a passive scan first, and optionally follows up with active scanning. After scanning, it traces each finding back to the exact source file and line that is the root cause — bridging the gap between a runtime HTTP observation and the vulnerable code that produced it.

## Usage

```
/secdevai dast                 # Auto-detect target and run DAST scan
/secdevai dast --url <URL>     # Scan a specific URL (legal warning applies)
/secdevai-dast                 # Alias
```

## Workflow

When this skill is invoked, follow these steps in order:

---

### Step 1: Detect Target

Search the current project directory for container definitions:

1. Look for (in priority order): `Containerfile`, `Dockerfile`, `docker-compose.yml`, `docker-compose.yaml`, `compose.yml`, `compose.yaml`
2. **If a Compose file is found**:
   - Detect the container runtime: check `podman` first, then `docker`. If neither is found, tell the user and stop.
   - Run `<runtime> compose up -d --build` (from the directory containing the compose file)
   - Determine the service URL: inspect the compose file for `ports:` mappings (e.g. `"8080:80"` → host port `8080`). Use the first mapped port and construct `http://localhost:<host-port>` as the target URL.
   - Note: the skill started this container and must clean it up in Step 7.
3. **If a Dockerfile/Containerfile is found (no compose)**:
   - Detect the container runtime (same as above).
   - Parse the file for `EXPOSE <port>` directives. Use the first exposed port (default to `8080` if none found).
   - Build the image: `<runtime> build -t secdevai-dast-target -f <file> .`
   - Start a container: `<runtime> run -d --name secdevai-dast-target -p <port>:<port> secdevai-dast-target`
   - Target URL: `http://localhost:<port>`
   - Note: the skill started this container and must clean it up in Step 7.
4. **If no container file is found AND the user did not supply `--url`**:
   - Display this warning and ask for the URL:

   ```
   ⚠️  LEGAL WARNING — READ BEFORE PROCEEDING ⚠️

   DAST scanning sends active HTTP requests to the target application.
   Scanning a system you do not own or have explicit written permission
   to test may violate the Computer Fraud and Abuse Act (CFAA), the
   Computer Misuse Act, GDPR, and other laws.

   You MUST confirm all of the following before proceeding:
   1. You own the target application OR have explicit written authorization to test it.
   2. The target is a TEST or STAGING environment — NOT production.
   3. You accept full legal responsibility for this scan.

   Please enter the target URL to scan (or type 'cancel' to abort):
   ```

   Wait for user input. If they type `cancel`, stop. Otherwise use their URL as the target.
5. **If `--url` was supplied**: use it directly. Still display a condensed reminder: "Confirm this is a system you own or have written permission to test."

---

### Step 2: Health Check

Before generating any config, verify the target is reachable:

```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 10 "<TARGET_URL>"
```

- If the HTTP status code is 000 (connection refused/timeout): tell the user the target is unreachable and stop.
- If status is 4xx or 5xx: warn the user ("Target returned `<code>` — scanning may have limited coverage") but continue.
- If status is 2xx or 3xx: proceed.

If a container was started in Step 1, wait up to 30 seconds for it to become ready (retry the health check every 5 seconds).

---

### Step 3: Discover OpenAPI Specification

First check the local project for spec files:

```
openapi.json, openapi.yaml, openapi.yml
swagger.json, swagger.yaml, swagger.yml
```

Search in these directories (relative to project root): `.`, `docs/`, `api/`, `static/`, `public/`, `src/`, `app/`

Then probe live endpoints on the running service:

```
<TARGET_URL>/openapi.json
<TARGET_URL>/openapi.yaml
<TARGET_URL>/docs/openapi.json
<TARGET_URL>/api/openapi.json
<TARGET_URL>/swagger.json
<TARGET_URL>/swagger.yaml
<TARGET_URL>/api-docs
<TARGET_URL>/v2/api-docs
<TARGET_URL>/v3/api-docs
```

Use `curl -s -o /dev/null -w "%{http_code}" --max-time 5 <url>` to check each endpoint. Use the first one that returns 200.

- **If an OpenAPI spec is found**: report it to the user (`Found OpenAPI spec at: <url>`) and proceed with `apiScan` mode.
- **If no spec is found**: tell the user and ask:

  ```
  No OpenAPI specification was found. Would you like to run a spider-based scan instead?
  - Spider scan: follows HTML links (faster, lower resource usage)
  - Ajax Spider: renders JavaScript pages using Firefox headless (slower, more thorough for SPAs)

  Enter your choice (spider/ajax/cancel) and optionally a max duration in minutes (default: 5):
  Example: "spider 10" or "ajax 5"
  ```

  Wait for user response. If `cancel`, stop.

---

### Step 4: Authentication

Ask the user whether the target requires authentication:

```
Does the target require authentication? Options:
1. none         - No authentication
2. http_basic   - HTTP Basic Auth (username + password)
3. http_header  - API key or Bearer token (header name + value)
4. cookie       - Cookie-based (name + value)
5. oauth2       - OAuth2 with refresh token (token endpoint + client ID + refresh token env var)

Enter choice (1-5, or press Enter for none):
```

Collect the required parameters for the chosen auth type. For `oauth2`, remind the user that the refresh token should be set as an environment variable (e.g. `RTOKEN`) and will be passed into the RapiDAST container.

---

### Step 5: Run Passive Scan

Call `scripts/rapidast-scan.sh` with the parameters gathered in the previous steps. The script generates a RapiDAST YAML config and runs the container.

```bash
bash scripts/rapidast-scan.sh \
  --target-url "<TARGET_URL>" \
  --app-name "<project-directory-name>" \
  --scan-type "<openapi|spider|ajax-spider>" \
  [--openapi-url "<OPENAPI_URL>"] \
  [--max-duration <MINUTES>] \
  [--auth-type "<AUTH_TYPE>"] \
  [--auth-params "<JSON_PARAMS>"] \
  --output-dir "./secdevai-results/dast"
```

Show the user the RapiDAST container output as it runs. Passive scanning typically takes 2–15 minutes depending on the application size.

Refer to `references/rapidast-config-templates.md` for the exact YAML that the script generates.

---

### Step 6: Present Passive Scan Results

After the scan completes:

1. Locate the SARIF output: `./secdevai-results/dast/zap/zap-report.sarif` (or search for `*.sarif` under the results directory)
2. Parse the SARIF file and present a summary:

```
## DAST Passive Scan Results

**Target**: <URL>
**Scan mode**: <OpenAPI / Spider / Ajax Spider>
**Duration**: <elapsed>

### Findings Summary
| Severity | Count |
|----------|-------|
| Critical | N     |
| High     | N     |
| Medium   | N     |
| Low      | N     |
| Info     | N     |

### Top Findings
[List up to 10 highest-severity findings with: rule ID, severity, description, affected URL]
```

3. Ask the user if they want active scanning:

```
Passive scan complete. Active scanning probes the application more aggressively
(sends attack payloads) and may take 30–120 minutes.

Run active scan? (yes/no):
```

If yes, re-run `scripts/rapidast-scan.sh` with `--active-scan` flag. Show results once complete.

---

### Step 7: Source Code Root Cause Analysis

This step bridges DAST findings to the codebase. For each finding in the SARIF, attempt to locate the exact source file and line that is responsible. This analysis is only meaningful when the project source code is available locally (which is the case when a Containerfile/Compose was used in Step 1, or when the user is running the scan against their own local project).

#### How to perform the trace

For each finding, the SARIF provides:
- `ruleId` — the ZAP rule that fired (e.g. `40018` = SQL Injection)
- `locations[].physicalLocation.artifactLocation.uri` — the affected URL
- `message.text` — what ZAP observed (e.g. manipulated boolean condition, injected parameter value)
- `webRequest.request.method` and query/body parameters ZAP used

Use this information to walk the source code:

1. **Extract the URL path** from the affected URI (strip the host/port). For example: `/api/pets/name/ZAP%27%20AND%20%271%27%3D%271%27%20--%20` → path template `/api/pets/name/<param>`
2. **Search for the route handler**: Look for route/endpoint definitions matching that path pattern in the source tree (e.g. `@app.route`, `@router.get`, `Blueprint.route`, Express `router.get`, Spring `@GetMapping`, etc.)
3. **Identify the vulnerable parameter**: The SARIF message or request context names the parameter ZAP injected. Locate where that parameter is read in the handler.
4. **Trace data flow to the sink**: Follow the parameter from the handler into any downstream call that could be a vulnerability sink — for SQL Injection: raw string query construction; for XSS: unescaped template rendering; for Path Traversal: file path construction; for SSRF: outbound HTTP calls; for Command Injection: shell execution.
5. **Pinpoint the root cause line**: The root cause is the line where untrusted input reaches a dangerous sink without sanitization or parameterization.

#### Output format per finding

For each finding that can be traced, produce:

```
### [Severity] Rule <ID> — <Rule Name>
**DAST observation**: <what ZAP detected, from SARIF message>
**Affected URL**: <URL from SARIF>

**Root cause**:
- File: `<relative/path/to/file.py>` line <N>
- Code: `<the vulnerable line>`
- Why: <one sentence explaining the flaw — e.g. "user input concatenated directly into SQL query without parameterization">

**Data flow**:
`<route handler>` (file, line N) → `<intermediate function>` (file, line N) → **vulnerable sink** (file, line N)

**Fix**:
<concrete code change — before/after snippet>
```

If a finding cannot be traced to source (e.g. a missing HTTP header, or the source is not available), note: "Source not applicable — this is a configuration/response-level finding."

#### Save the correlation report

Write the full source correlation as `source-correlation.md` into the same directory as the SARIF file:

```python
from pathlib import Path
import json, datetime

sarif_path = next(Path("./secdevai-results/dast").rglob("rapidast-scan-results.sarif"), None)
correlation_path = sarif_path.parent / "source-correlation.md"

# Build the report content from the trace analysis above
report_lines = [
    f"# DAST Source Correlation Report",
    f"",
    f"**Target**: {TARGET_URL}",
    f"**SARIF**: {sarif_path.name}",
    f"**Generated**: {datetime.datetime.now().isoformat()}",
    f"",
    f"This report maps each DAST finding to its root cause in the source code.",
    f"",
    # ... one section per finding, using the format above
]

correlation_path.write_text("\n".join(report_lines))
print(f"Source correlation saved to: {correlation_path}")
```

Also annotate the findings in the structured data before passing to `secdevai-export`, adding a `source_location` field:

```python
# Enrich each finding with source location before export
for finding in data["findings"]:
    finding["source_location"] = {
        "file": "src/backend/blueprints/pets.py",
        "line": 108,
        "code": "item = list(db.select_all(TABLE_NAME, where=f\"name='{pet_name}' COLLATE NOCASE\"))",
        "root_cause": "User-supplied path parameter interpolated directly into SQL WHERE clause"
    }
```

---

### Step 8: Export Results

After scanning is complete, export the findings using the `secdevai-export` skill:

```python
import importlib.util
from pathlib import Path
import json, datetime

# Load the SARIF file produced by RapiDAST
sarif_path = next(Path("./secdevai-results/dast").rglob("*.sarif"), None)

# Load the exporter
script_path = Path("secdevai-export/scripts/results_exporter.py")
spec = importlib.util.spec_from_file_location("results_exporter", script_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Build the data structure from SARIF findings
data = {
    "metadata": {
        "tool": "rapidast",
        "version": "latest",
        "timestamp": datetime.datetime.now().isoformat(),
        "analyzer": "RapiDAST / OWASP ZAP DAST",
        "target": TARGET_URL,
    },
    "summary": { ... },   # counts from SARIF results
    "findings": [ ... ],  # findings from SARIF results array
}

markdown_path, sarif_path = mod.export_results(data, command_type="dast")
```

Tell the user where the reports were saved.

### Step 9: Cleanup

If the skill started a container in Step 1, stop and remove it:

```bash
# Compose-managed container
<runtime> compose down

# Standalone container
<runtime> stop secdevai-dast-target
<runtime> rm secdevai-dast-target
```

---

## Notes

- **Passive scan first**: Passive scanning observes traffic without sending attack payloads — safe for staging environments. Always run it before active scanning.
- **Active scan warning**: Active scanning sends attack payloads. Never run against production. It can trigger WAF blocks, account lockouts, or application errors.
- **Results directory**: All scan artifacts go to `./secdevai-results/dast/` by default. Override the base with `export SECDEVAI_RESULTS_DIR=/your/path` — the `/dast` sub-path is always appended. This env var is shared with all other secdevai commands (`review`, `fix`, `tool`) so setting it once configures the base for everything.
- **RapiDAST container**: Scans run via `quay.io/redhatproductsecurity/rapidast:latest`. Ensure the container runtime can pull from `quay.io`.
- **Network access**: When scanning a locally started container, RapiDAST runs inside its own container. On Linux, use `--network host` or reference the host via the gateway IP. On macOS with Docker Desktop, use `host.docker.internal` instead of `localhost` in the target URL passed to RapiDAST.
- **macOS host resolution**: If the target is `http://localhost:<port>`, automatically substitute `host.docker.internal` as the hostname when running the RapiDAST container on macOS (detected via `uname -s`).
- **Source correlation**: Step 7 traces each finding to source code. It works best when the project source is available locally. For findings that are purely response-level (missing headers, server version leaks), source correlation is noted as "not applicable" — these are fixed in server/framework configuration, not application code.
- **Sink-to-source mapping by rule**: Key ZAP rules and their typical source sinks — `40018` SQL Injection → raw string query construction; `40014/40016` XSS → unescaped template output; `6` Path Traversal → file path joins with user input; `20019` SSRF → outbound HTTP calls with user-supplied URL; `90020` Command Injection → subprocess/shell calls; `10098` CORS → CORS middleware wildcard config.
