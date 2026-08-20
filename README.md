# Zennify

<p align="center">
    <img src="./assets/banner.png" alt="Zennify Banner">
    <br />
    <br />
    <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
    <br />
    <img src="https://img.shields.io/badge/Axum-000000?style=for-the-badge&logo=rust&logoColor=white" alt="Axum">
    <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js">
    <img src="https://img.shields.io/badge/Tauri-24C8D8?style=for-the-badge&logo=tauri&logoColor=white" alt="Tauri">
    <img src="https://img.shields.io/badge/Kotlin_Multiplatform-7F52FF?style=for-the-badge&logo=kotlin&logoColor=white" alt="Kotlin Multiplatform">
    <img src="https://img.shields.io/badge/Slint-232B2B?style=for-the-badge&logo=rust&logoColor=white" alt="Slint UI">
    <br />
    <img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
    <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux">
    <img src="https://img.shields.io/badge/Android-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Android">
    <img src="https://img.shields.io/badge/Embedded-Devices-4B0082?style=for-the-badge" alt="Embedded Devices">
    <br />
    <br />
    <i>A hardcore, gamified productivity suite for deep work</i>
</p>

## Abstract

Zennify is a cross-platform, local-first gamified productivity ecosystem designed for deep work and personal accountability. It integrates interval activity tracking, spaced-repetition flashcards, Pomodoro focus timers, customizable habit tracking, and a real-life reward shop tied together by a unified virtual economy. Built using a Distributed Hybrid Topology, Zennify operates with a central host server on desktop while client applications on desktop, mobile, and embedded hardware maintain local database replicas to guarantee zero latency and complete data privacy without cloud dependence.

## Objective

To provide a privacy-first, low-overhead productivity environment that uses gamification, strict accountability rules, and clear performance analytics to eliminate procrastination and cultivate long-term focus habits across all user devices.

## Features

### Functional

- **Activity Tracking & Tagging**: Prompts users at configurable intervals to log activities with tags and productivity ratings. Productive actions earn wallet coins, while unproductive logs incur coin deductions.
- **Flashcard Revision Manager**: Scans markdown directories for Q&A pairs and uses the Free Spaced Repetition Scheduler (FSRS) algorithm to optimize review intervals and long-term memory retention.
- **Habit Tracking & Reminders**: Manages custom habits with daily heatmaps, schedule routines, startup missed-reminder catch-ups, completion rewards, and missed-day penalties.
- **Pomodoro Timer Management**: Runs customizable focus and break countdown cycles with crash-proof state persistence. Earns virtual currency exclusively on completed work phases.
- **Todo Task Management**: Enforces active task limits, sorts tasks by deadline urgency, restricts rescheduling to a single explicit confirmation, and computes proactiveness scores.
- **Shop, Inventory & Economy**: Enables purchasing custom real-life reward items with wallet coins, banking partial unused reward time, compounding duplicate item durations, enforcing minimum penalty-to-reward ratios, and declaring bankruptcy for negative balances.
- **Multi-Platform Data Synchronization**: Reconciles state across devices via operational logs, Last-Write-Wins (LWW) conflict resolution, Hybrid Logical Clocks (HLC), and Backend-for-Frontend (BFF) payload tailoring.

### Non Functional

- **Local-First Responsiveness**: All client user interfaces read from and write to local SQLite replicas first, guaranteeing sub-millisecond input response times.
- **Privacy & Offline Independence**: Operates fully over local networks without sending personal activity or habit data to external cloud servers.
- **Form-Factor Optimization**: Provides lightweight binary payloads and minimal footprint UI layers for resource-constrained Slint embedded devices while serving complete structural payloads to desktop and mobile clients.
- **High Concurrency & Determinism**: Uses non-blocking asynchronous I/O on the host server and 100% deterministic pure domain core algorithms.

## Specifications

### Requirements

- **Desktop Host Server**: Rust toolchain (cargo, rustc).
- **Desktop Client Application**: Node.js, Next.js framework, and Tauri CLI.
- **Mobile Client Application**: Kotlin Multiplatform (KMP) or Flutter SDK.
- **Embedded Client Application**: Rust toolchain with Slint UI toolkit support.
- **Storage Engine**: SQLite database engine with Write-Ahead Logging (WAL) support.

### Dependencies

- **Web & Server Runtime**: Axum, Tokio async runtime.
- **Data Persistence**: SQLite (via sqlx / r2d2).
- **Serialization & Protocols**: Serde, Serde JSON, Bincode / Postcard, LZ4 compression.
- **Domain Algorithms**: FSRS algorithm engine, Hybrid Logical Clock (HLC) tick generator.

## Getting Started

Installation and usage guidelines are documented in [`docs/begin.md`](./docs/begin.md).
