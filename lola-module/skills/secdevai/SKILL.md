---
name: secdevai
description: AI-powered secure development assistant. Dispatches to review, fix, tool, and export subcommands. Use when the user invokes /secdevai with no subcommand or needs an overview of available security commands.
---

# SecDevAI Secure Development Assistant Command

## Description
AI-powered secure development assistant that dispatches to specialized sub-skills. Use `/secdevai` with no arguments for help, or specify a subcommand.

**Important**: `/secdevai` with no arguments shows help. Use `/secdevai review` to perform security reviews.

## Usage
```
/secdevai                      # Show help (default)
/secdevai help                 # Show all available commands
/secdevai review               # Review selected code (if selected) or full codebase scan
/secdevai review @ file        # Review specific file
/secdevai review last-commit   # Review last commit
/secdevai review last-commit --number N  # Review last N commits
/secdevai fix [severity high]  # Apply suggested fixes (with approval, optional severity filter)
/secdevai tool bandit          # Use specific tool (bandit, scorecard, all)
/secdevai git-commit           # Commit approved fixes (requires git config and approved fixes)
/secdevai export json          # Export report (json, markdown, sarif)
```

## Aliases
```
/secdevai-help                 # Show help (alias for /secdevai help)
/secdevai-fix                  # Apply suggested fixes (alias for /secdevai fix)
/secdevai-review               # Review code (alias for /secdevai review)
/secdevai-report               # Generate security report
/secdevai-tool                 # Use specific tool (alias for /secdevai tool)
/secdevai-export               # Export report (alias for /secdevai export)
```

## Command Dispatch

When user runs `/secdevai`, route to the appropriate sub-skill:

1. **No arguments / `help`** (default):
   - **IMPORTANT**: `/secdevai` with no arguments should ONLY show help, NOT run review
   - Display all available commands with descriptions
   - Show usage examples
   - List all options and flags
   - Do NOT perform any security review unless `review` is explicitly specified

2. **`review`**: **Delegate to the `secdevai-review` skill.**
   The review skill handles all security code review logic including scope detection, security context loading, OWASP/WSTG analysis, findings presentation, and result export.

3. **`fix`**: **Delegate to the `secdevai-fix` skill.**
   The fix skill handles applying security remediation with before/after diffs, severity filtering, explicit approval, and result export.

4. **`tool`**: **Delegate to the `secdevai-tool` skill.**
   The tool skill handles external tool execution (Bandit, Scorecard), output parsing, AI synthesis, and result export.

5. **`export`**: **Delegate to the `secdevai-export` skill.**
   The export skill handles converting findings to Markdown and SARIF formats.

6. **`git-commit`**:
   - Only proceed if there are approved fixes that have been applied
   - Verify git is configured (check for git repository and user config)
   - If conditions met: Create a commit with descriptive message about security fixes
   - If conditions not met: Explain what's missing (no approved fixes or git not configured)

## Security Principles

Follow these principles from the security context:
- Complete Mediation
- Defense in Depth
- Least Privilege
- Secure by Design, Default, Deployment

## Security Context Sources

This command uses multiple security context files:
- `secdevai-review/context/security-review.context` - OWASP Top 10 patterns (always loaded)
- `secdevai-review/context/wstg-testing.context` - OWASP WSTG v4.2 web app testing patterns (auto-loaded for web code)
- `secdevai-review/context/security-rules.md` - Extended pattern catalog (manual reference)

**Multi-Language Support**: While context files contain primarily Python examples, all sub-skills MUST adapt security patterns to the language being reviewed (JavaScript, Java, Go, Ruby, PHP, C#, Rust, etc.). Translate the security principles and provide language-specific remediation with appropriate frameworks and idioms.

## Integration

This command integrates with:
- `secdevai-review/context/` directory for security analysis guidelines
- `secdevai-tool/scripts/security-review.sh` for optional tool integration
- `secdevai-export/scripts/results_exporter.py` for result export
- `.secdevaiignore` for excluding files from scans
- External tools: Bandit, Scorecard

## Important Notes

- **Never modify code without explicit approval**
- **Always show preview before changes**
- **Create backups before applying fixes**
- **Respect `.secdevaiignore` file**
- **Cache results to avoid re-scanning**
