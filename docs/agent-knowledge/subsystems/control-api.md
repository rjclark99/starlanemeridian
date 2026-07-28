---
id: subsystem.control-api
kind: subsystem
status: active
verified_at: 2026-07-28
tags: [cloudflare, typescript, d1, security]
authority: [control-api/src, control-api/migrations, control-api/package.json]
supersedes: []
---

# Cloudflare control API

TypeScript Worker with D1, Wrangler, and Vitest. It implements expiring pairing,
signed device requests, replay protection, bounded status/events, device/household
deletion, closed-enum commands, and strictly allowlisted public Kodi redirects.

Do not add arbitrary payloads, URLs, shell, ADB, Kodi built-ins, or credential fields.
Protect only the intended admin boundary; device/public routes use their designed
authentication. Run `pnpm check` and `pnpm test`. Deployment and migrations require
separate authority and a preservation/rollback plan.
