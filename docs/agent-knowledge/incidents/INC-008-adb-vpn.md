---
id: incident.adb-vpn
kind: incident
status: active
verified_at: 2026-07-28
tags: [adb, vpn, network]
authority: [docs/TECHNICAL_HANDOFF_2026-07-26.md]
supersedes: []
---

# VPN blocked LAN ADB

## Summary

ADB returned Windows socket error 10013 while Proton blocked LAN access; the device
address and authorization were correct.

## Diagnose and prevent

Check device power/address/authorization and host LAN policy once. Ask the owner to
allow LAN traffic or pause VPN. Never silently alter VPN settings, and never expose
ADB publicly.
