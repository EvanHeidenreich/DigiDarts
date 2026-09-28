# DigiDarts – User Stories and Use Cases

**Team Members:** Evan Heidenreich, Nick Rigg, Jacob Curtis

## Overview

DigiDarts is an automated dartboard that utilizes two cameras and computer vision to capture darts thrown at a dartboard. Which will detect the dart, score it, and send it to a frontend app/website. Players can play an assortment of dartboard games such as 501, 301, Cricket, and Around-The-World while also storing players' stats in Supabase.

## Stakeholder Map

| Category | Stakeholder | Explanation |
|----------|-------------|-------------|
| Primary | Casual Players | Open the app and throw darts. They need every dart scored correctly and efficiently, with no errors. |
| Primary | Competitive Players | Plays competitively and wants a record of results and personal stats. |
| Secondary | Dart Board Owner | Owner of dart board must maintain product and fix or report any issues with board. |
| Hidden | Database | Database of players and personal stats that get updated regularly as the user plays. |
| Hidden | Model Retraining | Images need to be labeled with correct segments, whenever a dart is mis-scored or corrected. If the system doesn't capture them, then the model cannot improve. |

## INVEST Check

| Story | I | N | V | E | S | T |
|-------|---|---|---|---|---|---|
| US-1 | Y | Y | Y | Y | Y | Y |
| US-2 | Y | Y | Y | Y | Y | Y |
| US-3 | Y | Y | Y | Y | Y | Y |
| US-4 | Y | Y | Y | Y | Y | Y |
| US-5 | Y | Y | Y | Y | Y | Y |

## User Stories

### US-1: Primary Casual Players

- As a casual player, I want each dart thrown score recorded automatically as soon as it lands, so that I can keep throwing darts without stopping to manually add scores or updating the scoreboard.

### US-2: Primary Competitive Players

- As a competitive player, I want my wins, losses, and stats saved across every game I play, so I can see improvements in my gameplay overtime.

### US-3: Secondary Dart Board Owner

- As a Dart Board Owner, I want to identify when the dartboard or scoring system has an issue, such as a broken camera, bad lighting, network or computer problems. So that I can fix the problem and keep the board operational.

### US-4: Hidden Database

- As the DigiDarts database, I want to store player scores and game results, so that the player statistics can be retrieved and updated for future games and so they can review stats for themselves and other players.

### US-5: Hidden Model Retraining

- As the developer who retrains the dart-detection model, I want every dart a player corrects or the system scores with low confidence to be saved with the camera image segment and the exact confirmed location so I can retrain the model on real mistakes and improve the model's accuracy.

## Use Cases

### UC-1: Score a Turn Automatically

**Primary actor:** Casual Players

**Secondary actors:**
- Computer Vision
- Database

**Main success flow:**

1. Player throws the first darts, which lands on the board.
2. System detects the new dart, identifies its segment and multiplier (Single, Double, or Triple).
3. Player throws the second dart.
4. System detects and scores second dart, then updates the turn total.
5. Player throws the third dart.
6. System scores the third dart, subtracts the turn total from the players' remaining score, displays the new remaining score, and prompts player to remove their darts.
7. Player removes all three darts from the board.
8. System detects the board is empty, saves the turn to the database, and makes it the next players turn.

**Alternate Flow A1: Bust**

- Branches from either step 2, 4, or 6. The turn would leave the players with a remaining score below 0.
- System communicates "BUST" and restores the score to its value at the start of the turn, as well as telling the player to remove the darts.
- Player removes the darts, and the flow resumes back at step 8 with the turn being saved as a bust.

**Alternate Flow A1: Checkout**

- Branches from either step 2, 4, or 6. A dart brings the remaining score to exactly 0. (For competitive the dart must land on a double). Casual just exactly 0.
- System declares Player A as the winner, ends the game, and saves the results to the database.
- System updates both players win/loss stats. Links to US-2 and US-4.

---

### UC-2: Computer Vision Detects Darts

**Primary actor:** Casual/Competitive Players

**Secondary actors:**
- Cameras
- Database

**Main success flow:**

1. Player throws a dart which lands on the board.
2. Both cameras capturing video of the board, and the system detects a new dart.
3. System calculates the position of the dart, mapping it to a segment as well as its multiplier (single, double, triple, or bull).
4. System sends result (segment, multiplier and score) to the game/application and displays it to the player.
5. System records data to Supabase (game, player, segment, multiplier, score, timestamp, etc.).

**Alternate Flow A1: Darts close together**

- Branches from step 2. A new dart lands really close to another dart (e.g. 1 dart width) on the board, blocking one of the two cameras' views.
- System utilizes the unobstructed camera's view to locate the new dart.
- System continues at step 3, not re-scoring the earlier dart.

**Alternate Flow A1: Position cannot be determined**

- Branches from step 3. The system's confidence in the segment is below a certain margin, or there is a disagreement between the two cameras.
- System display "Unconfirmed dart", possibly asking the player to select the segment which it landed on manually (within the UI of the application).
- Players choose a segment and multiplier.
- System scores the dart as the player entered, flagging the record as manual, continuing at step 4.

## Acceptance Criteria

### UC-1: Score a Turn Automatically

#### AC-1.1: Main Flow Single Dart

- **Given** a game of 501 darts, and status okay, Player A's remaining scoring is 260, and it's their first throw of their turn.
- **When** Player A throws a dart that lands on T20.
- **Then** within 2 seconds of the dart landing, the computer displays the dart as T20=60 and Player A's remaining score is 200.

#### AC-1.2: Main Flow Completed Turn

- **Given** Player A has thrown all three darts scoring a T20, 5, and 1 from a remaining score of 260.
- **When** Player A removes their 3 darts from the board.
- **Then:**
  - Within 2 seconds of the 3 darts removed from the board, the screen displays Player A's total score of their 3 dart throws, and their remaining score of the game being 194.
  - Supabase retains each dart throw and score.
  - Turn Player A's turn to Player B.

#### AC-1.3: Alternate Player Busts

- **Given** Player A's remaining score is 10.
- **When** Player A's darts score 5 and then Red Bullseye (50).
- **Then:**
  - Display shows "Bust".
  - Player A's score remains 10.
  - After dart(s) are removed, transition to Player B's turn.

#### AC-1.4: Exception Low-Confidence Detection

- **Given** a dart is detected with a low model confidence, say <.90.
- **When** the system processes that dart.
- **Then:**
  - The dart is marked unconfirmed; nothing is subtracted from the remaining players' score until they confirm it's correct.
  - After the corrected score is applied, save the correction record and image of the dartboard segment for retraining.

### UC-2: Computer Vision Detects Darts

#### AC-2.1: Main Flow Dart Detected and Recorded

- **Given** a 501 game in progress, both cameras connected, the board is empty, and Player A's turn.
- **When** Player A throws a dart that lands on T20.
- **Then:**
  - The model detects a dart on the board.
  - The model determines the location corresponding score within 2 seconds and displays the value of T20=60 on the screen.

#### AC-2.2: Alternate Flow, Darts are Close Together

- **Given** a dart is already on the board, say, 15 and the score was recorded.
- **When** another dart is thrown and lands right next to the original dart and a camera is being blocked by the original dart.
- **Then:**
  - The second dart is scored in its segment, using the unblocked camera, and displayed within 2 seconds.
  - The first dart record is unchanged, and exactly 1 new record is added.

#### AC-2.3: Exception Flow, Darts Position Cannot Be Determined

- **Given** a dart thrown by Player A is detected with model confidence <.90, or the cameras place in different segments.
- **When** the system processes that dart.
- **Then:**
  - Within 2 seconds the display shows, "Unconfirmed Dart," and 0 points are subtracted from Player A's remaining score.
  - Player A must validate the segment on the display either its correct or provide the correct segment and score. Once confirmed, Player A's score is update and the low confidence and image of dart location is saved for model retraining.
