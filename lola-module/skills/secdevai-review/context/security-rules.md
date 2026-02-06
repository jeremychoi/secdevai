# Security Rules Reference Catalog

**Purpose**: Reference catalog of security patterns (not loaded by default to save tokens)

This file can be referenced when needed for specific security pattern details.

## Python Security Patterns

### Authentication & Authorization
- Session management vulnerabilities
- JWT security issues
- OAuth implementation flaws
- Role-based access control (RBAC) issues

### Cryptography
- Symmetric encryption patterns
- Asymmetric encryption patterns
- Key management issues
- Certificate validation problems

### Data Protection
- PII handling
- Data encryption at rest
- Data encryption in transit
- Data masking requirements

### Network Security
- TLS/SSL configuration
- Certificate pinning
- DNS security
- Firewall rules

### API Security
- Rate limiting
- API authentication
- Input validation
- Output encoding

## Language-Specific Patterns

### Python
- Django security patterns
- Flask security patterns
- FastAPI security patterns
- AsyncIO security considerations

### JavaScript/TypeScript (Future)
- XSS prevention
- CSRF protection
- DOM manipulation security
- NPM dependency security

### Java (Future)
- Serialization security
- Reflection security
- Classloader security
- Spring security patterns

### Go (Future)
- Goroutine security
- Channel security
- Interface security
- Dependency management

## Severity Classifications

### Critical
- Remote code execution
- Authentication bypass
- Privilege escalation
- Data breach potential

### High
- SQL injection
- Command injection
- Sensitive data exposure
- Broken authentication

### Medium
- Weak cryptography
- Missing input validation
- Insecure defaults
- Information disclosure

### Low
- Missing security headers
- Weak password policies
- Insufficient logging
- Code quality issues

## References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CWE Top 25: https://cwe.mitre.org/top25/
- Python Security: https://python.readthedocs.io/en/latest/library/security.html

