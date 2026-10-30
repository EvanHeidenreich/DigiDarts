# DigiDarts Requirements Document

**Team:** Evan Heidenreich, Nicholas Rigg, Jacob Curtis
**Advisor:** Dr. William Hawkins III
---

## 1. Version and Change Log

| Version | Date | Change | Author |
| ------- | ---- | ------ | ------ |
| 0.1 | 2026-10-28 | Initial consolidation of User Stories, D0, D1, D2 and Week 8 plan into one requirements baseline | Evan Heidenreich, Nicholas Rigg, Jacob Curtis |

## 2. Purpose and Scope

**Purpose.** This document states what DigiDarts must do and for whom. It is the baseline that the Technical Specification (`Technical_Specification.md`) traces to and that the Week 10 test plan verifies.

**Product.** DigiDarts is an automated dartboard. Two cameras watch a standard dartboard, computer vision detects where each dart lands, a game engine scores it, and a web app shows the live scoreboard and saves player statistics.

**In scope for this release:**
- Dart detection and segment scoring from two cameras
- Games: 501, 301, Cricket, Around the World (priority differs by mode, see Section 7)
- Player profiles, live scoreboard, manual score correction
- Match history and per-player statistics
- Calibration and lighting control

**Out of scope:** see the Won't list in Section 7.

**Related documents:** `User_Stories.md`, `Design_Diagrams/` (D0 architecture, D1 data model and API contract, D2 detailed design), `README.md`.

## 3. Stakeholders and User Goals

| Stakeholder | Role | Goal (from Week 4 stories) |
| ----------- | ---- | -------------------------- |
| Player | Throws darts, views score | Play without keeping score by hand; trust the score shown |
| Guest | Plays once, no profile | Start a game in under two minutes with no setup |
| Host / Owner | Sets up and maintains the board | Calibrate quickly, fix misreads, keep the system running |
| Team (developers) | Builds and maintains the system | Clear, testable requirements; modular design |
| Advisor / Instructor | Evaluates the project | Evidence of requirements, design, and testing rigor |

## 4. Glossary

Each term is defined once and used with exactly this meaning in both documents.

| Term | Definition |
| ---- | ---------- |
| Board | The physical Viper dartboard and its mount. |
| Dart | One physical dart thrown at the Board. |
| Throw | One Dart landing on the Board and being detected. |
| Turn | One player's set of up to three Throws before play passes on. |
| Game | One play of a game mode (501, 301, Cricket, Around the World) from start to finish. |
| Segment | One scoring region of the Board, identified by number (1-20, bull) and multiplier (single, double, triple). |
| Bust | A Turn in 501/301 that would take the score below zero (or to one) and is therefore voided. |
| Checkout | Finishing a 501/301 Game by reaching exactly zero with a double. |
| Player | A person with a saved profile. |
| Guest | A person playing without a saved profile; statistics are not stored. |
| Host | The person who operates and configures the system. |
| Calibration | The procedure that maps camera pixels to Board Segments. |
| Detection | The vision step that finds a Dart tip in camera frames. |
| Confidence | A 0-1 score the vision service attaches to a Detection. |
| Correction | A manual change by a user to the Segment of a detected Throw. |
| Board Controller | The Dell mini PC that runs all DigiDarts software at the Board. |
| Vision Service | Software that captures frames, performs Detection, and outputs Throw events. |
| Game Engine | Software that applies game rules to Throw events and maintains Game state. |
| API Server | Software exposing REST and WebSocket interfaces to the Web App. |
| Web App | The browser-based user interface. |
| Session | A continuous period of use from system start to shutdown. |

## 5. Functional Requirements

Source stories use placeholder IDs. `[TEAM: map each to a real story in User_Stories.md.]`

| ID | Requirement | Priority | Source | Verification |
| -- | ----------- | -------- | ------ | ------------ |
| REQ-01 | The system shall detect each dart that lands on the Board and report its Segment within 2.0 s of the dart coming to rest. | Must | US-01 | Test |
| REQ-02 | The system shall report the correct Segment for at least 95% of Throws in a 200-Throw test set covering all 20 numbers and all multipliers under standard lighting. | Must | US-01 | Test |
| REQ-03 | The system shall score 501 and 301 Games for 1 to 4 Players, applying Bust and double-out Checkout rules, and shall let a user advance the Turn manually. | Must | US-02 | Test |
| REQ-04 | The system shall score Cricket Games (numbers 15-20 and bull, three marks to close) for 2 to 4 Players. | Should | US-03 | Test |
| REQ-05 | The system shall score Around the World Games for 1 to 4 Players, advancing a Player to the next number only on a hit of the current number. | Could | US-04 | Test |
| REQ-06 | The system shall let a user create, select, and delete Player profiles and shall support Guest play without a profile. | Must | US-05 | Test, Demonstration |
| REQ-07 | The system shall update the on-screen scoreboard within 1.0 s of a Throw being scored, on every connected client. | Must | US-06 | Test |
| REQ-08 | The system shall let a user correct or undo the most recent Throw in no more than 3 taps, with the Game state recalculated correctly. | Must | US-07 | Test |
| REQ-09 | The system shall store completed Game results and show each Player their three-dart average, win count, and Checkout percentage. | Should | US-08 | Test, Demonstration |
| REQ-10 | The system shall provide a guided Calibration that a Host can complete in 5 minutes or less and that yields a pass/fail result. | Must | US-09 | Demonstration |
| REQ-11 | The system shall detect dart removal after a Turn and advance to the next Player automatically within 3 s of the last Dart being removed. | Should | US-10 | Test |
| REQ-12 | The system shall restore an interrupted Game, losing no completed Turn, after the Board Controller restarts. | Should | US-11 | Test |
| REQ-13 | The system shall switch the LED lighting on at Game start and off after 10 minutes of inactivity. | Should | US-12 | Demonstration |

## 6. Non-Functional Requirements

| ID | Category | Requirement | Priority | Source | Verification |
| -- | -------- | ----------- | -------- | ------ | ------------ |
| NFR-01 | Performance | The system shall show a scored Throw on the scoreboard within 2.0 s of the dart coming to rest, at the 95th percentile, with 4 clients connected. | Must | US-06 | Test |
| NFR-02 | Performance | The API Server shall answer non-vision requests within 200 ms at the 95th percentile on the local network with 4 clients. | Should | US-06 | Test |
| NFR-03 | Security | The API Server shall require a valid session token on every state-changing request and shall reject unauthenticated requests with HTTP 401. | Must | US-13 | Test |
| NFR-04 | Security / Privacy | The system shall keep camera frames on the Board Controller, never transmit them off the local network, and delete them within 60 s unless debug mode is on. | Should | US-13 | Inspection, Test |
| NFR-05 | Reliability | The system shall complete a 3-hour Session with no crash and no unrecoverable fault in at least 9 of 10 test Sessions. | Must | US-14 | Test |
| NFR-06 | Reliability | The Vision Service shall recover from a camera disconnect and reconnect within 10 s without restarting the Game. | Should | US-14 | Test |
| NFR-07 | Usability | At least 4 of 5 first-time users shall start a 501 Game for two Players without help in 90 s or less. | Should | US-15 | Usability test |
| NFR-08 | Usability | The scoreboard shall be legible at 3 m (current score in text at least 48 px on a 1080p display), and all touch targets shall be at least 44 px. | Could | US-15 | Inspection |

All thresholds above are proposals. `[TEAM: adjust to what your cameras and CPU can actually achieve; a threshold you cannot meet is worse than a modest one you can.]`

## 7. MoSCoW Summary

Of 21 requirements, 10 are Must (about 48%).

**Must (MVP):** REQ-01, REQ-02, REQ-03, REQ-06, REQ-07, REQ-08, REQ-10, NFR-01, NFR-03, NFR-05

**Should:** REQ-04, REQ-09, REQ-11, REQ-12, REQ-13, NFR-02, NFR-04, NFR-06, NFR-07

**Could:** REQ-05, NFR-08

**Won't (this release):**
- Native iOS/Android apps (browser access only)
- Cloud accounts, cloud sync, or any hosted backend
- Game modes beyond the four listed
- More than 4 Players per Game
- More than two cameras, or any change to the Board beyond the 3D-printed camera and light mounts
- Outdoor use or use in uncontrolled lighting
- Tournament brackets and leagues
- Voice control and audio commentary

## 8. Inherited Constraints

| ID | Constraint | Origin |
| -- | ---------- | ------ |
| CON-01 | Software shall run on Dell mini form-factor 760 PCs; no discrete GPU can be assumed. | Hardware on hand |
| CON-02 | Imaging shall use two Arducam AR0234 USB 3.0 cameras (SKU B0495C). | Hardware on hand |
| CON-03 | The Board is a standard Viper dartboard with a 3D-printed camera and light ring; the Board itself is not modified. | Hardware on hand |
| CON-04 | Total project budget shall not exceed $350. | Week 3 essay |
| CON-05 | Source shall live in the team GitHub repository; requirements, priorities and traceability shall be the team's own work. | Course policy |
| CON-06 | The system shall operate on a local network with no paid cloud services. | Week 3 essay |

## 9. Assumptions and Open Questions

| # | Type | Item | Owner | Due |
| - | ---- | ---- | ----- | --- |
| A-1 | Assumption | Indoor lighting from the LED ring is consistent enough for the REQ-02 accuracy target. | Evan Heidenreich | 2026-11-04 |
| A-2 | Assumption | Players and clients are on the same local network as the Board Controller. | Nicholas Rigg | 2026-11-04 |
| A-3 | Assumption | Two cameras are enough to resolve the Segment of darts that overlap or sit close together. | Jacob Curtis | 2026-11-11 |
| Q-1 | Open question | Is 95% Segment accuracy achievable on the Dell 760 within the 2.0 s latency budget? | Evan Heidenreich | 2026-11-11 |
| Q-2 | Open question | How do we handle bounce-outs and darts that fall off the Board? | Jacob Curtis | 2026-11-11 |
| Q-3 | Open question | How is a session token issued to a Guest? | Nicholas Rigg | 2026-11-04 |
