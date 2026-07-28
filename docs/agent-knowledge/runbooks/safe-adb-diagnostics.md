---
id: runbook.safe-adb-diagnostics
kind: runbook
status: active
verified_at: 2026-07-28
tags: [adb, device, diagnostics, security]
authority: [docs/OPERATIONS.md, docs/TECHNICAL_HANDOFF_2026-07-26.md]
supersedes: []
---

# Safe ADB diagnostics

Confirm device address and authorization without assuming availability. Batch bounded
read-only checks: package/version, active skin, exact log matches, and relevant files.
Do not print complete sensitive settings. Before mutation stop Kodi and hash/preserve
the exact targets. Prefer recoverable moves and targeted pushes.

Use ADB-only local forwarding for Kodi JSON-RPC rather than enabling network services,
then remove the forward. Do not expose port 5555 publicly. If Windows reports socket
10013, check VPN/LAN policy once and ask the owner to permit LAN traffic; never change
VPN state silently.
