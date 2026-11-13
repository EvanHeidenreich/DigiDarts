# Ethics & Responsible-Use Statement

**Team Members:**
- Evan Heidenreich
- Jacob Curtis
- Nicholas Rigg

**Advisor:** Dr. William Hawkins III

## Privacy Summary

| Data item | Source | Purpose | Consent | Storage | Access | Retention |
|---|---|---|---|---|---|---|
| Camera frames of the board | 2x Arducam AR0234 | Detect dart positions | Posted notice at the board; use of the board implies consent. | Processed in memory; CV component only | Kept in the running program | Once processed the frames are deleted. |
| Dart coordinates and scores | CV pipeline | Score the game | Part of play | Supabase | Game server, authenticated players | Kept with game history; deleted with account |
| Player display name | Typed by player at signup | Identify players in games and stats | Player enters it and accepts the notice at signup | Supabase | Logged-in players; admin | Until account deletion or project end |
| Game history and stats | Game server | Player stats pages | Part of play | Supabase | The player | Until account deletion |
| Server and device logs | Web server, CV service | Debugging | Disclosed in this document | Local log files | Team members | In server until deleted |

## Security Summary

### Gaps addressed

- **Default credentials:** Supabase DB password is the same as when it was set, but we will be sure to begin rotating it
- **Unauthenticated endpoints:** All FastAPI routes except /health and signup require a verified Supabase JWT; the CV service uses a device API key.
- **Secrets in source control:** .env is git-ignored.

### Mechanisms

| Mechanism | What we use |
|---|---|
| Authentication | Supabase Auth, JWT checked by FastAPI] |
| Token lifetime | Access N min; refresh N days |
| Secret storage | Host env settings; local .env |
| HTTPS | Enforced by host |
| Rate limiting | N req/min on login and score endpoints |

### Git history search

On 11/10/2026, we ran `gitleaks detect --source . --log-opts=--all -v` across 24 commits. Result: no leaks found

```
gitleaks
4:53PM INF 24 commits scanned.
4:53PM INF scanned ~326275 bytes (326.27 KB) in 954ms
4:53PM INF no leaks found
```

### Self-audit

| Gap | Question | Answer |
|---|---|---|
| Default credentials | Is any default DB or dashboard login still in use? | [No; password rotated on date.] |
| Default credentials | Does the board keep a default login? | [No; SSH key-only.] |
| Unauthenticated endpoints | Does every non-public route verify the token server-side? | [Yes; get_current_user in file:line, 401 without token.] |
| Unauthenticated endpoints | What stops fake dart coordinates? | [Device API key; 401/403 without it.] |
| Secrets in source control | Did the history search find secrets? | No findings |
| Secrets in source control | Is .env ignored? | [Yes; .gitignore line N.] |

## Licensing Summary

| Name | Version | License | Permissive / Copyleft | Obligation |
|---|---|---|---|---|
| OpenCV | Version 4.10.0 | Apache-2.0 | Permissive | Keep the license text and copyright notices when redistributing and state any changes you make to OpenCV itself. |
| Supabase | Version 2.115.0 | Apache-2.0 | Permissive | Keep license and copyright notices if you redistribute the code. If you use the hosted service, you also agree to Supabase's Terms of Service. |
| FastAPI | Version 0.136.3 | MIT | Permissive | Keep the MIT copyright and license notice in copies of the code you distribute. |
| Vite | Version 8.3.2 | MIT | Permissive | Keep the MIT copyright and license notice in copies of the code you distribute. |

## Attribution List

| Type | Item | Used For | Source/URL |
|---|---|---|---|
| Library | OpenCV | Dart detection reference-line differencing and Huber line fitting | https://github.com/opencv/opencv-python |
| Library | NumPy | Image arrays and numeric work | https://github.com/numpy/numpy |
| Library | FastAPI | Back-end web API | https://github.com/fastapi/fastapi |
| Library | Supabase-py | Python Client for the database | https://github.com/supabase/supabase-py |
| Service | Supabase | Database and auth for players, games, & stats | https://supabase.com/ |
| Library | Vite | Front-end build tool and dev server for the app / website | https://github.com/vitejs/vite |

## AI-Use Disclosure

Generative AI tools may be used for drafting and code assistance but not for the design decisions or written analysis that are assessed in this course.

| Tool | Used By | Task | Column | How verified |
|---|---|---|---|---|
| ClaudeAI | Team | Writing drafts/structures to edit | Generally OK | The team reviews and makes additions and changes. |
| ClaudeAI | Evan | Assisting in Dart Detection with creating test cases and | Generally OK | Nick and Evan verify dart detection by running tests and confirming the detection showed the correct landing. |
| ClaudeAI | Evan | Help validate math for calibration and board overlay | Generally OK | Verified with simple math calculations and the board overlay was equal to the actual Dartboard |
