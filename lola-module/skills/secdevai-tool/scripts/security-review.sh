#!/bin/bash
# SecDevAI Security Review Script
# Integrates with external security tools and formats output for AI consumption

set -euo pipefail

TOOL="${1:-}"
TARGET="${2:-.}"

# Output JSON structure
OUTPUT_FILE=$(mktemp)
trap "rm -f $OUTPUT_FILE ${OUTPUT_FILE}.error" EXIT

echo "{" > "$OUTPUT_FILE"
echo "  \"tool\": \"$TOOL\"," >> "$OUTPUT_FILE"
echo "  \"findings\": [" >> "$OUTPUT_FILE"

FINDINGS_COUNT=0

# Function to escape JSON string (handles newlines, quotes, etc.)
escape_json() {
    printf '%s' "$1" | jq -Rs .
}

# Function to add finding to JSON
add_finding() {
    local severity="$1"
    local rule="$2"
    local message="$3"
    local file="$4"
    local line="${5:-}"
    local code="${6:-}"
    local source_tool="${7:-}"
    
    if [ $FINDINGS_COUNT -gt 0 ]; then
        echo "," >> "$OUTPUT_FILE"
    fi
    
    echo "    {" >> "$OUTPUT_FILE"
    [ -n "$source_tool" ] && echo "      \"source_tool\": $(escape_json "$source_tool")," >> "$OUTPUT_FILE"
    echo "      \"severity\": $(escape_json "$severity")," >> "$OUTPUT_FILE"
    echo "      \"rule\": $(escape_json "$rule")," >> "$OUTPUT_FILE"
    echo "      \"message\": $(escape_json "$message")," >> "$OUTPUT_FILE"
    echo "      \"file\": $(escape_json "$file")," >> "$OUTPUT_FILE"
    [ -n "$line" ] && echo "      \"line\": $line," >> "$OUTPUT_FILE"
    [ -n "$code" ] && echo "      \"code\": $(escape_json "$code")," >> "$OUTPUT_FILE"
    # Remove trailing comma
    sed -i '' '$ s/,$//' "$OUTPUT_FILE" 2>/dev/null || sed -i '$ s/,$//' "$OUTPUT_FILE"
    echo "    }" >> "$OUTPUT_FILE"
    
    FINDINGS_COUNT=$((FINDINGS_COUNT + 1))
}

# Bandit integration
run_bandit() {
    local source_tool="${1:-bandit}"
    if ! command -v bandit &> /dev/null; then
        echo "  \"error\": \"bandit not found\"" >> "$OUTPUT_FILE"
        return 1
    fi
    
    # Run bandit with JSON output
    # Extract only JSON portion (bandit outputs log messages to stdout before JSON)
    # Use sed to extract everything from the first '{' to the end
    # Note: bandit exits with code 1 when it finds issues, which is normal
    local bandit_output
    bandit_output=$(bandit -r "$TARGET" -f json -q 2>&1 | sed -n '/^{/,$p' || true)
    
    # Check if we got valid JSON
    if [ -z "$bandit_output" ] || ! echo "$bandit_output" | jq empty 2>/dev/null; then
        echo "  \"error\": \"bandit produced invalid JSON output\"" >> "$OUTPUT_FILE"
        return 1
    fi
    
    # Parse bandit JSON and extract findings
    # Process each finding as a JSON object to handle multi-line code fields
    local finding_count
    finding_count=$(echo "$bandit_output" | jq '.results | length' 2>/dev/null || echo "0")
    
    if [ "$finding_count" -gt 0 ]; then
        local idx=0
        while [ $idx -lt "$finding_count" ]; do
            local rule severity message file line code
            
            rule=$(echo "$bandit_output" | jq -r ".results[$idx].test_id // empty" 2>/dev/null)
            severity=$(echo "$bandit_output" | jq -r ".results[$idx].issue_severity // empty" 2>/dev/null)
            message=$(echo "$bandit_output" | jq -r ".results[$idx].issue_text // empty" 2>/dev/null)
            file=$(echo "$bandit_output" | jq -r ".results[$idx].filename // empty" 2>/dev/null)
            line=$(echo "$bandit_output" | jq -r ".results[$idx].line_number // empty" 2>/dev/null)
            code=$(echo "$bandit_output" | jq -r ".results[$idx].code // empty" 2>/dev/null)
            
            # Skip if rule is empty
            [ -z "$rule" ] && { idx=$((idx + 1)); continue; }
            
            # Map bandit severity to our format
            case "$severity" in
                HIGH) sev="HIGH" ;;
                MEDIUM) sev="MEDIUM" ;;
                LOW) sev="LOW" ;;
                *) sev="INFO" ;;
            esac
            
            add_finding "$sev" "$rule" "$message" "$file" "$line" "$code" "$source_tool"
            
            idx=$((idx + 1))
        done
    fi
    
    return 0
}

# Scorecard integration
run_scorecard() {
    local source_tool="${1:-scorecard}"
    if ! command -v scorecard &> /dev/null; then
        echo "  \"error\": \"scorecard not found\"" >> "$OUTPUT_FILE"
        return 1
    fi
    
    # Run scorecard with JSON output for local folder
    # Scorecard requires --local flag for local analysis
    # Scorecard JSON structure: checks[] with name, score (0-10), reason, details[]
    scorecard --local="$TARGET" --format=json 2>/dev/null | jq -r '.checks[]? | select(.score < 10) | "\(.name)|\(.score)|\(.reason // "No reason provided")|\(.details[0] // "")"' | while IFS='|' read -r rule score message detail; do
        # Map scorecard score (0-10 integer) to severity format
        # Lower scores indicate more critical issues
        if [ -z "$score" ] || [ "$score" = "null" ]; then
            sev="INFO"
        else
            # Use awk for numeric comparison (more portable than bc)
            score_int=$(echo "$score" | awk '{print int($1)}')
            if [ "$score_int" -lt 3 ]; then
                sev="HIGH"
            elif [ "$score_int" -lt 6 ]; then
                sev="MEDIUM"
            else
                sev="LOW"
            fi
        fi
        
        # Use detail as code snippet if available
        code="${detail:-}"
        file="repository"
        line=""
        
        add_finding "$sev" "$rule" "$message" "$file" "$line" "$code" "$source_tool"
    done
    
    return 0
}

# Run all tools
run_all() {
    local tools_run=0
    local tools_failed=0
    local error_msg=""
    
    # Run bandit
    if command -v bandit &> /dev/null; then
        run_bandit "bandit"
        tools_run=$((tools_run + 1))
    else
        tools_failed=$((tools_failed + 1))
    fi
    
    # Run scorecard
    if command -v scorecard &> /dev/null; then
        run_scorecard "scorecard"
        tools_run=$((tools_run + 1))
    else
        tools_failed=$((tools_failed + 1))
    fi
    
    # Store error message for later (will be added after findings array closes)
    if [ $tools_failed -gt 0 ]; then
        if [ $tools_run -eq 0 ]; then
            error_msg="No tools available (bandit and scorecard not found)"
        else
            error_msg="Some tools unavailable ($tools_failed of $((tools_run + tools_failed)) tools not found)"
        fi
        # Store in a temp file for later retrieval
        echo "$error_msg" > "${OUTPUT_FILE}.error"
    fi
    
    return 0
}

# Main execution
case "$TOOL" in
    bandit)
        run_bandit "bandit"
        ;;
    scorecard)
        run_scorecard "scorecard"
        ;;
    all)
        run_all
        ;;
    *)
        echo "  \"error\": \"Unknown tool: $TOOL\"" >> "$OUTPUT_FILE"
        echo "  \"available_tools\": [\"bandit\", \"scorecard\", \"all\"]" >> "$OUTPUT_FILE"
        exit 1
        ;;
esac

echo "  ]" >> "$OUTPUT_FILE"

# Add error/warning if present (for "all" tool)
if [ -f "${OUTPUT_FILE}.error" ]; then
    error_msg=$(cat "${OUTPUT_FILE}.error")
    rm -f "${OUTPUT_FILE}.error"
    if echo "$error_msg" | grep -q "No tools available"; then
        echo "," >> "$OUTPUT_FILE"
        echo "  \"error\": \"$error_msg\"" >> "$OUTPUT_FILE"
    else
        echo "," >> "$OUTPUT_FILE"
        echo "  \"warning\": \"$error_msg\"" >> "$OUTPUT_FILE"
    fi
fi

echo "}" >> "$OUTPUT_FILE"

# Output JSON
cat "$OUTPUT_FILE"

