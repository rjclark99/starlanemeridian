---
id: current.deployed-state
kind: current
status: active
verified_at: 2026-07-29
tags: [device, kodi, fire-tv, portal, control-api, real-debrid]
authority: [adb, wrangler, local-portal, docs/CURRENT_STATUS.md]
supersedes: []
---

# Reference device state

The latest bounded device check reports Kodi 21.3 with private
`skin.starlane.movies` 2.2.20 active. The main menu is VOD-only: Search, Home, New &
Popular, TV Shows, Movies, Categories, and My List. Mad Titan and The Crew, their
profile data, and cached install packages are absent. Starlane Movies: On Demand
6.7.81.1 remains enabled. The generated include has 106 Umbrella route references and
zero FenLight, Mad Titan, The Crew, Live TV ID, or Sports ID references. Production
skin 1.2.4 remains installed. Private 2.2.19 is the immediate rollback.

The setup application was upgraded in place to 0.5.0/code 5 using an APK signed by
the same certificate as the previously installed 0.3.0 build. It retained its
pairing and reported app version 5 through the production control plane. Kodi
remained running as 21.3 during the setup-app upgrade.

Production service state at Worker version
`9a4f3899-825b-4aae-9dcb-4ddf58b3fd0f` includes applied D1 migration
`0004_real_debrid_authorization.sql`. Public health returned 200, unauthenticated
`/v1/admin/*` traffic was redirected to Cloudflare Access, and the portal's existing
service-token configuration reached the admin devices endpoint without exposing its
credentials. The updated loopback portal returned 200 at `127.0.0.1:54731`, exposed
the Real-Debrid control, and retained its configured `appsettings.json` byte-for-byte.
Its vault is locked after restart and requires the owner to unlock it before use.

Local ignored rollback evidence is under
`build/device-backups/kodi-active-pre-real-debrid-deploy-20260729/`,
`build/device-backups/real-debrid-remote-auth-pre-0.5.0-20260729/`, and
`build/device-backups/portal-pre-real-debrid-20260729/`. The Kodi backup contains
the installed 21.3 APK plus a verified full `.kodi` archive; treat it as sensitive
because it contains provider settings and viewing databases.

Device reachability, installed versions, and rollback files are mutable. Recheck them
read-only before any hardware change and use the private-skin device-test runbook.
