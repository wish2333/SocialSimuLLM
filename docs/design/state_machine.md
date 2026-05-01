# State Machine Definitions

> Version: 3.1
> Last Updated: 2026-05-01
> Status: Active

---

## 1. Agent State Machine

### 1.1 Overview

Each agent in the simulation follows a state machine that governs its behavior throughout the simulation loop. The agent transitions between states based on the current global time and simulation events.

### 1.2 States

| State | ID | Description | Entry Action |
|-------|----|-------------|---------------|
| IDLE | S1 | Agent is waiting for next time increment | None |
| DAILY_PLANNING | S2 | Agent is generating daily plans | Call `daily_planning()` |
| HOURLY_PLANNING | S3 | Agent is generating hourly plan | Call `hourly_planning()` |
| ACTION_EXECUTION | S4 | Agent is executing planned action | Call `execute_action()` |
| LOCATION_RATING | S5 | Agent is rating locations | Call `rate_locations()` |
| MOVING | S6 | Agent is moving to new location | Call `move()` |
| IMPRESSION_FORMATION | S7 | Agent is forming impressions | Call `form_impression()` |
| REFLECTION | S8 | Agent is reflecting on the day | Call `form_reflection()` |
| MEMORY_UPDATE | S9 | Agent's memory is being updated | Call `memory.add_experience()` |

### 1.3 State Transition Diagram

```
                    +-------------------+
                    |                   |
                    |      IDLE         |
                    |                   |
                    +--+-----+----+---+
                       |     |    |
        (new day) ----+     |    +---- (new hour) ----> +-------------------+
                       |    |                        |   HOURLY_PLANNING  |
                       v    |                        |   (S3)             |
            +-------------------+                    +--------+----------+
            |                   |                             |
            | DAILY_PLANNING   |                             v
            | (S2)             |                    +-------------------+
            +--------+----------+                    |                   |
                     |                               |  ACTION_EXECUTION |
                     v                               |  (S4)             |
            +-------------------+                    +--------+----------+
            |                   |                             |
            |  MEMORY_UPDATE    |<---------------------------+ (after action)
            |  (S9)             |
            +--------+----------+
                     |
                     v
            +-------------------+       +-------------------+
            |                   |       |                   |
            |    IDLE           |<------|  LOCATION_RATING  |
            |  (S1)           |       |  (S5)             |
            +--+-----+----+---+       +--------+----------+
               |     |    |                        |
    (new hour) |    |    +-- (new hour) -------+
               |    |
               |    v
               |  +-------------------+       +-------------------+
               |  |                   |       |                   |
               +->|  IMPRESSION      |------>|  MEMORY_UPDATE    |
                  |  FORMATION       |       |  (S9)             |
                  |  (S7)             |       +--------+----------+
                  +--------+----------+                |
                           |                           |
                           v                           v
                  +-------------------+       +-------------------+
                  |                   |       |                   |
                  |     IDLE         |<------|  MOVING           |
                  |  (S1)             |       |  (S6)             |
                  +-------------------+       +-------------------+

            (end of day)
                  +-------------------+
                  |                   |
                  |   REFLECTION      |------> (to IDLE)
                  |   (S8)             |
                  +-------------------+
```

### 1.4 Transition Table

| Current State | Trigger | Condition | Next State | Action |
|--------------|---------|-----------|------------|--------|
| IDLE (S1) | global_time is 08:00 | new_day == True | DAILY_PLANNING (S2) | `daily_planning()` |
| IDLE (S1) | minutes == ":00" | new_hour == True | HOURLY_PLANNING (S3) | `hourly_planning()` |
| IDLE (S1) | minutes != ":00" | new_hour == False | ACTION_EXECUTION (S4) | `execute_action()` |
| DAILY_PLANNING (S2) | planning complete | Always | MEMORY_UPDATE (S9) | `memory.add_experience(plan)` |
| MEMORY_UPDATE (S9) | after daily plan | new_day == True | HOURLY_PLANNING (S3) | `hourly_planning()` |
| MEMORY_UPDATE (S9) | after hourly plan | new_hour == True | LOCATION_RATING (S5) | `rate_locations()` |
| MEMORY_UPDATE (S9) | after action | new_hour == False | ACTION_EXECUTION (S4) | `execute_action()` |
| HOURLY_PLANNING (S3) | planning complete | Always | ACTION_EXECUTION (S4) | `execute_action()` |
| ACTION_EXECUTION (S4) | action complete | Always | MEMORY_UPDATE (S9) | `memory.add_experience(action)` |
| LOCATION_RATING (S5) | rating complete | Always | MOVING (S6) | `move(highest_rated)` |
| MOVING (S6) | movement complete | Always | IMPRESSION_FORMATION (S7) | `form_impression()` |
| IMPRESSION_FORMATION (S7) | impression complete | Always | MEMORY_UPDATE (S9) | `memory.add_experience(impression)` |
| MEMORY_UPDATE (S9) | after impression | Always | IDLE (S1) | Wait for next tick |
| IDLE (S1) | global_time is 08:00 (next day) | new_day == True | REFLECTION (S8) | `form_reflection()` |
| REFLECTION (S8) | reflection complete | Always | MEMORY_UPDATE (S9) | `memory.add_experience(reflection)` |
| MEMORY_UPDATE (S9) | after reflection | Always | IDLE (S1) | Wait for next day |

### 1.5 Time-Driven Transitions

The simulation uses a global time that increments by 10 minutes each loop. Transitions are driven by time checks:

| Time Check | Function | Returns True When | Triggers |
|------------|----------|-------------------|----------|
| `if_new_day(global_time)` | Checks if time is "08:00" | Start of new day | DAILY_PLANNING, REFLECTION (previous day) |
| `if_new_hour(global_time)` | Checks if minutes are ":00" | Start of new hour | HOURLY_PLANNING, LOCATION_RATING, IMPRESSION_FORMATION |

---

## 2. Memory State Machine

### 2.1 Overview

The Memory class manages the lifecycle of experiences stored for each agent.

### 2.2 Memory States

| State | ID | Description |
|-------|----|-------------|
| EMPTY | M1 | No experiences stored |
| ACTIVE | M2 | Experiences being added and retrieved |
| PERSISTED | M3 | Experiences saved to JSON and SQLite |
| RETRIEVED | M4 | Experiences fetched for agent use |

### 2.3 Memory Transition Diagram

```
+-------------------+
|                   |
|     EMPTY         |
|     (M1)           |
+-------------------+
        |
        | add_experience()
        v
+-------------------+       +-------------------+
|                   |       |                   |
|     ACTIVE        |------>|    PERSISTED      |
|     (M2)           | save  |    (M3)           |
+-------------------+       +-------------------+
        |                           |
        | get_*()                   | load_*()
        v                           v
+-------------------+       +-------------------+
|                   |       |                   |
|    RETRIEVED      |       |     EMPTY         |
|    (M4)           |       |     (M1)           |
+-------------------+       +-------------------+
```

### 2.4 Experience Type State

Each experience has a type that determines how it is processed:

| Type | Processing |
|------|-------------|
| `plan` (priority 2-3) | Added to JSON only (daily:3, hourly:2) |
| `action` (priority 1-9) | Added to JSON + embeddings to SQLite, propagated to other agents at same location |
| `thought` (priority 4 or 7) | Added to JSON only (impression:4, reflection:7) |
| `event` (priority 9) | Added to ALL agents' JSON memories |

---

## 3. Simulation Loop State Machine

### 3.1 States

| State | ID | Description |
|-------|----|-------------|
| INITIALIZING | L1 | Loading project data, creating agents |
| RUNNING | L2 | Main simulation loop executing |
| PAUSED | L3 | Waiting for user input (not implemented) |
| SUMMARIZING | L4 | Generating daily summary |
| SAVING | L5 | Persisting state to disk |
| COMPLETED | L6 | Simulation finished |

### 3.2 Transition Diagram

```
+-------------------+
|                   |
|  INITIALIZING     |----> (error) ----> TERMINATED
|  (L1)             |
+-------------------+
        |
        | success
        v
+-------------------+       +-------------------+
|                   |       |                   |
|     RUNNING       |------>|    SUMMARIZING    |
|     (L2)           |       |    (L4)           |
+--------+----------+       +-------------------+
         |                           |
         | end of repeat             | summary done
         v                           v
+-------------------+       +-------------------+
|                   |       |                   |
|    SAVING        |<------|     RUNNING       |
|    (L5)           |       |     (L2)           |
+-------------------+       +-------------------+
         |
         | done
         v
+-------------------+
|                   |
|   COMPLETED       |
|   (L6)             |
+-------------------+
```

---

## 4. Location State Machine

### 4.1 Location States

| State | ID | Description |
|-------|----|-------------|
| UNVISITED | L1 | No agent has visited |
| OCCUPIED | L2 | One or more agents present |
| RATED | L3 | Agents have rated this location |

### 4.2 Transition Table

| Current State | Trigger | Next State | Action |
|--------------|---------|------------|--------|
| UNVISITED (L1) | Agent rates location | RATED (L3) | Store rating |
| UNVISITED (L1) | Agent moves in | OCCUPIED (L2) | Add to occupancy |
| OCCUPIED (L2) | Agent moves out | UNVISITED (L1) | Remove from occupancy |
| OCCUPIED (L2) | Agent rates location | RATED (L3) | Store rating |
| RATED (L3) | New rating cycle | RATED (L3) | Update rating |
| RATED (L3) | Agent moves in | OCCUPIED (L2) | Add to occupancy |
