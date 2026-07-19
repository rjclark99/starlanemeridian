# Starlane Meridian brand guide

## Brand idea

Starlane Meridian is a calm navigation system for home media. The identity combines a meridian arc, a guide star, a horizon, and converging lanes. It should feel precise and quietly futuristic rather than playful, aggressive, or densely “sci-fi.”

Working tagline: **Your media. On course.**

## Logo

The primary emblem is the transparent `assets/branding/starlane-meridian-emblem-v2.png`. Keep clear space around it equal to at least one quarter of the emblem width. Do not rotate it, add an outer badge, recolour it purple, or place it over visually busy imagery.

The generated chroma source and first matte are retained as provenance and iteration history. Production consumers use the `-v2` transparent emblem.

## Colour system

| Role | Colour | Use |
| --- | --- | --- |
| Deep space | `#050B14` | Primary background |
| Night route | `#081522` | Panels and dialogs |
| Meridian blue | `#102A42` | Elevated surfaces |
| Starlight | `#F4FAFF` | Primary text and selected surfaces |
| Ice route | `#61C8FF` | Focus, progress, and links |
| Guide mint | `#67E8C4` | Success, active markers, and fine accents |
| Navigation grey | `#91A8C0` | Secondary text |
| Alert coral | `#FF7B72` | Errors only |

## Typography and motion

Use a clean system sans-serif with a strong distinction between regular and semibold weights. Uppercase is reserved for the wordmark, short navigation labels, and small wayfinding metadata. Body copy remains sentence case.

TV transitions use restrained fades and 8-pixel focus slides between 150 and 280 milliseconds. Focus must be obvious without relying on colour alone: selected controls also change surface, weight, and position.

## Interface principles

- One clear focal point per screen.
- Generous safe margins for television overscan.
- Large, predictable D-pad targets.
- Dark negative space is part of the composition, not unused space.
- Device status is expressed as a progress line, named phase, human-readable message, and error code when applicable.
- Never place credentials, tokens, IP addresses, viewing activity, or payment information in cloud telemetry.

## Source artwork

The emblem and home background were generated with the built-in image-generation workflow, then stored in `assets/branding`. Android and web derivatives are reproducibly created by `tools/build_brand_assets.py`. The Kodi skin builder embeds the same production assets so every surface presents one coherent identity.
