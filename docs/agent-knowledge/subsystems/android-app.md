---
id: subsystem.android-app
kind: subsystem
status: active
verified_at: 2026-07-28
tags: [android, kotlin, compose, security]
authority: [android-app/app/build.gradle.kts, android-app/app/src]
supersedes: []
---

# Android setup application

Kotlin 2.3.21/Compose, Java 17, `minSdk 25`, and compile/target SDK 36. The app verifies
signed manifests, artifact hashes, package identity, ABI, and signing certificates;
creates a non-exportable P-256 device key; signs requests; and stores Real-Debrid
tokens only in Keystore-backed local storage.

The 0.5.2 source candidate has one narrowly scoped Android 9/Fire OS profile
integration. After the user grants the existing storage permission, Bootstrap
preparation merges only `addons.unknownsources=true` into official Kodi's
`guisettings.xml`, preserving all other settings and using rollback-safe replacement.
The package ID and setting ID are constants, unsafe XML is rejected, and no remote
parameter, shell, ADB, accessibility, or general settings writer exists. Android 10+
retains the manual Kodi step because scoped storage blocks this cross-app route.

Preserve D-pad navigation and visible Android permission/install confirmations. Never
add unattended installation, credential collection, arbitrary commands, or remote
shell behavior. Iterate with focused tests, then
`:app:testDebugUnitTest :app:lintDebug`; hardware acceptance for Fire TV and Android
TV/Google TV remains separate.
