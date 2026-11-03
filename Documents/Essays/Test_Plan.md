# Must Requirements by Category

## 1. Functionality

  -----------------------------------------------------------------------
  Requirement ID                      Requirement
  ----------------------------------- -----------------------------------
  REQ-03                              The system shall score 501 and 301
                                      Games for 1 to 4 Players, applying
                                      Bust and double-out Checkout rules,
                                      and shall let a user advance the
                                      Turn manually.

  REQ-06                              The system shall let a user create,
                                      select, and delete Player profiles
                                      and shall support Guest play
                                      without a profile.

  REQ-08                              The system shall let a user correct
                                      or undo the most recent Throw in no
                                      more than 3 taps, with the Game
                                      state recalculated correctly.

  REQ-10                              The system shall provide a guided
                                      Calibration that a Host can
                                      complete in 5 minutes or less and
                                      that yields a pass/fail result.

  NFR-03                              The API Server shall require a
                                      valid session token on every
                                      state-changing request and shall
                                      reject unauthenticated requests
                                      with HTTP 401.
  -----------------------------------------------------------------------

**Metric:** 100% of Must requirements pass their assigned tests.

**Target Threshold:** All required functions work correctly.

**How It Is Measured:** Run test cases and compare results with expected
results.

## 2. Performance

  -----------------------------------------------------------------------
  Requirement ID                      Requirement
  ----------------------------------- -----------------------------------
  REQ-01                              The system shall detect each dart
                                      that lands on the Board and report
                                      its Segment within 2.0 seconds of
                                      the dart coming to rest.

  REQ-07                              The system shall update the
                                      on-screen scoreboard within 1.0
                                      second of a Throw being scored, on
                                      every connected client.

  NFR-01                              The system shall show a scored
                                      Throw on the scoreboard within 2.0
                                      seconds of the dart coming to rest,
                                      at the 95th percentile, with 4
                                      clients connected.
  -----------------------------------------------------------------------

**Metric:** Main operations complete within the required time limits.

**Target Threshold:** 1.0--2.0 seconds, depending on the operation.

**How It Is Measured:** Measure the time required to complete
operations.

## 3. Reliability

  -----------------------------------------------------------------------
  Requirement ID                      Requirement
  ----------------------------------- -----------------------------------
  NFR-05                              The system shall complete a 3-hour
                                      Session with no crash and no
                                      unrecoverable fault in at least 9
                                      of 10 test Sessions.

  -----------------------------------------------------------------------

**Metric:** No critical crashes during testing.

**Target Threshold:** At least 9 out of 10 successful 3-hour test
sessions.

**How It Is Measured:** Run repeated tests and record errors or crashes.

## 4. Usability

  -----------------------------------------------------------------------
  Requirement ID                      Requirement
  ----------------------------------- -----------------------------------
  REQ-06                              The system shall let a user create,
                                      select, and delete Player profiles
                                      and shall support Guest play
                                      without a profile.

  REQ-08                              The system shall let a user correct
                                      or undo the most recent Throw in no
                                      more than 3 taps, with the Game
                                      state recalculated correctly.

  REQ-10                              The system shall provide a guided
                                      Calibration that a Host can
                                      complete in 5 minutes or less and
                                      that yields a pass/fail result.
  -----------------------------------------------------------------------

**Metric:** At least 80% of test users can complete assigned tasks.

**Target Threshold:** At least 80% task completion.

**How It Is Measured:** Observe users completing tasks and collect
feedback.

## 5. Accuracy

  -----------------------------------------------------------------------
  Requirement ID                      Requirement
  ----------------------------------- -----------------------------------
  REQ-02                              The system shall report the correct
                                      Segment for at least 95% of Throws
                                      in a 200-Throw test set covering
                                      all 20 numbers and all multipliers
                                      under standard lighting.

  -----------------------------------------------------------------------

**Metric:** At least 95% correct results.

**Target Threshold:** 95% accuracy across 200 throws.

**How It Is Measured:** Compare system results against known correct
results.

------------------------------------------------------------------------

**Note:** REQ-06, REQ-08, and REQ-10 appear in both Functionality and
Usability because they involve both system capabilities and how users
interact with the system. NFR-03 is categorized under Functionality
because it describes required system behavior, although it is
specifically a security requirement.
