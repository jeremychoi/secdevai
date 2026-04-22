---
name: secdevai-review
description: Perform AI-powered security code review using OWASP Top 10 and WSTG patterns. Use when reviewing source code, specific files, git commits, or entire codebases for security vulnerabilities. Supports multi-language analysis and severity classification.
---

# SecDevAI Review Command

## Description
Perform AI-powered security code review. Invoked via `/secdevai review` or the `/secdevai-review` alias.

## Usage
```
/secdevai review               # Review selected code (if selected) or full codebase scan
/secdevai review @ file        # Review specific file
/secdevai review last-commit   # Review last commit
/secdevai review last-commit --number N  # Review last N commits
/secdevai-review               # Alias: same as /secdevai review
/secdevai-review @ file        # Alias: same as /secdevai review @ file
```

## Expected Response

When this skill is invoked, follow these steps in order:

### Step 1: Detect Scope

Determine what to review (in priority order):

1. If `review last-commit --number N` specified: Review last N commits (requires git)
2. If `review last-commit` specified: Review last commit (requires git)
3. If `review @ file` is specified: Review the specified file
4. If text is selected in UI: Automatically review only the selected code
5. Otherwise (default): Scan entire codebase

### Step 2: Filter with `.secdevaiignore`

Read `secdevai-review/context/.secdevaiignore` and apply its patterns to the files identified in Step 1. In addition to the explicit patterns in that file, **always skip**:

- **Binary and media files** — images, fonts, audio, video, compiled artifacts (`.class`, `.pyc`, `.o`), archives, and other non-human-readable content
- **SecDevAI own files** — the skill's own configuration and context files, including `.secdevaiignore`, `secdevai-*/` skill directories, `secdevai-review/context/`, and `secdevai-results/` output

> **Note:** Documentation files (markdown, RST, plaintext, etc.) are **not** skipped. They can contain hardcoded secrets (passwords, API keys, tokens), leaked infrastructure details, or AI agent instructions (e.g. `SKILL.md`, `AGENTS.md`) that may introduce prompt injection risks.

Apply filtering according to scope:

- **Codebase scan**: Exclude matching files from the scan.
- **Commit review** (`last-commit` / `last-commit --number N`): Check changed files in each commit against the rules above and remove matches from the review set.
- **File review** (`@ file`): If the specified file would be excluded, warn the user but proceed — they explicitly chose it.
- **Selected text**: No filtering — the user explicitly selected code to review.

**If ALL files are excluded after filtering**, stop and report:

```
## Security Review: Skipped

**Scope**: [commit hash / file / codebase]
**Reason**: All files match .secdevaiignore exclusion patterns or are binary files. No security-relevant content to review.

Tip: To review an excluded file, remove its pattern from .secdevaiignore.
```

**If SOME files are excluded**, proceed with the remaining files and list the skipped files at the end of the review output.

### Step 3: Load Security Context

- **Always read**: `secdevai-review/context/security-review.context` for OWASP Top 10 patterns

- **Auto-detect WSTG context** (additionally read `secdevai-review/context/wstg-testing.context` if ANY condition applies):
  - Source code is for a web application, web service, or web site
  - User explicitly mentions: "WSTG", "Web Security Testing Guide", or category numbers (4.1-4.12)

- **Auto-detect Golang context** (additionally read `secdevai-review/context/golang-security.context` if ANY condition applies):
  - Source code or files under review include Go (e.g. `.go` files, `go.mod` present)

- **Auto-detect OCI/container context** (additionally read `secdevai-oci-image-security/references/` files if ANY condition applies):
  - `Dockerfile` or `Containerfile` is present in the repo
  - Kubernetes manifests (YAML files with `apiVersion`/`kind` fields) are detected
  - OpenShift deployment configs or templates are present
  - `docker-compose.yml` or `compose.yaml` exists

- **Note**: WSTG patterns enhance web application security analysis; golang-security.context provides Go-specific vulnerability and weakness patterns; OCI image security references provide container supply chain, configuration, hardening, and EOL detection patterns

### Step 4: Optional Tool Integration

- If `tool` specified: Run the tool via `secdevai-tool` (see `secdevai-tool/scripts/container-run.sh`)
- Parse tool output and synthesize with AI analysis
- If tool unavailable: Fall back to AI-only analysis

### Step 5: Perform Analysis

- Scan code for security patterns from loaded context
- Classify findings by severity (Critical/High/Medium/Low/Info)
- Reference OWASP categories
- Provide context-aware explanations

### Step 6: Present Findings

```
## 🔒 **Security Review Results**

### 🔴 **Critical Findings** (2)
- [Finding 1 with code reference]
- [Finding 2 with code reference]

### 🟠 **High Severity** (3)
- [Finding details]

### 🟡 **Medium Severity** (5)
- [Finding details]

**Total**: 10 findings across [file/codebase]
```

### Step 7: Save Results

After presenting findings, collect all findings into structured JSON and export:

```python
import importlib.util
from pathlib import Path

# Load the exporter from secdevai-export skill scripts
script_path = Path("secdevai-export/scripts/results_exporter.py")
spec = importlib.util.spec_from_file_location("results_exporter", script_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Collect findings into data structure
data = {
    "metadata": {
        "tool": "secdevai-ai-analysis",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "target_file": "[file path or 'codebase']",
        "analyzer": "AI Security Review",
    },
    "summary": {
        "total_findings": [count],
        "critical": [count],
        "high": [count],
        "medium": [count],
        "low": [count],
        "info": [count],
    },
    "findings": [list of finding objects],
}

# Export to markdown and SARIF
markdown_path, sarif_path = mod.export_results(data, command_type="review")
```

- The exporter will prompt the user to confirm the result directory (default: `secdevai-results`)
- Results are saved with timestamp: `secdevai-review-YYYYMMDD_HHMMSS.md` and `.sarif`

### Step 8: Offer Remediation (if `fix` also specified)

If `fix` is specified alongside review:
- If `fix severity [level]` specified: Filter fixes by severity (critical, high, medium, low)
- Show suggested fixes with before/after code
- Explain security implications
- Preview changes before applying
- Require explicit approval
- After applying fixes, delegate to the `secdevai-fix` skill for result export

## Security Context Sources

- `secdevai-review/context/security-review.context` - OWASP Top 10 patterns (always loaded)
- `secdevai-review/context/wstg-testing.context` - OWASP WSTG v4.2 web app testing patterns (auto-loaded for web code)
- `secdevai-review/context/golang-security.context` - Go-specific vulnerabilities and weaknesses (auto-loaded for Go code)

**WSTG Auto-Detection**: The WSTG context automatically loads when reviewing web application code or when explicitly requested.

**Golang Auto-Detection**: The Golang context automatically loads when reviewing Go source (e.g. `.go` files, `go.mod`) or when the user mentions Go/Golang.

**OCI/Container Auto-Detection**: The OCI image security references automatically load when the repo contains Dockerfiles, Containerfiles, Kubernetes manifests, or docker-compose files.

## Multi-Language Support

**CRITICAL**: While security context files contain primarily Python examples, you MUST adapt patterns to the language being reviewed.

### Language Detection and Adaptation

1. **Detect the Language**: Identify the programming language from file extension, syntax, or imports
   - Python: `.py`, imports like `import flask`, `from django`
   - JavaScript/TypeScript: `.js`, `.ts`, `.jsx`, `.tsx`, `require()`, `import from`
   - Java: `.java`, `import`, `class`, `public static void`
   - Go: `.go`, `package`, `import`, `func`
   - Ruby: `.rb`, `require`, `def`, `class`
   - PHP: `.php`, `<?php`, `namespace`
   - C#: `.cs`, `using`, `namespace`
   - Rust: `.rs`, `use`, `fn`, `impl`

2. **Translate Security Patterns**: Apply the same security principle but with language-specific syntax

   **Example - SQL Injection**:
   
   *Python (from context)*:
   ```python
   # BAD
   query = f"SELECT * FROM users WHERE id = {user_id}"
   # GOOD
   cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
   ```
   
   *JavaScript/Node.js (your response)*:
   ```javascript
   // BAD
   const query = `SELECT * FROM users WHERE id = ${userId}`;
   // GOOD
   db.query("SELECT * FROM users WHERE id = ?", [userId]);
   ```
   
   *Java (your response)*:
   ```java
   // BAD
   String query = "SELECT * FROM users WHERE id = " + userId;
   // GOOD
   PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
   stmt.setInt(1, userId);
   ```
   
   *Go (your response)*:
   ```go
   // BAD
   query := fmt.Sprintf("SELECT * FROM users WHERE id = %s", userID)
   // GOOD
   db.Query("SELECT * FROM users WHERE id = ?", userID)
   ```

3. **Use Language-Specific Frameworks and Idioms**:
   - Python: Django ORM, Flask, FastAPI patterns
   - JavaScript: Express.js, Next.js, React patterns
   - Java: Spring Security, Jakarta EE patterns
   - Go: net/http, Gin, Echo patterns
   - Ruby: Rails security patterns
   - PHP: Laravel, Symfony patterns
   - C#: ASP.NET Core patterns

4. **Provide Language-Appropriate Remediation**:
   - Reference language-specific security libraries
   - Use idiomatic code for that language
   - Cite language-specific documentation

5. **Security Principles Are Universal**:
   - The underlying vulnerability (SQL injection, XSS, etc.) is the same
   - The detection pattern (string concatenation, unescaped input) is similar
   - Only the syntax and remediation differ

### Example Language Adaptations

**XSS Prevention**:
- Python/Flask: Use Jinja2 auto-escaping, `escape()`, `Markup()`
- JavaScript/React: Use `textContent`, DOMPurify, React auto-escaping
- Java: Use OWASP Java Encoder, ESAPI
- Go: Use `html.EscapeString()`, `template.HTMLEscapeString()`

**Authentication**:
- Python: bcrypt, argon2, werkzeug.security
- JavaScript: bcrypt.js, passport.js, jsonwebtoken
- Java: Spring Security, BCryptPasswordEncoder
- Go: golang.org/x/crypto/bcrypt

**CSRF Protection**:
- Python/Django: `@csrf_protect`, CSRF middleware
- JavaScript/Express: csurf middleware
- Java/Spring: `@EnableWebSecurity`, CSRF token
- Go: gorilla/csrf

### Response Format for Non-Python Code

When reviewing non-Python code, structure your findings exactly the same way but with appropriate language examples:

```
## 🔴 **Critical: SQL Injection**

**Location**: `UserController.java:42-45`
**Language**: Java
**OWASP Category**: A03: Injection

**Vulnerable Code**:
```java
String query = "SELECT * FROM users WHERE username = '" + username + "'";
Statement stmt = connection.createStatement();
ResultSet rs = stmt.executeQuery(query);
```

**Risk**: Attacker can inject SQL commands leading to data breach

**Remediation**:
```java
// Use PreparedStatement with parameterized queries
String query = "SELECT * FROM users WHERE username = ?";
PreparedStatement stmt = connection.prepareStatement(query);
stmt.setString(1, username);
ResultSet rs = stmt.executeQuery();
```

**References**:
- OWASP: https://owasp.org/www-community/attacks/SQL_Injection
- Java: https://docs.oracle.com/javase/tutorial/jdbc/basics/prepared.html
```

## Verification Requirements

**CRITICAL - Line Number Verification**: Before presenting any findings:
1. After analyzing git diff/commits, read the actual modified files
2. Verify all line numbers in findings match the actual file content
3. Ensure Location fields match code reference line numbers exactly
4. Cross-check each finding against actual file content

**Format Consistency**:
- Location: `file:line_start-line_end` must match code block `startLine:endLine:filepath`
- Read actual files to confirm line numbers, don't rely only on diff context
