#!/bin/bash
# SecDevAI Security Review — thin wrapper
# Delegates to the Python implementation (security-review.py) which provides
# proper JSON serialization, input validation, and subprocess safety.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/security-review.py" "$@"
