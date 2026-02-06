---
name: secdevai-fix
description: Apply suggested security fixes from a prior review. Use when the user wants to remediate security findings with before/after code diffs, severity filtering, and explicit approval before modifying code.
---

# SecDevAI Fix Command (Alias)

## Description
Alias for `/secdevai fix` - Apply suggested security fixes.

## Usage
```
/secdevai-fix                  # Apply all suggested fixes (with approval)
/secdevai-fix severity high    # Apply fixes filtered by severity (critical, high, medium, low)
```

## What This Command Does
This is an alias for `/secdevai fix`. See the main `/secdevai` command documentation for full details.

When invoked, this command:
- Shows suggested fixes with before/after code
- Explains security implications
- Previews changes before applying
- Requires explicit approval before modifying code

## Expected Response
See `/secdevai` command documentation. This alias executes `/secdevai fix` with the same behavior.

**Important**: 
- Always shows preview before changes and requires explicit approval
- After applying fixes, always save results to Markdown and SARIF formats:
  - Use `secdevai_cli.results_exporter.export_results()` to save results
  - Prompt user to confirm result directory (default: `secdevai-results`)
  - Save both markdown and SARIF files with timestamp

