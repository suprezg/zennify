# Zennify

<p align="center">
    <img src="./assets/banner.png" alt="Zennify Banner">
    <br />
    <br />
    <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
    <br />
    <img src="https://img.shields.io/badge/Gin-00ADD8?style=for-the-badge&logo=go&logoColor=white" alt="Gin">
    <img src="https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white" alt="Rust">
    <img src="https://img.shields.io/badge/Svelte-FF3E00?style=for-the-badge&logo=svelte&logoColor=white" alt="Svelte">
    <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React">
    <img src="https://img.shields.io/badge/Tauri-24C8D8?style=for-the-badge&logo=tauri&logoColor=white" alt="Tauri">
    <img src="https://img.shields.io/badge/Kotlin-7F52FF?style=for-the-badge&logo=kotlin&logoColor=white" alt="Kotlin">
    <img src="https://img.shields.io/badge/Slint-232B2B?style=for-the-badge&logo=rust&logoColor=white" alt="Slint UI">
    <br />
    <img src="https://img.shields.io/badge/Web-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Web">
    <img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
    <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux">
    <img src="https://img.shields.io/badge/Android-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Android">
    <img src="https://img.shields.io/badge/Embedded-Devices-4B0082?style=for-the-badge" alt="Embedded Devices">
    <br />
    <br />
    <i>A hardcore, discipline-driven productivity suite built on daily Planning, Execution, and Reflection.</i>
</p>

## Abstract

Zennify is not casual gamification. It is built upon the philosophical approach that work and time management can be accomplished through daily Planning, Execution, and Reflection, cultivating a disciplined and genuinely productive environment. The only purpose of incorporating an economic currency mechanism is to instill real discipline by establishing that relaxation, leisure, and pleasure must be earned through hard, focused labor.

```
+-------------------------------------------------------+
|                   THE ZENNIFY TRIAD                   |
|                                                       |
|   [ PLANNING ]  -->  [ EXECUTION ]  --> [ REFLECTION ] |
|   Goal-Oriented       Pomodoro Focus      Activity &  |
|  Task Management          Timer         Habit Tracking|
+-------------------------------------------------------+
                            |
                   [ THE DISCIPLINE CORE ]
             Earning Leisure Through Hard Labor
        Real-Life Reward Shop & Hardcore Bankruptcy
```

To eliminate distraction and superficial productivity, the entire ecosystem is engineered to be hardcore. The system enforces strict concurrent goal limits so users only create goals they can actively focus on and execute, preventing the common trap of endlessly planning tasks with zero execution. Every task carries an unyielding deadline where missing any single task triggers an immediate fail-all cascade across the entire goal, deducting severe wallet penalties. Active goals and tasks cannot be deleted or evaded once committed. There are no artificial streaks or coin multipliers; accountability is measured honestly at face value. Persistent negative debt hits a hard floor at -250 coins, enforcing automatic bankruptcy, asset liquidation, and complete inventory forfeiture.

Every target client—Web built with Svelte, Desktop built with React and Tauri, Mobile built natively with Kotlin for Android, and Embedded built with Slint and Rust—runs completely standalone with its own local dual-layer persistence combining a materialized relational database with an append-only event log. An optional self-hosted synchronization daemon written in Go using Gin pairs with an internal Rust rusqlite sidecar process over standard input/output pipes, enabling Git-like event synchronization across devices with zero reliance on cloud services.

## Objective

To provide an autonomous, privacy-first, zero-latency productivity environment that replaces soft task management with unyielding commitment, enabling individuals to conquer procrastination and earn their leisure through daily planning, execution, and reflection.

## Features

### Functional

- **Goal-Oriented Task Management (Planning)**: Replaces soft todo lists with unyielding goal contracts decomposed into mandatory tasks. Enforces strict concurrent active goal limits to eliminate task hoarding without execution. Failing any single task deadline immediately triggers a fail-all cascade across the entire goal and deducts penalty coins. Active goals and tasks cannot be deleted or evaded once committed.
- **Pomodoro Focus Timer (Execution)**: Runs customizable work and recovery countdown cycles (work time, short break, long break, and cycle intervals) with crash-proof local persistence.
- **Activity Tracking & Tagging (Reflection)**: Prompts users at configurable intervals (15m, 30m, 45m, 60m) to reflect on and categorize their recent actions into productive and un productive with category tags.
- **Habit Tracking & Routines (Reflection)**: Tracks daily habits with custom days-of-week cadences, individual calendar heatmaps, and startup missed-reminder catch-ups.
- **Real-Life Reward Shop**: Enables users to create custom real-world incentives with designated coin prices and durations (e.g., "1 Hour Gaming = 100 coins"). Rewards are purchased strictly with earned wallet coins, establishing that leisure must be earned through hard labor.
- **Inventory & Time Banking**: Purchased rewards sit in inventory as banked time assets. Users activate items in a dedicated countdown window, pause to bank unused minutes for later, and compound duplicate purchases additively into single combined durations.
- **Discipline Economy & Bankruptcy**: Enforces a closed-loop economy without streaks or multipliers. Negative balances allow grinding out of debt or declaring voluntary bankruptcy. Hitting the -250 coin limit automatically enforces bankruptcy, incrementing the permanent bankruptcy count, resetting balance to zero, and liquidating all inventory assets.
- **Event-Sourced HLC Synchronization**: Synchronizes state across platforms using Hybrid Logical Clocks (HLC) and immutable mutation event logs. Operates via a Git-like protocol (commit, push, pull, merge) using local and global tracking pointers without branches, transmitting only required incremental deltas.

### Non Functional

- **Custom Semantic Reconciliation (No LWW)**: Rejects naive Last-Write-Wins (LWW) overwriting in favor of deterministic domain-specific convergence.
- **Automated Snapshot Compaction & Time-Travel**: Triggers when the event log exceeds 5,000 entries, compressing the first 4,000 entries into a verified base state snapshot while retaining the latest 1,000 uncompressed logs for active peer reconciliation.
- **Two-Tier Server Core (Go Relay + Rust Sidecar)**: Couples an external Go/Gin HTTP gateway for high-concurrency network streaming with an internal Rust rusqlite sidecar process over standard input/output pipes (stdpipe) using newline-delimited JSON. The Rust engine manages WAL-mode database persistence, multi-device tracking, and reconciliation.
- **Standalone Offline Independence**: Every platform client functions with complete local autonomy, executing reads and writes directly against native local storage and zero server connection requirements.
- **Minimalist 2D Duo-Chromatic User Interface**: Flat 2D visual design, provides Dark and Light themes with selectable accent color from seven options.
- **Multi-Platform Form-Factor Optimization**: Delivers native client implementations tailored to each platform—reactive web interfaces via Svelte, desktop performance via React + Tauri, native mobile performance via Kotlin (Android), and low-footprint embedded binaries via Slint and Rust.

## Prerequisites

### Requirements

To compile and build Zennify from source on your local system:

- **Web Client (Svelte)**: Node.js (LTS version 18 or higher) and package manager (`npm`, `pnpm`, or `yarn`).
- **Desktop Client (React + Tauri)**: Node.js, stable Rust toolchain (`rustc`, `cargo`), Tauri CLI (`@tauri-apps/cli`), and platform C/C++ compilers (`gcc`, `clang`, or MSVC Build Tools).
- **Mobile Client (Kotlin)**: Android SDK, Android NDK, JDK 17+, and a configured Gradle build environment.
- **Embedded Client (Slint)**: Stable Rust toolchain (2021 edition) and Slint GUI toolkit system dependencies.
- **Synchronization Server (Go + Rust)**: Go toolchain (version 1.21 or higher) for the Gin gateway and Rust toolchain for the internal rusqlite sidecar engine.
- **Linux Development Headers**: Development packages for `libwebkit2gtk-4.1-dev` (or `4.0`), `libssl-dev`, and `libayatana-appindicator3-dev`.

### Dependencies

To run and use Zennify directly without building from source:

- **Web Browser**: Any modern evergreen web browser supporting standard Web APIs and client storage (Chrome, Firefox, Safari, Edge).
- **Desktop Environment**: Windows 10/11 (64-bit with Microsoft Edge WebView2 Evergreen Runtime) or modern Linux distributions with WebKit2GTK runtime libraries.
- **Mobile Environment**: Android device running Android 8.0 (Oreo / API Level 26) or higher.
- **Embedded Hardware**: Microcontroller or single-board computer running embedded Linux compatible with the Slint GUI runtime.
- **Optional Sync Server Runtime**: Local loopback or network interface with standard process pipe (`stdpipe`) execution permissions.
- **Filesystem Permissions**: Standard user-level read and write filesystem permissions for local database files and append-only event logs.

## Getting Started

Installation and Usage Guidelines are inside the docs/begin.md.
