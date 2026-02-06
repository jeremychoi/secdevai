---
name: secdevai
description: AI-powered secure development assistant. Dispatches to review, fix, tool, and export subcommands. Use when the user invokes /secdevai with no subcommand or needs an overview of available security commands.
---

# SecDevAI Secure Development Assistant Command

## Description
Perform AI-powered security code review with optional integration to existing security tools. Supports file, selection, and full codebase analysis.

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

## What This Command Does
- Loads `secdevai-review/context/security-review.context` for security analysis guidelines
- Analyzes code for OWASP Top 10 patterns and common vulnerabilities
- Optionally integrates with external tools (Bandit, Scorecard)
- Provides prioritized findings with severity classification
- Suggests remediation with code examples
- Always shows preview before applying fixes
- Requires explicit approval before modifying code

## Expected Response

When user runs `/secdevai`, you should:

1. **Show Help** (if no arguments or `help` specified):
   - **IMPORTANT**: `/secdevai` with no arguments should ONLY show help, NOT run review
   - Display all available commands with descriptions
   - Show usage examples
   - List all options and flags
   - Do NOT perform any security review unless `review` is explicitly specified

2. **Review Command** (ONLY if `review` is explicitly specified):
   - **Load Security Context**:
     - Always read: `secdevai-review/context/security-review.context` for OWASP Top 10 patterns
     
    - **Auto-detect WSTG context** (additionally read `secdevai-review/context/wstg-testing.context` if ANY condition applies):
      - Source code is for a web application, web service, or web site
      - User explicitly mentions: "WSTG", "Web Security Testing Guide", or category numbers (4.1-4.12)
     
     - **Note**: WSTG patterns enhance web application security analysis with 12 comprehensive testing categories
   
   - **Detect Scope** (in priority order):
     - If `review last-commit --number N` specified: Review last N commits (requires git)
     - If `review last-commit` specified: Review last commit (requires git)
     - If `review @ file` is specified: Review the specified file
     - If text is selected in UI: Automatically review only the selected code
     - Otherwise (default): Scan entire codebase (respect `.secdevaiignore`)

   - **Optional Tool Integration**:
     - If `tool` specified: Run `secdevai-tool/scripts/security-review.sh` with tool name
     - Parse tool output and synthesize with AI analysis
     - If tool unavailable: Fall back to AI-only analysis

   - **Perform Analysis**:
     - Scan code for security patterns from context
     - Classify findings by severity (Critical/High/Medium/Low/Info)
     - Reference OWASP categories
     - Provide context-aware explanations

   - **Present Findings**:
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

   - **Save Results** (after presenting findings):
     - Collect all findings into a structured JSON format matching the security-review-report.json schema
     - Use the results exporter to save results:
       ```python
       from secdevai_cli.results_exporter import export_results
       import json
       
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
       markdown_path, sarif_path = export_results(data, command_type="review")
       ```
     - The exporter will prompt the user to confirm the result directory (default: `secdevai-results`)
     - Results are saved with timestamp: `secdevai-review-YYYYMMDD_HHMMSS.md` and `.sarif`

   - **Offer Remediation** (if `fix` specified):
     - If `fix severity [level]` specified: Filter fixes by severity (critical, high, medium, low)
     - Show suggested fixes with before/after code
     - Explain security implications
     - Preview changes before applying
     - Require explicit approval
     - **Save Results** (after applying fixes):
       - Collect information about applied fixes into structured format
       - Use the results exporter to save results:
         ```python
         from secdevai_cli.results_exporter import export_results
         
         # Collect fix results into data structure
         data = {
             "metadata": {
                 "tool": "secdevai-fix",
                 "version": "1.0.0",
                 "timestamp": datetime.now().isoformat(),
                 "analyzer": "AI Security Fix",
             },
             "summary": {
                 "total_fixes": [count],
                 "applied": [count],
                 "skipped": [count],
             },
             "fixes": [list of applied fix objects],
         }
         
         # Export to markdown and SARIF
         markdown_path, sarif_path = export_results(data, command_type="fix")
         ```
       - The exporter will prompt the user to confirm the result directory (default: `secdevai-results`)
       - Results are saved with timestamp: `secdevai-fix-YYYYMMDD_HHMMSS.md` and `.sarif`

3. **Git Commit** (if `git-commit` specified):
   - Only proceed if there are approved fixes that have been applied
   - Verify git is configured (check for git repository and user config)
   - If conditions met: Create a commit with descriptive message about security fixes
   - If conditions not met: Explain what's missing (no approved fixes or git not configured)

4. **Tool Command** (if `tool` specified):
   - Run `secdevai-tool/scripts/security-review.sh` with tool name (bandit, scorecard, all)
   - Parse tool output and synthesize with AI analysis
   - **Save Results** (after tool execution):
     - Collect tool findings into structured format
     - Use the results exporter to save results:
       ```python
       from secdevai_cli.results_exporter import export_results
       
       # Collect tool results into data structure
       data = {
           "metadata": {
               "tool": "[tool-name]",
               "version": "1.0.0",
               "timestamp": datetime.now().isoformat(),
               "analyzer": "[tool-name] Security Tool",
           },
           "summary": {
               "total_findings": [count],
               "critical": [count],
               "high": [count],
               "medium": [count],
               "low": [count],
               "info": [count],
           },
           "findings": [list of tool finding objects],
       }
       
       # Export to markdown and SARIF
       markdown_path, sarif_path = export_results(data, command_type="tool")
       ```
     - The exporter will prompt the user to confirm the result directory (default: `secdevai-results`)
     - Results are saved with timestamp: `secdevai-tool-YYYYMMDD_HHMMSS.md` and `.sarif`

5. **Export Option** (if `export` specified):
   - Generate report in requested format
   - Include all findings with metadata
   - Save to file

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

**WSTG Auto-Detection**: The WSTG context automatically loads when reviewing web application, web service, or web site code, or when explicitly requested by mentioning "WSTG" or category numbers (4.1-4.12).

**Multi-Language Support**: While context files contain primarily Python examples, you MUST adapt security patterns to the language being reviewed (JavaScript, Java, Go, Ruby, PHP, C#, Rust, etc.). Translate the security principles and provide language-specific remediation with appropriate frameworks and idioms.

## Integration

This command integrates with:
- `secdevai-review/context/` directory for security analysis guidelines
- `secdevai-tool/scripts/security-review.sh` for optional tool integration
- `.secdevaiignore` for excluding files from scans
- External tools: Bandit, Scorecard

## Important Notes

- **Never modify code without explicit approval**
- **Always show preview before changes**
- **Create backups before applying fixes**
- **Respect `.secdevaiignore` file**
- **Cache results to avoid re-scanning**
