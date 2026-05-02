# State Machine Definitions

## Simulation Step State Machine

Each 10-minute simulation step follows this state machine:

```
                    ┌──────────┐
                    │  START   │
                    │ (step N) │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ ADVANCE  │
                    │   TIME   │
                    └────┬─────┘
                         │
                    ┌────▼────────┐
                    │ DAY BOUNDARY│
                    │  (08:00?)   │──── Yes ──► DAILY_PLANNING
                    └────┬────────┘                   │
                         │ No                          │
                         ◄─────────────────────────────┘
                         │
                    ┌────▼────────┐
                    │   HOUR      │
                    │  BOUNDARY?  │──── Yes ──► HOURLY_PLANNING
                    └────┬────────┘                   │
                         │ No                          │
                         ◄─────────────────────────────┘
                         │
                    ┌────▼─────────┐
                    │    EXECUTE   │
                    │   ACTIONS    │
                    └────┬─────────┘
                         │
                    ┌────▼─────────┐
                    │   MOVEMENT   │
                    │  (rate+move) │
                    └────┬─────────┘
                         │
                    ┌────▼─────────┐
                    │  IMPRESSIONS │
                    │  (co-located)│
                    └────┬─────────┘
                         │
                    ┌────▼─────────┐
                    │  REFLECTION  │
                    │  CHECK       │
                    └────┬─────────┘
                         │
                ┌────────┴────────┐
                │                 │
           Triggered         Not Triggered
                │                 │
        ┌───────▼──────┐         │
        │  REFLECTION   │         │
        │  EXECUTE      │         │
        └───────┬──────┘         │
                │                 │
                └────────┬────────┘
                         │
                    ┌────▼─────────┐
                    │  GLOBAL      │
                    │  EVENTS      │
                    └────┬─────────┘
                         │
                    ┌────▼─────────┐
                    │  CHECKPOINT  │
                    │  (if N steps)│
                    └────┬─────────┘
                         │
                    ┌────▼─────────┐
                    │     END      │
                    │  (step N+1)  │
                    └──────────────┘
```

## Reflection Trigger State Machine

```
                 ┌──────────────────┐
                 │ reflection_check │
                 └────────┬─────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
     end_of_day?                  threshold?
       (22:00)              (importance >= 15)
            │                           │
            │                      ┌────▼────┐
            │                      │ Yes     │
            │                      └────┬────┘
            │                           │
            └────────┬──────────────────┘
                     │
                ┌────▼────┐
                │ reflect │
                │  _all() │
                └────┬────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼───┐ ┌────▼────┐ ┌────▼───┐
    │ daily  │ │ pattern │ │ social │
    │ always │ │>=2 dail │ │>=1 soc │
    └────┬───┘ └────┬────┘ └────┬───┘
         │          │           │
         │     Optional      Optional
         │          │           │
         └──────────┼───────────┘
                    │
              ┌─────▼──────┐
              │ Store as   │
              │MemoryEntry │
              │(reflection)│
              └────────────┘
```

## Memory Event Routing State Machine

```
           ┌──────────────────┐
           │ MemoryEntry.store│
           │   entry.event_type│
           └────────┬─────────┘
                    │
     ┌──────────┬──┴──┬──────────┬──────────┐
     │          │     │          │          │
  "action"  "plan" "thought"  "event"  "reflection"
     │          │     │          │          │
┌────▼────┐     │     │     ┌────▼────┐     │
│ Save to │     │     │     │ Save to │     │
│ acting  │     │     │     │ ALL     │     │
│ agent   │     │     │     │ agents  │     │
├─────────┤     │     │     ├─────────┤     │
│ Fan out │     │     │     │ (no     │     │
│ to co-  │     │     │     │ embed)  │     │
│ located │     │     │     └─────────┘     │
├─────────┤     │     │                     │
│ Embed   │     │     │                     │
│ summary │     │     │                     │
└─────────┘     │     │                     │
                │     │                     │
         ┌──────▼─────▼──────┐              │
         │   Save to agent   │              │
         │   only (no fan)   │              │
         └──────┬─────────────┘              │
                │                            │
         ┌──────▼──────┬─────────────────────▼┐
         │ Save to     │ Embed + Save to      │
         │ agent only  │ agent only            │
         └─────────────┘──────────────────────┘
```
