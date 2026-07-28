---
id: subsystem.admin-portal
kind: subsystem
status: active
verified_at: 2026-07-28
tags: [dotnet, windows, vault, adb]
authority: [admin-portal/KodiSetup.Admin.csproj, admin-portal/Program.cs]
supersedes: []
---

# Windows administration portal

.NET 8 Windows x64, self-contained. The portal binds to loopback, requires an unlocked
vault for protected API work, and uses Argon2id, AES-256-GCM, and Windows DPAPI.
The local vault has no recovery bypass or cross-profile restore path.

Never print service-token values, replace a live vault/configuration with checked-in
blanks, weaken loopback binding, or add arbitrary cloud/ADB execution. Validate with
restore, Release build, and `admin-portal.tests`; a running portal or PID is external
state and must be inspected before restart.
