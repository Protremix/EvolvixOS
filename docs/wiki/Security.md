# Security

## Authentication

### JWT + OTP
- Users register with email and receive an OTP code
- OTP verified → JWT token issued (24h expiry)
- All authenticated endpoints require `Authorization: Bearer <token>`

### API Keys
- Per-user API keys with `evx_` prefix
- Stored as SHA-256 hashes (never plaintext)
- 4 endpoints: generate, list, revoke, usage
- Rate limited: 100/min per key

## Rate Limiting

| Scope | Limit | Window |
|-------|-------|--------|
| Per IP | 30 requests | 1 minute |
| Per API key | 100 requests | 1 minute |

Implementation: sliding window with Redis-style counters.

## SSRF Guard (CWE-918)

Ported from Octop's SSRF guard module. Blocks requests to:
- Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Loopback (127.0.0.0/8)
- Link-local (169.254.0.0/16)
- Metadata endpoints (169.254.169.254)

## Shell Injection Protection

- All `bash_exec` calls use `shlex.split()` + `shell=False`
- Input validation on all command arguments
- Dangerous characters filtered

## Error Handling

- 21 error handling blocks patched across the codebase
- Graceful degradation when external APIs are unavailable
- No stack traces exposed to end users

## Best Practices

1. Never commit `.env` or `.jwt_secret` files
2. Use environment variables for all secrets
3. Rotate API keys regularly via `/auth/api-keys`
4. Monitor rate limiting logs for abuse
5. Keep Let's Encrypt SSL certificates current
