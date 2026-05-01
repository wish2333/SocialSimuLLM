# Product Requirements Document (PRD)

> Version: 3.1
> Last Updated: 2026-05-01
> Status: Active

---

## 1. Product Overview

### 1.1 Product Name

SocialSimuLLM - Large Language Model Based Social Simulation Framework

### 1.2 Problem Statement

Traditional social simulation frameworks lack the ability to model complex, nuanced human-like decision making and interactions. Existing agent-based models use simple rule-based systems that cannot capture the depth of human social behavior, impressions formation, and reflective thinking.

### 1.3 Product Vision

Build a flexible, customizable social simulation framework powered by Large Language Models (LLMs) that can simulate realistic agent interactions, memory formation, and social dynamics in various scenarios.

### 1.4 Target Audience

- Social science researchers studying group dynamics and social interactions
- AI researchers exploring LLM-based agent behavior
- Game developers creating dynamic NPC interaction systems
- Urban planners simulating pedestrian movement patterns
- Students learning about agent-based modeling

---

## 2. Goals and Objectives

### 2.1 Primary Goals

1. **Realistic Agent Behavior**: Agents should exhibit human-like planning, action execution, and reflection
2. **Memory Management**: Agents must maintain short-term and long-term memories with importance rating
3. **Flexible Scenarios**: Support customizable town data, agent profiles, and interaction rules
4. **Scalable Architecture**: Support multiple agents and locations without performance degradation

### 2.2 Success Metrics

- Agents can complete multi-day simulations with coherent daily plans
- Memory retrieval returns contextually relevant experiences
- Location ratings accurately reflect agent preferences
- Simulation logs provide readable narrative summaries

---

## 3. Features

### 3.1 Implemented Features

#### F-001: Agent Daily Planning
- **Status**: Completed (V1.0)
- **Description**: At the start of each day (08:00), agents generate hourly plans for the day using LLM prompts
- **Priority**: P0
- **Details**: Plans cover 08:00-20:00 with one action per hour, limited to 10 words per action

#### F-002: Agent Hourly Planning
- **Status**: Completed (V1.0)
- **Description**: At the start of each hour (xx:00), agents generate specific plans for the next hour based on location, nearby agents, and recent impressions
- **Priority**: P0
- **Details**: Limited to 20 words, considers current location description and people present

#### F-003: Action Execution
- **Status**: Completed (V1.0)
- **Description**: Agents execute planned actions with LLM-generated responses, including potential communication with other agents at the same location
- **Priority**: P0
- **Details**: Actions limited to 50 words, supports agent-to-agent communication

#### F-004: Experience Rating
- **Status**: Completed (V2.0)
- **Description**: Rate the importance/poignancy of experiences on a 1-9 scale for memory prioritization
- **Priority**: P1
- **Details**: Scale: 1=Mundane (brushing teeth), 9=Extremely poignant (breakup, college acceptance)

#### F-005: Location Rating and Movement
- **Status**: Completed (V1.0)
- **Description**: Agents rate likelihood of moving to each location (1-9 scale) and move to the highest-rated location
- **Priority**: P0
- **Details**: Movement uses shortest path algorithm via NetworkX graph

#### F-006: Memory Management
- **Status**: Completed (V3.0)
- **Description**: Agents maintain memory with JSON storage for structured data and SQLite for embeddings
- **Priority**: P0
- **Details**:
  - JSON: Stores experiences with agent_name, global_time, location, action, exp_type, priority
  - SQLite: Stores action embeddings for similarity search
  - Memory types: action, plan, thought, event, reflection

#### F-007: Impression Formation
- **Status**: Completed (V2.0)
- **Description**: Agents form impressions of their current state (emotional status, social drive, confidence, etc.)
- **Priority**: P1
- **Details**: 30-word limit, 5 dimensions: Emotional Status, Social/Learning Drive, Confidence, Information Preference, Technology Acceptance

#### F-008: Daily Reflection
- **Status**: Completed (V3.0)
- **Description**: At the end of each day, agents reflect on their experiences, feelings about technology, social interactions, and accomplishments
- **Priority**: P1
- **Details**: 75-word limit, uses important events from the day (priority > 6)

#### F-009: Event System
- **Status**: Completed (V3.0)
- **Description**: Global events can be injected into the simulation, affecting all agents' memories
- **Priority**: P2
- **Details**: Events stored in event.json, propagated to all agents with priority 9

#### F-010: Simulation Summary
- **Status**: Completed (V2.0)
- **Description**: Generate human-readable summaries of daily simulation using LLM
- **Priority**: P2
- **Details**: Summarizes actions from all agents, outputs to simulation_summary.txt

#### F-011: Project persistence
- **Status**: Completed (V1.0)
- **Description**: Simulation state is saved to disk, allowing continuation across sessions
- **Priority**: P0
- **Details**: meta.json stores global_time and round; agent memories persist in JSON and SQLite

### 3.2 Planned Features

#### F-012: Web UI
- **Status**: Planned
- **Description**: Browser-based interface for configuring and monitoring simulations
- **Priority**: P2

#### F-013: Multi-project Support
- **Status**: Planned
- **Description**: Run multiple simulations in parallel with isolated project folders
- **Priority**: P1

---

## 4. Data Models

### 4.1 Agent

| Field | Type | Description |
|-------|------|-------------|
| name | str | Unique agent identifier |
| description | str | JSON string of agent traits and background |
| location | str | Current location name |
| daily_plans | str | Today's hourly plans |
| hourly_plan | str | Current hour's specific plan |
| action | str | Most recent executed action |
| impression | str | Most recent impression |
| reflection | str | Most recent daily reflection |

### 4.2 Memory Experience

| Field | Type | Description |
|-------|------|-------------|
| agent_name | str | Agent who owns this memory |
| global_time | str | Format: "Day X, HH:MM" |
| location | str | Where the experience occurred |
| action | str | Narrative description |
| action_des | str | Simplified SVO sentence |
| other_agents | list | Agents present during experience |
| exp_type | str | One of: action, plan, thought, event, reflection |
| priority | int | Importance rating 1-9 |

### 4.3 Location

| Field | Type | Description |
|-------|------|-------------|
| name | str | Location identifier |
| description | str | Text description of the location |

### 4.4 Town Data (town_data.json)

| Field | Type | Description |
|-------|------|-------------|
| general.memory_limit | int | Max recent experiences to retrieve |
| town_people | dict | Agent definitions keyed by name |
| town_areas | dict | Location definitions keyed by name |

---

## 5. Non-Functional Requirements

### 5.1 Performance
- Simulation loop: 10-minute increments processed within 5 seconds (excluding LLM API latency)
- Memory retrieval: Return top-N related experiences within 1 second

### 5.2 Scalability
- Support up to 20 agents in a single simulation
- Support up to 15 locations

### 5.3 Reliability
- Simulation state must be persistable and resumable
- JSON and SQLite files must maintain valid state after each round

### 5.4 Extensibility
- New prompt templates can be added without code changes
- LLM provider can be swapped via config.py
- Town data is JSON-based for easy customization

---

## 6. Module Descriptions

### 6.1 Main Module (`socialsimullm/__main__.py`)
- Entry point of the simulation
- Initializes global variables and modules
- Loads project data (meta.json, town_data.json)
- Creates NetworkX graph of the town
- Creates and initializes agents
- Runs the main simulation loop:
  - Daily planning (08:00)
  - Hourly planning (xx:00)
  - Action execution (every 10 minutes)
  - Memory updates
  - Location rating and movement
  - Impression formation
  - Daily reflection (08:00 next day)
  - Simulation summary generation

### 6.2 Agents Module (`socialsimullm/agents/`)
- **agent.py**: Agent class with methods for planning, action, movement, rating, impression, reflection
- **memory.py**: Agent memory helper functions (experience rating, memory formatting, location change recording)
- **movement.py**: Location rating and movement logic using NetworkX

### 6.3 Locations Module (`socialsimullm/locations/`)
- **locations.py**: Location and Locations classes for managing simulation locations

### 6.4 Retrieve Module (`socialsimullm/retrieve/`)
- **memory.py**: Memory class for managing agent memories (JSON + SQLite with embeddings)
- **reflect.py**: Reflect class for agent reflection (placeholder)

### 6.5 Utils Module (`socialsimullm/utils/`)
- **config.py**: API keys, base URLs, default model configurations
- **global_methods.py**: Helper functions for loading/saving meta data, town data, agent data, time management
- **text_generation.py**: GPT API requests, embeddings, rating extraction, simulation summarization

### 6.6 Prompt Templates (`socialsimullm/prompt_templates/`)
- **template_agents.py**: All LLM prompt templates for agent planning, action, rating, impression, reflection

---

## 7. User Stories

### US-001: Run a Basic Simulation
As a researcher, I want to run a simulation with default town data so that I can observe agent interactions.

### US-002: Customize Agent Profiles
As a user, I want to modify town_data.json to define my own agents and locations so that I can simulate custom scenarios.

### US-003: Resume a Simulation
As a user, I want to re-enter a project name so that I can continue a previously started simulation.

### US-004: Inject Global Events
As a researcher, I want to input a global event so that I can observe how agents react to unexpected situations.

### US-005: Review Simulation Logs
As a user, I want to read simulation_log.txt and simulation_summary.txt so that I can analyze agent behavior.

---

## 8. Acceptance Criteria

### 8.1 For F-001 (Daily Planning)
- [ ] Agent generates plans at 08:00 each day
- [ ] Plans cover 08:00-20:00 with one action per hour
- [ ] Plans are saved to agent's memory with exp_type='plan' and priority=3

### 8.2 For F-005 (Movement)
- [ ] Agent rates all locations on 1-9 scale each hour
- [ ] Agent moves to highest-rated location
- [ ] Movement is recorded in memory with exp_type='action' and priority=2
- [ ] Movement uses shortest path algorithm

### 8.3 For F-006 (Memory)
- [ ] Experiences are saved to JSON file
- [ ] Action embeddings are stored in SQLite
- [ ] Related experiences can be retrieved by similarity search
- [ ] Memory limit controls how many recent experiences are returned
