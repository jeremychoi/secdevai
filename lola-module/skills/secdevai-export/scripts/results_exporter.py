#!/usr/bin/env python3
"""
SecDevAI Results Exporter
Exports security review results to Markdown and SARIF formats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.prompt import Prompt

console = Console()

# SARIF schema version
SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"


def confirm_result_directory(default: str = "secdevai-results") -> Path:
    """
    Prompt user to confirm result directory.
    
    Args:
        default: Default directory name
        
    Returns:
        Path object for the result directory
    """
    console.print(f"\n[bold blue]Save results to directory:[/bold blue]")
    result_dir_input = Prompt.ask(
        f"Result directory",
        default=default,
        show_default=True,
    )
    
    result_dir = Path(result_dir_input).expanduser().resolve()
    
    # Create directory if it doesn't exist
    result_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[green]✓[/green] Results will be saved to: {result_dir}\n")
    
    return result_dir


def severity_to_sarif_level(severity: str) -> str:
    """Convert SecDevAI severity to SARIF level."""
    severity_upper = severity.upper()
    if severity_upper in ("CRITICAL", "HIGH"):
        return "error"
    elif severity_upper == "MEDIUM":
        return "warning"
    elif severity_upper == "LOW":
        return "note"
    else:
        return "none"


def severity_to_sarif_severity(severity: str) -> str:
    """Convert SecDevAI severity to SARIF severity."""
    severity_upper = severity.upper()
    if severity_upper == "CRITICAL":
        return "critical"
    elif severity_upper == "HIGH":
        return "high"
    elif severity_upper == "MEDIUM":
        return "medium"
    elif severity_upper == "LOW":
        return "low"
    else:
        return "info"


def convert_to_markdown(data: Dict[str, Any]) -> str:
    """
    Convert security review results to Markdown format.
    
    Args:
        data: Security review results dictionary
        
    Returns:
        Markdown formatted string
    """
    lines = []
    
    # Header
    lines.append("# SecDevAI Security Review Report")
    lines.append("")
    
    # Metadata
    metadata = data.get("metadata", {})
    lines.append("## Metadata")
    lines.append("")
    lines.append(f"- **Tool**: {metadata.get('tool', 'secdevai')}")
    lines.append(f"- **Version**: {metadata.get('version', '1.0.0')}")
    lines.append(f"- **Timestamp**: {metadata.get('timestamp', datetime.now().isoformat())}")
    
    target_file = metadata.get("target_file")
    if target_file:
        lines.append(f"- **Target File**: `{target_file}`")
    
    analyzer = metadata.get("analyzer")
    if analyzer:
        lines.append(f"- **Analyzer**: {analyzer}")
    
    lines.append("")
    
    # Summary
    summary = data.get("summary", {})
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total Findings**: {summary.get('total_findings', 0)}")
    lines.append(f"- **Critical**: {summary.get('critical', 0)}")
    lines.append(f"- **High**: {summary.get('high', 0)}")
    lines.append(f"- **Medium**: {summary.get('medium', 0)}")
    lines.append(f"- **Low**: {summary.get('low', 0)}")
    lines.append(f"- **Info**: {summary.get('info', 0)}")
    lines.append("")
    
    # Findings
    findings = data.get("findings", [])
    if findings:
        lines.append("## Findings")
        lines.append("")
        
        # Group by severity
        severity_groups = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
            "INFO": [],
        }
        
        for finding in findings:
            severity = finding.get("severity", "INFO").upper()
            if severity in severity_groups:
                severity_groups[severity].append(finding)
            else:
                severity_groups["INFO"].append(finding)
        
        # Emoji mapping for severity
        severity_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "INFO": "ℹ️",
        }
        
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            group_findings = severity_groups[severity]
            if not group_findings:
                continue
            
            emoji = severity_emoji.get(severity, "")
            lines.append(f"### {emoji} **{severity} Severity** ({len(group_findings)})")
            lines.append("")
            
            for finding in group_findings:
                finding_id = finding.get("id", "")
                title = finding.get("title", "")
                
                lines.append(f"#### {finding_id}: {title}")
                lines.append("")
                
                # Location
                location = finding.get("location", {})
                if location:
                    file_path = location.get("file", "")
                    start_line = location.get("start_line")
                    end_line = location.get("end_line")
                    
                    if file_path:
                        if start_line and end_line:
                            lines.append(f"**Location**: `{file_path}:{start_line}-{end_line}`")
                        elif start_line:
                            lines.append(f"**Location**: `{file_path}:{start_line}`")
                        else:
                            lines.append(f"**Location**: `{file_path}`")
                        lines.append("")
                
                # OWASP Category and CWE
                owasp_category = finding.get("owasp_category")
                cwe = finding.get("cwe")
                
                if owasp_category or cwe:
                    lines.append("**Classification**:")
                    if owasp_category:
                        lines.append(f"- OWASP: {owasp_category}")
                    if cwe:
                        lines.append(f"- CWE: {cwe}")
                    lines.append("")
                
                # Description
                description = finding.get("description")
                if description:
                    lines.append("**Description**:")
                    lines.append("")
                    lines.append(description)
                    lines.append("")
                
                # Risk
                risk = finding.get("risk")
                if risk:
                    lines.append("**Risk**:")
                    lines.append("")
                    lines.append(risk)
                    lines.append("")
                
                # Attack Vector
                attack_vector = finding.get("attack_vector")
                if attack_vector:
                    lines.append("**Attack Vector**:")
                    lines.append("")
                    lines.append(attack_vector)
                    lines.append("")
                
                # Attack Example
                attack_example = finding.get("attack_example")
                if attack_example:
                    lines.append("**Attack Example**:")
                    lines.append("")
                    lines.append("```")
                    lines.append(attack_example)
                    lines.append("```")
                    lines.append("")
                
                # Vulnerable Code
                vulnerable_code = finding.get("vulnerable_code")
                if vulnerable_code:
                    lines.append("**Vulnerable Code**:")
                    lines.append("")
                    lines.append("```python")
                    lines.append(vulnerable_code)
                    lines.append("```")
                    lines.append("")
                
                # Remediation
                remediation = finding.get("remediation", {})
                if remediation:
                    approach = remediation.get("approach")
                    code = remediation.get("code")
                    
                    if approach:
                        lines.append("**Remediation**:")
                        lines.append("")
                        lines.append(approach)
                        lines.append("")
                    
                    if code:
                        lines.append("**Fixed Code**:")
                        lines.append("")
                        lines.append("```python")
                        lines.append(code)
                        lines.append("```")
                        lines.append("")
                
                # Impact
                impact = finding.get("impact", [])
                if impact:
                    lines.append("**Impact**:")
                    lines.append("")
                    for item in impact:
                        lines.append(f"- {item}")
                    lines.append("")
                
                # References
                references = finding.get("references", [])
                if references:
                    lines.append("**References**:")
                    lines.append("")
                    for ref in references:
                        lines.append(f"- {ref}")
                    lines.append("")
                
                lines.append("---")
                lines.append("")
    
    # Affected Endpoints
    affected_endpoints = data.get("affected_endpoints", [])
    if affected_endpoints:
        lines.append("## Affected Endpoints")
        lines.append("")
        for endpoint in affected_endpoints:
            endpoint_name = endpoint.get("endpoint", "")
            file_path = endpoint.get("file", "")
            line = endpoint.get("line", "")
            vulnerability = endpoint.get("vulnerability", "")
            user_input = endpoint.get("user_input", "")
            
            lines.append(f"### {endpoint_name}")
            lines.append("")
            if file_path:
                lines.append(f"- **File**: `{file_path}:{line}`")
            if vulnerability:
                lines.append(f"- **Vulnerability**: {vulnerability}")
            if user_input:
                lines.append(f"- **User Input**: {user_input}")
            lines.append("")
    
    # Recommendations
    recommendations = data.get("recommendations", {})
    if recommendations:
        lines.append("## Recommendations")
        lines.append("")
        
        immediate = recommendations.get("immediate_actions", [])
        if immediate:
            lines.append("### Immediate Actions")
            lines.append("")
            for action in immediate:
                lines.append(f"- {action}")
            lines.append("")
        
        long_term = recommendations.get("long_term_improvements", [])
        if long_term:
            lines.append("### Long-term Improvements")
            lines.append("")
            for improvement in long_term:
                lines.append(f"- {improvement}")
            lines.append("")
    
    return "\n".join(lines)


def convert_to_sarif(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert security review results to SARIF format.
    
    Args:
        data: Security review results dictionary
        
    Returns:
        SARIF formatted dictionary
    """
    metadata = data.get("metadata", {})
    findings = data.get("findings", [])
    
    # Create SARIF structure
    sarif = {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": metadata.get("tool", "secdevai"),
                        "version": metadata.get("version", "1.0.0"),
                        "informationUri": "https://github.com/RedHatProductSecurity/secdevai",
                        "rules": [],
                    }
                },
                "results": [],
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "exitCode": 0,
                    }
                ],
            }
        ],
    }
    
    # Extract unique rules
    rules = {}
    for finding in findings:
        rule_id = finding.get("id", "")
        if rule_id and rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "name": finding.get("title", ""),
                "shortDescription": {
                    "text": finding.get("title", ""),
                },
                "fullDescription": {
                    "text": finding.get("description", ""),
                },
                "properties": {
                    "tags": [],
                },
            }
            
            # Add OWASP and CWE tags
            owasp_category = finding.get("owasp_category")
            if owasp_category:
                rules[rule_id]["properties"]["tags"].append(owasp_category)
            
            cwe = finding.get("cwe")
            if cwe:
                rules[rule_id]["properties"]["tags"].append(cwe)
    
    # Add rules to SARIF
    sarif["runs"][0]["tool"]["driver"]["rules"] = list(rules.values())
    
    # Convert findings to SARIF results
    for finding in findings:
        location = finding.get("location", {})
        file_path = location.get("file", "")
        start_line = location.get("start_line")
        end_line = location.get("end_line")
        
        result = {
            "ruleId": finding.get("id", ""),
            "level": severity_to_sarif_level(finding.get("severity", "INFO")),
            "message": {
                "text": finding.get("description", ""),
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_path,
                        },
                    }
                }
            ],
            "properties": {
                "severity": severity_to_sarif_severity(finding.get("severity", "INFO")),
            },
        }
        
        # Add region (line numbers)
        if start_line:
            region = {"startLine": start_line}
            if end_line:
                region["endLine"] = end_line
            result["locations"][0]["physicalLocation"]["region"] = region
        
        # Add code snippet if available
        vulnerable_code = finding.get("vulnerable_code")
        if vulnerable_code and start_line:
            result["locations"][0]["physicalLocation"]["contextRegion"] = {
                "startLine": start_line,
                "snippet": {
                    "text": vulnerable_code,
                },
            }
        
        sarif["runs"][0]["results"].append(result)
    
    return sarif


def export_results(
    data: Dict[str, Any],
    result_dir: Optional[Path] = None,
    command_type: str = "review",
) -> tuple[Path, Path]:
    """
    Export security review results to Markdown and SARIF formats.
    
    Args:
        data: Security review results dictionary
        result_dir: Directory to save results (will prompt if None)
        command_type: Type of command (review, fix, tool)
        
    Returns:
        Tuple of (markdown_path, sarif_path)
    """
    if result_dir is None:
        result_dir = confirm_result_directory()
    
    # Generate timestamp for directory and filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create datetime-based subdirectory with 'secdevai-' prefix
    timestamp_dir = result_dir / f"secdevai-{timestamp}"
    timestamp_dir.mkdir(parents=True, exist_ok=True)
    
    base_name = f"secdevai-{command_type}-{timestamp}"
    
    # Save Markdown
    markdown_content = convert_to_markdown(data)
    markdown_path = timestamp_dir / f"{base_name}.md"
    markdown_path.write_text(markdown_content, encoding="utf-8")
    console.print(f"[green]✓[/green] Markdown report saved: {markdown_path}")
    
    # Save SARIF
    sarif_content = convert_to_sarif(data)
    sarif_path = timestamp_dir / f"{base_name}.sarif"
    sarif_path.write_text(json.dumps(sarif_content, indent=2), encoding="utf-8")
    console.print(f"[green]✓[/green] SARIF report saved: {sarif_path}")
    
    return markdown_path, sarif_path



