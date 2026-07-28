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
`skin.starlane.movies` 2.2.20 active. The main menu is VOD-only: Search, Home, New &
Popular, TV Shows, Movies, Categories, and My List. Mad Titan and The Crew, their
profile data, and cached install packages are absent. Starlane Movies: On Demand
6.7.81.1 remains enabled. The generated include has 106 Umbrella route references and
zero FenLight, Mad Titan, The Crew, Live TV ID, or Sports ID references. Production
skin 1.2.4 remains installed. Private 2.2.19 is the immediate rollback.

Device reachability, installed versions, and rollback files are mutable. Recheck them
read-only before any hardware change and use the private-skin device-test runbook.
