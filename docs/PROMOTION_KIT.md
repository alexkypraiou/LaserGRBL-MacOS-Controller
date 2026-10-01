# Promotion Kit

This kit keeps the project's public message consistent across GitHub, social networks, maker communities, and release announcements.

## Positioning

### One-line pitch

A modern, open-source GRBL controller for laser engravers and CNC machines on macOS.

### Short description

Connect, jog, preview, generate raster G-code, and stream laser jobs from a focused macOS desktop app with acknowledgement-based GRBL flow control.

### Full description

LaserGRBL for macOS is an independent open-source desktop controller for GRBL-compatible laser engravers and CNC machines. It combines serial connection, machine status, jogging, work-zero setup, G-code editing, raster image conversion, path preview, and acknowledgement-driven job streaming in one focused interface. A built-in demo controller lets makers evaluate the complete workflow without connecting hardware.

### Core message

**Control. Preview. Engrave.**

The supporting message is: **Built for macOS makers who want visible machine state, predictable streaming, and a straightforward open-source workflow.**

## GitHub profile setup

### Repository description

```text
A modern GRBL controller for laser engravers and CNC machines on macOS—safe streaming, path preview, and image-to-G-code.
```

### Website field

After enabling GitHub Pages with **GitHub Actions** as the source, run the `GitHub Pages` workflow and use:

```text
https://alexkypraiou.github.io/LaserGRBL-MacOS-Controller/
```

Until the landing page is deployed, use:

```text
https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller/releases/latest
```

### Suggested topics

```text
grbl
laser-engraver
laser-cutting
cnc
gcode
macos
pyqt6
arduino
maker
open-source
```

### Social preview

Upload `assets/social-preview.png` under **Settings → General → Social preview**.

## Audience

Primary audiences:

- macOS users with GRBL-compatible diode lasers.
- CNC and Arduino hobbyists building compact machines.
- Makers who currently switch operating systems to run a sender.
- Contributors interested in machine control, PyQt, and G-code tooling.

Secondary audiences:

- Fab labs and educational workshops.
- Open-source hardware communities.
- Developers looking for a compact GRBL protocol implementation.

## Launch posts

### X / Twitter

```text
I rebuilt LaserGRBL for macOS as a focused open-source GRBL workspace: serial connection, jogging, raster image-to-G-code, path preview, and acknowledgement-based job streaming—plus a demo mode with no hardware required.

GitHub: https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller
```

### LinkedIn

```text
I am releasing a major rebuild of LaserGRBL for macOS, an open-source desktop controller for GRBL-compatible laser engravers and CNC machines.

The new version includes:
• A modern macOS-focused PyQt interface
• Buffered GRBL status and serial parsing
• Acknowledgement-driven G-code streaming
• Pause, resume, and abort/reset controls
• Raster image-to-G-code conversion
• Toolpath preview and live machine coordinates
• A complete demo mode that requires no hardware
• Automated tests and macOS application builds

The project is in alpha and I am looking for careful feedback from macOS makers using different GRBL controllers, USB interfaces, Intel Macs, and Apple silicon Macs.

Repository: https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller
```

### Reddit / maker forum

Suggested title:

```text
I rebuilt an open-source GRBL laser controller for macOS — looking for hardware testers
```

Suggested post:

```text
macOS makers often end up switching to Windows or using a generic serial console for GRBL laser projects, so I rebuilt my open-source controller around a more reliable workflow.

LaserGRBL for macOS now supports serial discovery, GRBL status and work coordinates, X/Y/Z jogging, homing and unlock, raster image-to-G-code generation, G-code editing, path preview, and one-line-at-a-time streaming that waits for each GRBL acknowledgement.

There is also a --demo mode, so the full interface can be explored without connecting a machine.

The project is still alpha. I would especially value reports that include the controller board, GRBL version, USB chip, Mac model, and macOS version. Please follow proper laser safety procedures and start with the laser disconnected or at minimum power.

GitHub: https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller
```

### Hacker News / Show HN

```text
Show HN: An open-source GRBL laser and CNC controller for macOS
```

### Release announcement

```text
LaserGRBL for macOS v0.2.0 is available.

This release replaces the original prototype with a modular, tested application and introduces acknowledgement-driven streaming, a no-hardware demo controller, safer job controls, a new toolpath preview, optimized raster G-code generation, and automated macOS app builds.

Read the release notes and download the macOS bundle:
https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller/releases/tag/v0.2.0
```

## Community launch sequence

### Day 0 — Prepare

- Publish `v0.2.0` with the generated zip and checksum.
- Upload the social preview and repository topics.
- Verify the README on desktop and mobile.
- Create a pinned hardware-testing issue with the reporting template.

### Day 1 — Existing network

- Share the short launch post on personal social accounts.
- Ask two or three trusted makers to run demo mode and review installation instructions.
- Correct unclear documentation before wider promotion.

### Days 2–4 — Maker communities

- Post once in relevant GRBL, laser engraving, CNC, Arduino, and macOS communities.
- Adapt the introduction to each community instead of cross-posting identical copy.
- Lead with technical value and the request for compatibility feedback.
- Answer every reproducible report and link fixes to issues.

### Days 5–7 — Developer communities

- Publish the Show HN post or an equivalent developer-focused announcement.
- Highlight the protocol parser, stream state machine, tests, and demo mode.
- Tag a patch release if launch feedback reveals setup blockers.

### Week 2 — Proof and momentum

- Publish a compatibility table from verified reports.
- Share a short demo video or GIF showing connect, preview, and job progress.
- Post the first contributor-friendly roadmap issues.
- Thank testers publicly and link their fixes or reports.

## Content ideas

- “How GRBL acknowledgement-based streaming prevents command flooding.”
- “Turning a grayscale image into serpentine laser G-code.”
- “Building a PyQt macOS controller that can be tested without hardware.”
- “A practical GRBL laser safety checklist for software developers.”
- “Testing common CH340, CP210x, and FTDI controllers on macOS.”

## Promotion principles

- Do not call the application production-ready while it is in alpha.
- Do not claim support for hardware that has not been tested.
- Show real interface captures rather than conceptual mockups.
- Put laser safety near every first-run or beginner-oriented post.
- Invite specific, structured compatibility reports instead of generic feedback.
- Avoid spam: one useful post per community, followed by genuine support.

## Media assets

- `assets/social-preview.png` — GitHub and social link preview, 1280 × 640.
- `assets/app-screenshot.png` — real interface capture in demo mode, 1440 × 900.
- `assets/app-icon-1024.png` — application and profile icon source, 1024 × 1024.
