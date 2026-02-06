---
name: secdevai-tool
description: Run external security analysis tools such as Bandit (Python linter) and OSSF Scorecard (repository assessment). Use when the user wants to execute specific security tools, combine their output with AI analysis, or run all available tools at once.
---

# SecDevAI Tool Command (Alias)

## Description
Alias for `/secdevai tool` - Use specific security tool for analysis.

## Usage
```
/secdevai-tool bandit          # Use Bandit for Python security analysis
/secdevai-tool scorecard       # Use Scorecard for repository security assessment
/secdevai-tool all             # Run all available security tools
```

## What This Command Does
This is an alias for `/secdevai tool`. See the main `/secdevai` command documentation for full details.

When invoked, this command:
- Runs the specified security tool via `scripts/security-review.sh`
- Parses tool output and synthesizes with AI analysis
- Falls back to AI-only analysis if tool is unavailable
- Provides integrated findings combining tool results with AI insights

## Expected Response

When user runs `/secdevai-tool`:

1. **If no tool specified** (e.g., `/secdevai-tool` with no arguments):
   - **IMPORTANT**: Prompt the user to select which tool they want to use
   - Display available tools with descriptions in a clear, user-friendly format:
     - Show a heading: "SecDevAI Tool Selection"
     - List available tools with brief descriptions:
       - **bandit**: Python security linter - Scans Python code for common security issues
       - **scorecard**: Repository security assessment - Evaluates repository security practices (OSSF Scorecard)
       - **all**: Run all available security tools (bandit and scorecard) and combine their findings
     - Show usage examples:
       - `/secdevai-tool bandit` - Run Bandit for Python security analysis
       - `/secdevai-tool scorecard` - Run Scorecard for repository security assessment
       - `/secdevai-tool all` - Run all available security tools
   - Do NOT run any tool automatically - wait for user to specify which tool they want

2. **If tool specified** (e.g., `/secdevai-tool bandit`, `/secdevai-tool scorecard`, `/secdevai-tool all`):
   - Run the specified security tool(s) via `scripts/security-review.sh`
   - If `all` is specified: Run both bandit and scorecard, combining their findings
   - Parse tool output and synthesize with AI analysis
   - If tool unavailable: Fall back to AI-only analysis with a message explaining the tool wasn't found
   - Provide integrated findings combining tool results with AI insights
   - Present findings in a structured format similar to `/secdevai review`
   - When `all` is used, clearly indicate which findings came from which tool
   - **Save Results** (after tool execution):
     - Collect tool findings into structured format
     - Use `secdevai_cli.results_exporter.export_results()` to save results
     - Prompt user to confirm result directory (default: `secdevai-results`)
     - Save both markdown and SARIF files with timestamp: `secdevai-tool-YYYYMMDD_HHMMSS.md` and `.sarif`

## Available Tools
- `bandit`: Python security linter - Scans Python code for common security issues
- `scorecard`: Repository security assessment tool (OSSF Scorecard) - Evaluates repository security practices
- `all`: Run all available security tools (bandit and scorecard) and combine their findings

