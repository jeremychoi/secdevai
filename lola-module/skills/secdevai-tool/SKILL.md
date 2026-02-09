---
name: secdevai-tool
description: Run external security analysis tools such as Bandit (Python linter) and OSSF Scorecard (repository assessment). Use when the user wants to execute specific security tools, combine their output with AI analysis, or run all available tools at once.
---

# SecDevAI Tool Command

## Description
Run external security analysis tools. Invoked via `/secdevai tool` or the `/secdevai-tool` alias.

## Usage
```
/secdevai tool bandit          # Use Bandit for Python security analysis
/secdevai tool scorecard       # Use Scorecard for repository security assessment
/secdevai tool all             # Run all available security tools
/secdevai-tool bandit          # Alias: same as /secdevai tool bandit
/secdevai-tool scorecard       # Alias: same as /secdevai tool scorecard
/secdevai-tool all             # Alias: same as /secdevai tool all
```

## Available Tools
- **bandit**: Python security linter - Scans Python code for common security issues
- **scorecard**: Repository security assessment tool (OSSF Scorecard) - Evaluates repository security practices
- **all**: Run all available security tools (bandit and scorecard) and combine their findings

## Expected Response

When this skill is invoked, follow these steps:

### Step 1: Tool Selection

**If no tool specified** (e.g., `/secdevai-tool` with no arguments):
- **IMPORTANT**: Prompt the user to select which tool they want to use
- Display available tools with descriptions in a clear, user-friendly format:
  - Show a heading: "SecDevAI Tool Selection"
  - List available tools with brief descriptions (see Available Tools above)
  - Show usage examples
- Do NOT run any tool automatically - wait for user to specify which tool they want

### Step 2: Run Tool (if tool specified)

- Run the specified security tool(s) via `scripts/security-review.sh`
- If `all` is specified: Run both bandit and scorecard, combining their findings
- Parse tool output and synthesize with AI analysis
- If tool unavailable: Fall back to AI-only analysis with a message explaining the tool wasn't found

### Step 3: Present Findings

- Provide integrated findings combining tool results with AI insights
- Present findings in a structured format similar to `/secdevai review`
- When `all` is used, clearly indicate which findings came from which tool

### Step 4: Save Results

After tool execution, collect tool findings into structured format and export:

```python
import importlib.util
from pathlib import Path

# Load the exporter from secdevai-export skill scripts
script_path = Path("secdevai-export/scripts/results_exporter.py")
spec = importlib.util.spec_from_file_location("results_exporter", script_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

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
markdown_path, sarif_path = mod.export_results(data, command_type="tool")
```

- The exporter will prompt the user to confirm the result directory (default: `secdevai-results`)
- Results are saved with timestamp: `secdevai-tool-YYYYMMDD_HHMMSS.md` and `.sarif`
