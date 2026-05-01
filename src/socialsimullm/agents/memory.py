# socialsimullm/agents/memory.py

# -*- coding: utf-8 -*-

"""
Unified agent memory with structured storage and multi-dim retrieval.

Replaces the previous Memory class from retrieve/memory.py.
Storage format: per-agent JSON files + per-agent SQLite embedding DBs.
Scoring formula: 0.5*similarity + 0.3*recency + 0.2*importance.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

import numpy as np

from socialsimullm.utils.text_generation import get_embedding


class AgentMemory:
    """Unified agent memory with structured storage and multi-dim retrieval.

    Manages per-agent JSON memory files and SQLite embedding databases.
    All recall methods return list[dict]; format_* helpers return str for LLM prompts.

    Attributes:
        project_folder: Path to the project directory.
        agents: List of Agent instances in the simulation.
        memory_limit: Default number of recent experiences to consider.
    """

    def __init__(self, project_folder: str, agents: list[Any], memory_limit: int) -> None:
        self.project_folder = project_folder
        self.agents = agents
        self.memory_limit = memory_limit

    # --- Store ---

    def store(self, observation: dict) -> None:
        """Store an observation, routing by exp_type to appropriate agents.

        Routing rules:
            - action: route to the agent AND all other_agents present
            - plan/thought: route to agent only
            - event: route to ALL agents
            - reflection: route to agent, then embed and store
        """
        exp_type = observation.get("exp_type", "")

        if exp_type == "action":
            agent_name = observation["agent_name"]
            other_agents = observation.get("other_agents", [])
            # Always store for the acting agent
            memory_full = self._load_memory_file(agent_name)
            memory_full["memory"].append(observation)
            self._save_memory_file(agent_name, memory_full)
            # Fan out to co-located agents
            for agent in self.agents:
                if agent.name != agent_name and agent.name in other_agents:
                    memory_full = self._load_memory_file(agent.name)
                    memory_full["memory"].append(observation)
                    self._save_memory_file(agent.name, memory_full)
            action_des = observation.get("action_des", "")
            if action_des:
                self._embed_and_store(agent_name, action_des)

        elif exp_type in ("plan", "thought"):
            agent_name = observation["agent_name"]
            memory_full = self._load_memory_file(agent_name)
            memory_full["memory"].append(observation)
            self._save_memory_file(agent_name, memory_full)

        elif exp_type == "event":
            for agent in self.agents:
                memory_full = self._load_memory_file(agent.name)
                memory_full["memory"].append(observation)
                self._save_memory_file(agent.name, memory_full)

        elif exp_type == "reflection":
            agent_name = observation["agent_name"]
            memory_full = self._load_memory_file(agent_name)
            memory_full["memory"].append(observation)
            self._save_memory_file(agent_name, memory_full)
            action_text = observation.get("action", "")
            if action_text:
                self._embed_and_store(agent_name, action_text)

    # --- Recall API (PRD) ---

    def recall_recent(self, agent_name: str, n: int = 10) -> list[dict]:
        """Return last n action-type memories for an agent."""
        memory_full = self._load_memory_file(agent_name)
        actions = [m for m in memory_full["memory"] if m["exp_type"] == "action"]
        return actions[-n:]

    def recall_semantic(self, agent_name: str, query: str, top_k: int = 5) -> list[dict]:
        """Return memories ranked by embedding similarity + recency + importance."""
        plan_embedding = self._embed_action(query)

        db_file = os.path.join(self.project_folder, "agent_data", f"{agent_name}_memory.db")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT action_description, action_embedding FROM action_embeddings ORDER BY action_index DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        memory_full = self._load_memory_file(agent_name)
        action_memory = []
        for item in memory_full["memory"]:
            if item["exp_type"] == "action":
                action_memory.append(item)
            if item["exp_type"] == "thought" and item.get("priority") == 7:
                action_memory.append(item)
        action_map = {item["action_des"]: item for item in action_memory}

        weights = {"similarity": 0.5, "recency": 0.3, "importance": 0.2}

        scored: list[tuple[float, dict]] = []
        for idx, (action_des, emb_json) in enumerate(rows):
            if action_des not in action_map:
                continue
            action = action_map[action_des]
            action_embedding = np.array(json.loads(emb_json))
            norms = np.linalg.norm(plan_embedding) * np.linalg.norm(action_embedding)
            similarity = np.dot(plan_embedding, action_embedding) / norms if norms > 0 else 0.0
            recency = 1 - (idx / len(rows)) if rows else 0
            importance = int(action.get("priority") or 1)
            normalized_importance = (min(max(importance, 1), 9) - 1) / 8
            score = (
                weights["similarity"] * similarity
                + weights["recency"] * recency
                + weights["importance"] * normalized_importance
                + 0.0001
            )
            scored.append((score, action))
            scored.sort(reverse=True, key=lambda x: x[0])

        return [item[1] for item in scored[:top_k]]

    def recall_by_location(self, agent_name: str, location_id: str) -> list[dict]:
        """Return memories filtered by location."""
        memory_full = self._load_memory_file(agent_name)
        return [m for m in memory_full["memory"] if m.get("location") == location_id]

    def recall_time_span(self, agent_name: str, start: str, end: str) -> list[dict]:
        """Return memories within a time range.

        Time format: "Day X, HH:MM". Compares lexicographically.
        """
        memory_full = self._load_memory_file(agent_name)
        return [
            m
            for m in memory_full["memory"]
            if start <= m.get("global_time", "") <= end
        ]

    def recall_by_importance(self, agent_name: str, global_time: str, min_importance: int = 7) -> list[dict]:
        """Return high-importance action memories from the current day."""
        day_str = global_time.split(",")[0]
        memory_full = self._load_memory_file(agent_name)
        return [
            item
            for item in memory_full["memory"]
            if item["exp_type"] == "action"
            and int(item.get("priority", 1) or 1) > min_importance - 1
            and item.get("global_time", "").split(",")[0] == day_str
        ]

    def recall_impressions(self, agent_name: str, n: int = 3) -> list[dict]:
        """Return recent impression (thought, priority=4) memories."""
        memory_full = self._load_memory_file(agent_name)
        impressions = [
            m for m in memory_full["memory"]
            if m["exp_type"] == "thought" and m.get("priority") == 4
        ]
        return impressions[-n:]

    # --- Format helpers (for LLM prompts) ---

    def format_recent(self, agent_name: str, n: int) -> str:
        """Format recent actions as a newline-separated string."""
        items = self.recall_recent(agent_name, n)
        lines = [m.get("action_des", "No new things recorded") for m in items]
        return "\n".join(lines)

    def format_impressions(self, agent_name: str, n: int) -> str:
        """Format recent impressions as a newline-separated string."""
        items = self.recall_impressions(agent_name, n)
        lines = [m.get("action", "No impression recorded") for m in items]
        return "\n".join(lines)

    def format_semantic(self, agent_name: str, query: str, top_k: int) -> str:
        """Format semantically-related memories as a newline-separated string."""
        items = self.recall_semantic(agent_name, query, top_k)
        lines = [m.get("action_des", "No related things recorded") for m in items]
        return "\n".join(lines)

    def format_by_importance(self, agent_name: str, global_time: str) -> str:
        """Format important memories from the current day as a string."""
        items = self.recall_by_importance(agent_name, global_time)
        lines = [m.get("action_des", "No important things recorded") for m in items]
        return "\n".join(lines)

    # --- Initialization ---

    def get_init_memory(self, agent_name: str) -> list[str]:
        """Return [daily_plan_str, hourly_plan_str] from last saved plans."""
        memory_full = self._load_memory_file(agent_name)
        memory = memory_full["memory"]
        daily_plans = [p for p in memory if p["exp_type"] == "plan" and p.get("priority") == 3]
        last_daily = daily_plans[-1] if daily_plans else {"action": ""}
        hourly_plans = [p for p in memory if p["exp_type"] == "plan" and p.get("priority") == 2]
        last_hourly = hourly_plans[-1] if hourly_plans else {"action": ""}
        return [last_daily["action"], last_hourly["action"]]

    # --- Global events ---

    def load_events(self) -> dict:
        """Load global events from event.json. Create if missing."""
        event_file = os.path.join(self.project_folder, "agent_data", "event.json")
        if not os.path.exists(event_file):
            event = {"event": []}
            with open(event_file, "w", encoding="utf-8") as f:
                json.dump(event, f, indent=4)
        else:
            with open(event_file, "r", encoding="utf-8") as f:
                event = json.load(f)
        return event

    def save_event(self, new_event: dict) -> dict:
        """Append a global event and return the updated events dict."""
        event = self.load_events()
        event["event"].append(new_event)
        event_file = os.path.join(self.project_folder, "agent_data", "event.json")
        with open(event_file, "w", encoding="utf-8") as f:
            json.dump(event, f, indent=4)
        return event

    # --- Internal storage ---

    def _load_memory_file(self, agent_name: str) -> dict:
        """Load an agent's memory JSON file."""
        memory_file = os.path.join(
            self.project_folder, "agent_data", f"{agent_name}_memory.json"
        )
        with open(memory_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_memory_file(self, agent_name: str, data: dict) -> None:
        """Save an agent's memory JSON file."""
        memory_file = os.path.join(
            self.project_folder, "agent_data", f"{agent_name}_memory.json"
        )
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def _embed_action(self, action: str) -> list[float]:
        """Generate embedding for an action string."""
        return get_embedding(action)

    def _embed_and_store(self, agent_name: str, action: str) -> None:
        """Embed an action and store in the agent's SQLite database."""
        embedding = self._embed_action(action)
        self._store_embedding(agent_name, action, embedding)

    def _store_embedding(self, agent_name: str, action: str, embedding: list[float]) -> None:
        """Store an action embedding in the agent's SQLite database."""
        embedding_json = json.dumps(embedding)
        db_file = os.path.join(self.project_folder, "agent_data", f"{agent_name}_memory.db")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS action_embeddings (
                action_index INTEGER,
                action_description TEXT,
                action_embedding TEXT
            )"""
        )
        cursor.execute("SELECT MAX(action_index) FROM action_embeddings")
        max_index = cursor.fetchone()[0] or 0
        cursor.execute(
            "INSERT INTO action_embeddings (action_index, action_description, action_embedding) VALUES (?, ?, ?)",
            (max_index + 1, action, embedding_json),
        )
        conn.commit()
        conn.close()
