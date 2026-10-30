# DigiDarts — Technical Specification Document

**Team:** Evan Heidenreich, Nick Rigg, Jacob Curtis
**Advisor:** Dr. William Hawkins III

---

## 1. Version and Change Log

| Version | Date | Change | Author |
| ------- | ---- | ------ | ------ |
| 0.1 | 2026-10-29 | First consolidation of D0, D1 and D2 into one specification. | Team |

## 2. Architecture Summary

DigiDarts uses a pipeline (data-flow) architecture (D0 Part 6). The major components are the Dart Detector, Score Mapper, Game Logic (with its TurnManager), User Interface and Database.

**Deployment.** Everything except the database runs on one mini-PC with Ubuntu: two Arducam USB cameras plug into it, a Python 3 process runs the Detector, Mapper and Game Logic, and the same process serves the UI as a local web page shown full-screen in Chromium on an HDMI display. The database is Supabase (hosted PostgreSQL), external to the mini-PC. A local SQLite offline write queue sits between Game Logic and Supabase.

**Data flow.** Camera frames (I1) go to the Dart Detector, which emits a DartDetection with a board position in millimeters (I2). The Score Mapper turns that into a ScoredDart (I3). Game Logic applies the game rules, sends state to the UI and receives player commands back (I4, two-way), and writes each throw to the queue, which uploads to Supabase (I5). The UI reads stats from Supabase (I6) and draws to the display (I7). Unconfirmed and corrected darts are also written to a local retraining store. Nothing on the scoring path (I1–I4) waits for the internet, which is how NFR-01 is met even when Supabase is slow.

## 3. Interfaces and Data Formats

### 3.1 Component boundaries

| ID | From -> To | Inputs / Outputs | Format | Protocol | Error behavior |
| -- | ---------- | ---------------- | ------ | -------- | -------------- |
| I1 | Cameras -> Dart Detector | Video frames + ms timestamp per camera; saved calibration (two 3 × 3 matrices) | Raw frames 1920 × 1200 @ 50 fps | USB (UVC) via OpenCV | No frame for > 1 s -> E_CAMERA_LOST; switch to single-camera mode; both lost -> manual entry. No calibration -> E_NOT_CALIBRATED. |
| I2 | Dart Detector -> Score Mapper | DartDetection (3.2) | JSON object (Python dict validated by pydantic) | In-process function call `next_detection()` | E_NO_DART, E_CAM_DISAGREE, E_AMBIGUOUS_SCENE returned to Game Logic, which asks for manual entry. > 15% board change -> nothing emitted, reference reset. |
| I3 | Score Mapper -> Game Logic | ScoredDart (3.2) | JSON object | In-process function call `score_dart()` | E_BAD_INPUT: input discarded and logged; player enters the dart by hand. Duplicate seq ignored. |
| I4 | Game Logic <-> User Interface | Out: game state snapshot. In: player commands. | JSON messages (3.3) | Local HTTP API (3.5) | UI disconnected -> Game Logic keeps state; UI reloads full snapshot on reconnect. Invalid command -> 400 with error code; state unchanged. |
| I5 | Game Logic -> Database | Game, game_player and throw rows | JSON over REST (3.4, 3.6) | HTTPS to Supabase via local SQLite queue | Timeout or 5xx -> stay queued, retry with backoff; UI shows "Not synced". 4xx -> logged, not retried, warning shown. Duplicate throw_id ignored as success. |
| I6 | Database -> User Interface | Player stats, throw history | JSON arrays (3.6) | HTTPS GET (Supabase REST) | Unreachable or paused -> stats shown as unavailable; game play unaffected. |
| I7 | User Interface -> Display | Rendered page | Video signal | HDMI / DisplayPort | No display -> game and UI keep running. |
| R1 | Game Logic -> Retraining store | Image + detection + confirmed value | PNG + JSON file pair (3.7) | Local file write | Disk full -> logged, warning on status screen; game continues. |

### 3.2 DartDetection (I2) and ScoredDart (I3)

```jsonc
// DartDetection, schema_version 1
{ "v": 1, "seq": 42, "t": "2026-10-01T21:14:32.105Z",
  "x_mm": 3.4, "y_mm": 102.8,   // float, −250 to 250, +x right, +y up
  "confidence": 0.91,           // 0 to 1; capped at 0.6 with one camera
  "cameras_used": ["A", "B"],
  "agreement_mm": 2.1 }         // null with one camera

// ScoredDart = DartDetection fields plus:
{ "segment": 20,                // 0 (miss), 1–20, or 25 (bull)
  "multiplier": 3,              // 0–3
  "points": 60,                 // 0–60
  "boundary": false }
```

Rules: rings by radius in mm (≤ 6.35 inner bull, ≤ 15.9 outer bull, ≤ 99 single, ≤ 107 triple, ≤ 162 single, ≤ 170 double, > 170 miss); segment from the angle clockwise from the top (D1 Algorithm 2). Adding an optional field is non-breaking; removing, renaming, retyping or changing units needs a new `v`.

### 3.3 I4 messages (Game Logic ↔ UI)

State snapshot (Game Logic → UI), sent on every change and on connect:

```jsonc
{ "type": "state", "game_id": "g-20261001-0042", "game_type": "501",
  "status": "in_progress", "double_out": true,
  "players": [{ "player_id": "p-0007", "name": "Evan", "remaining": 141 }],
  "current_index": 0, "turn": 4, "dart": 2,
  "turn_darts": [{ "segment": 20, "multiplier": 3, "points": 60, "source": "camera" }],
  "pending": null,   // or a ScoredDart awaiting confirmation (REQ-13)
  "message": null,   // "BUST", "UNCONFIRMED", "REMOVE DARTS", "WINNER"
  "status_flags": { "camera_A": "ok", "camera_B": "lost",
                    "calibrated": true, "db": "not_synced" } }
```

Commands (UI → Game Logic): `start_game`, `confirm_dart`, `manual_dart`, `next_player`, `undo_dart`, `abandon_game` (endpoints in §3.5).

### 3.4 Database schema (Supabase PostgreSQL)

| Table / view | Columns | Keys and rules |
| ------------ | ------- | -------------- |
| `player` | `player_id` text, `display_name` text not blank | PK `player_id` |
| `games` | `game_id` text, `game_type` text (301, 501, cricket), `double_out` bool, `status` text, `started_at`, `ended_at` timestamptz, `winner_id` text | PK `game_id`; FK `winner_id` → `game_players` of this game |
| `game_players` | `game_id`, `player_id` text, `turn_order` int ≥ 1 | PK (`game_id`, `player_id`); unique (`game_id`, `turn_order`) |
| `throws` | `throw_id` uuid, `game_id`, `player_id` text, `turn` int ≥ 1, `dart` int 1–3, `segment` int, `multiplier` int 0–3, `points` int 0–60, `remaining` int ≥ 0, `is_bust` bool, `x_mm`, `y_mm` real, `confidence` real, `source` text (camera/manual), `thrown_at` timestamptz | PK `throw_id`; FK (`game_id`, `player_id`) → `game_players`; unique (`game_id`, `player_id`, `turn`, `dart`); index (`player_id`, `thrown_at`) |
| `player_stats` (view) | `player_id`, `games_played`, `games_won`, `darts_thrown`, `three_dart_avg`, `highest_turn` | Computed from `throws` and `games`, never stored |

### 3.5 Local API (I4), served by FastAPI on the mini-PC

| Method & path | Input | Success | Errors |
| ------------- | ----- | ------- | ------ |
| GET `/ws` (WebSocket) | — | Stream of state snapshots | Closed → UI attempts reconnect |
| POST `/api/game` | `game_type`, `double_out`, `players` [1–8 `player_id`] | 201, snapshot | 400 E_BAD_INPUT (unknown type, double-out on Cricket, blank name, > 8 players) |
| POST `/api/confirm` | `sequence` | 200, snapshot | 409 no pending dart with that sequence |
| POST `/api/manual` | `segment`, `multiplier` | 200, snapshot | 400 impossible value |
| POST `/api/next` | — | 200, snapshot | 409 game not in progress |
| POST `/api/undo` | — | 200, snapshot | 409 no dart this turn |
| POST `/api/players` | `display_name` | 201, `player_id` | 400 blank name |
| GET `/api/status` | — | 200, `status_flags` (REQ-11) | — |

### 3.6 Supabase REST endpoints (I5, I6)

Base URL `https://<project-ref>.supabase.co/rest/v1`. Every request carries the project API key and a Supabase Auth token.

| Request | Purpose | Success | Errors |
| ------- | ------- | ------- | ------ |
| POST `/player` | Create player | 201 | 400, 401, 403, 409 duplicate id |
| POST `/games`, POST `/game_players` | Create game and players | 201 | 400 bad type/field; 401; 403; 409 duplicate id or turn order |
| POST `/throws` (`Prefer: resolution=ignore-duplicates`) | Record a throw | 201; repeated `throw_id` = success | 400 out of range; 401; 403; 409 player not in game. Timeout/5xx -> requeue. |
| PATCH `/games?game_id=eq.<id>` | Finish game | 204 | 400; 401; 403; 409 winner not in game |
| GET `/player_stats?player_id=eq.<id>` | Stats | 200, 0 or 1 rows | 400; 401 |
| GET `/throws?player_id=eq.<id>&order=thrown_at.desc&limit=<n>` | History | 200, array | 400; 401 |

### 3.7 Retraining store (R1)

For each sample, `retrain/<throw_id>.png` (crop around the tip from each camera) and `retrain/<throw_id>.json` with the original DartDetection, the confirmed segment and multiplier, and reason (`low_confidence`, `corrected`, `disagree`). Location (local disk or Supabase Storage) is open question OQ-04.

## 4. Technology Stack

| Layer | Choice | Justification |
| ----- | ------ | ------------- |
| Hardware | Mini-PC (CPU only) | CON-01; more power than a Raspberry Pi for two live video streams (NFR-01). |
| Cameras | Two Arducam USB cameras | CON-02; two angles needed for accuracy and occlusion (NFR-02, REQ-02, NFR-03). |
| Operating system | Ubuntu Linux | CON-03; less background load leaves CPU for vision (NFR-01). |
| Language | Python 3 | One language for all components; libraries for vision and the database (REQ-01–REQ-04). |
| Computer vision | OpenCV + NumPy | Compiled image processing fast enough on CPU (NFR-01, CON-01); difference + homography needs no training data (CON-05). |
| Payload validation | pydantic | Enforces I2/I3 types and ranges (REQ-03, E_BAD_INPUT handling). |
| Local API | FastAPI (WebSocket + HTTP) | Pushes state to the UI as it changes (REQ-05, NFR-01) and accepts commands (REQ-13). Chosen over Flask in D1 for built-in WebSockets. |
| User interface | Web page in Chromium kiosk mode; framework TBD (OQ-05) | Runs locally on the mini-PC (NFR-01); web UI suited to large, readable screens (NFR-06). |
| Database | Supabase (hosted PostgreSQL) | Stats readable from other devices (REQ-10); SQL view for stats (REQ-07); foreign keys and unique keys enforce one record per dart (REQ-06). |
| Auth | Supabase Auth + row-level security | Named security mechanism (NFR-05). |

## 5. Known Constraints

| ID | Constraint | Rules out / forces |
| -- | ---------- | ------------------ |
| CON-01 | One mini-PC, no GPU | Rules out a neural-network detector for this release; forces OpenCV image differencing on the CPU and a 960 × 600 working resolution if 1920 × 1200 misses NFR-01. |
| CON-02 | Two funded Arducam cameras | Rules out adding cameras; forces single-camera mode (confidence cap 0.6) when one is blocked or lost. |
| CON-03 | Ubuntu Linux | Rules out Windows-only libraries and drivers; forces the team to work on the Linux command line. |
| CON-04 | Supabase free plan (500 MB, pauses after 7 days idle) | Forces the offline write queue, a "stats unavailable" state in the UI, and waking the project before demos; limits storing retraining images in the cloud (OQ-04). |
| CON-05 | No labeled images at start | Rules out a trained model at launch; forces REQ-12 so labeled data accumulates during play. |

## 6. Traceability Matrix

| Req ID | Description | Design Component (D0/D1/D2) | Status | Test Case |
| ------ | ----------- | --------------------------- | ------ | --------- |
| REQ-01 | Capture and pair frames from two cameras | D0 I1; D1 Algorithm 1 step 1, `next_detection` | Designed | TC-01 |
| REQ-02 | Detect each new dart once, with confidence | D0 Dart Detector; D1 Algorithm 1 steps 2–5; D2 EC03, EC17, EC18 | Designed | TC-02 |
| REQ-03 | Position -> segment, multiplier, points; boundary rule | D0 Score Mapper; D1 Algorithm 2, `score_dart` | Designed | TC-03 |
| REQ-04 | 301/501 rules, bust, checkout | D2 Algorithm 3, TurnManager, Game Logic data model, Figure D2-1; EC05 | Designed | TC-04 |
| REQ-05 | Display dart, turn total, scores, current player | D0 User Interface; D2 Figure D2-2; I4 snapshot (3.3) | Designed | TC-05 |
| REQ-06 | Save each dart exactly once | D1 `throws` table, POST `/throws`, `throw_id`; D2 EC14 | Designed | TC-06 |
| REQ-07 | Player statistics | D1 `player_stats` view, GET `/player_stats`; D2 EC13 | Designed | TC-07 |
| REQ-08 | Unique player IDs, blank names rejected | D1 `player` table; D2 Rationale 6, EC11; POST `/api/players` | Designed | TC-08 |
| REQ-09 | Cricket | D2 Algorithm 4, marks, EC21 | In progress | TC-09 |
| REQ-10 | Stats from another device, read-only | D0 Decision 3; D1 row-level security | Designed | TC-10 |
| REQ-11 | Status and warnings for the owner | D1 E_CAMERA_LOST, E_NOT_CALIBRATED; D2 EC19, EC20; GET `/api/status` | Planned | TC-11 |
| REQ-12 | Save retraining samples | D0 Game Logic; retraining store R1 (3.7) | Planned | TC-12 |
| REQ-13 | Unconfirmed darts and manual entry | D2 Figure D2-1 "Awaiting Confirm", EC01, EC02, EC08, EC22; POST `/api/confirm`, `/api/manual` | Designed | TC-13 |
| NFR-01 | Score shown within 2 s for ≥ 95% of darts | D1 Algorithm 1 target; local scoring path I1–I4 | Designed | TC-14 |
| NFR-02 | ≥ 95% correct segment and multiplier | D1 Algorithms 1 and 2 (8 mm agreement, boundary flag) | Designed | TC-15 |
| NFR-03 | Continue on one camera | D1 single-camera mode; D2 EC20, Figure D2-1 "Camera Disconnect" | Designed | TC-16 |
| NFR-04 | No data lost offline | D1 SQLite queue; D2 EC16, EC24 | Designed | TC-17 |
| NFR-05 | Auth token and row-level security | D1 Supabase Auth, row-level security | In progress | TC-18 |
| NFR-06 | Start game ≤ 60 s, correct dart ≤ 10 s | D2 Figure D2-2, SetupScreen, Scoreboard | Planned | TC-19 |
| CON-01 | One mini-PC, no GPU | D0 Decision 2; D1 Algorithm 1 §4 | Designed | TC-14 |
| CON-02 | Two Arducam cameras | D0 Decisions 1 and 4 | Designed | TC-16 |
| CON-03 | Ubuntu Linux | D0 Decision 2 | Designed | TC-01 |
| CON-04 | Supabase free plan limits | D1 technology choices; SQLite queue; D2 EC10, EC16 | Designed | TC-17 |
| CON-05 | No labeled training data | D1 Algorithm 1 §4; REQ-12 retraining store | Designed | TC-12 |

## 7. Advisor Review Record

This section must record a real meeting. Fill it in after the review; the entries below are the structure only.

| Field | Entry |
| ----- | ----- |
| Advisor | Dr. William Hawkins III |
| Date of review | [TEAM: date] (drafts sent [TEAM: date, at least 3 days before the deadline]) |
| Attendees | [TEAM: names] |
| Materials brought | Both drafts and the traceability matrix |
| Discussed | [TEAM: notes] |

| # | Feedback | Change made | Document and version |
| - | -------- | ----------- | -------------------- |
| 1 | [TEAM] | [TEAM] | [TEAM] |
| 2 | [TEAM] | [TEAM] | [TEAM] |
