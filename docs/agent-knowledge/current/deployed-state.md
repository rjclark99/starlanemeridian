---
id: current.deployed-state
kind: current
status: active
verified_at: 2026-07-28
tags: [device, kodi, fire-tv]
authority: [docs/CURRENT_STATUS.md, docs/TECHNICAL_HANDOFF_2026-07-26.md]
supersedes: []
---

# Reference device state

The latest bounded device check reports Kodi 21.3 with private
`skin.starlane.movies` 2.2.17 active. Live TV uses The Crew; Sports retains Mad Titan.
The generated include had 101 Umbrella, three Mad Titan, three The Crew, zero FenLight,
and zero broken Mad Titan Live NetTV references. Production skin 1.2.4 remains
installed for rollback.

Device reachability, installed versions, and rollback files are mutable. Recheck them
read-only before any hardware change and use the private-skin device-test runbook.
