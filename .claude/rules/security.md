# Security Rules

> Security requirements for this project.
> Extends common security.md with project-specific rules.

## Pre-Commit Checklist

- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated at system boundary
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized output)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Error messages don't leak sensitive data
- [ ] No sensitive data in logs

## Secret Management

- NEVER hardcode secrets in source code
- ALWAYS use environment variables or secret manager
- Validate required secrets at startup
- Rotate any exposed secrets immediately

## Input Validation

- Validate ALL user input at the system boundary
- Use schema-based validation where available
- Fail fast with clear user-facing error messages
- Never trust external data (API responses, user input, file content)

## Security Response

If a security issue is found:

1. **STOP** immediately
2. Assess severity (Critical / High / Medium / Low)
3. Fix Critical and High issues before continuing
4. Rotate any exposed secrets
5. Search codebase for similar patterns
6. Document the fix in changelog
