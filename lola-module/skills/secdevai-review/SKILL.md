---
name: secdevai-review
description: Perform AI-powered security code review using OWASP Top 10 and WSTG patterns. Use when reviewing source code, specific files, git commits, or entire codebases for security vulnerabilities. Supports multi-language analysis and severity classification.
---

# SecDevAI Review Command (Alias)

## Description
Alias for `/secdevai review` - Perform security code review.

## Usage
```
/secdevai-review               # Review selected code (if selected) or full codebase scan
/secdevai-review @ file        # Review specific file
/secdevai-review last-commit    # Review last commit
/secdevai-review last-commit --number N  # Review last N commits
```

## What This Command Does
This is an alias for `/secdevai review`. See the main `/secdevai` command documentation for full details.

When invoked, this command:
- **Load Security Context**:
  - Always read: `secdevai-review/context/security-review.context` for OWASP Top 10 patterns
  
  - **Auto-detect WSTG context** (additionally read `secdevai-review/context/wstg-testing.context` if ANY condition applies):
    - Source code is for a web application, web service, or web site
    - User explicitly mentions: "WSTG", "Web Security Testing Guide", or category numbers (4.1-4.12)

- Analyzes code for OWASP Top 10 patterns and WSTG testing patterns (auto-detected for web apps)
- Provides prioritized findings with severity classification
- Supports file, selection, and full codebase analysis

## Security Context Sources

- `secdevai-review/context/security-review.context` - OWASP Top 10 patterns (always loaded)
- `secdevai-review/context/wstg-testing.context` - OWASP WSTG v4.2 web app testing patterns (auto-loaded for web code)
- `secdevai-review/context/security-rules.md` - Extended pattern catalog (manual reference)

**WSTG Auto-Detection**: The WSTG context automatically loads when reviewing web application code or when explicitly requested.

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

## Expected Response
See `/secdevai` command documentation. This alias executes `/secdevai review` with the same behavior.

## Verification Requirements

**CRITICAL - Line Number Verification**: Before presenting any findings:
1. After analyzing git diff/commits, read the actual modified files
2. Verify all line numbers in findings match the actual file content
3. Ensure Location fields match code reference line numbers exactly
4. Cross-check each finding against actual file content

**Format Consistency**:
- Location: `file:line_start-line_end` must match code block `startLine:endLine:filepath`
- Read actual files to confirm line numbers, don't rely only on diff context

**Important**: After presenting findings, always save results to Markdown and SARIF formats:
- Use `secdevai_cli.results_exporter.export_results()` to save results
- Prompt user to confirm result directory (default: `secdevai-results`)
- Save both markdown and SARIF files with timestamp

