# socialsimullm/utils/logger.py

# -*- coding: utf-8 -*-

"""
Structured JSONL logger with checkpoint support for SocialSimuLLM.

Provides StructuredLogger that writes machine-readable JSONL event logs
alongside human-readable text logs. Supports periodic checkpoint saves
of simulation state for reproducibility and crash recovery.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime

import networkx as nx


@dataclass
class LogConfig:
    """Configuration for structured logging.

    Attributes:
        log_to_file: Write human-readable simulation_log.txt.
        log_to_jsonl: Write machine-readable events.jsonl.
        print_to_console: Print event summaries to stdout.
        include_in_summary: Include event data in summary buffer for LLM.
    """

    log_to_file: bool = True
    log_to_jsonl: bool = True
    print_to_console: bool = True
    include_in_summary: bool = True


class StructuredLogger:
    """Structured JSONL logger with checkpoint support.

    Writes events to three channels simultaneously:
    1. JSONL file (events.jsonl) for machine-readable analysis
    2. Text file (simulation_log.txt) for human-readable logs
    3. Console (stdout) for real-time monitoring

    Also maintains a summary buffer for LLM-based day summaries
    and supports periodic checkpoint saves.

    Usage::

        logger = StructuredLogger(project_folder)
        logger.log_event("daily_plan", step=1, agent_id="Alice", data={"plan": "..."})
        logger.save_checkpoint(state, step=10)
        logger.finalize()
    """

    def __init__(self, output_dir: str, log_config: LogConfig | None = None) -> None:
        self.output_dir = output_dir
        self.log_config = log_config or LogConfig()
        self.events_file = os.path.join(output_dir, "events.jsonl")
        self.log_file = os.path.join(output_dir, "simulation_log.txt")
        self.summary_file = os.path.join(output_dir, "simulation_summary.txt")
        self._summary_buffer: list[str] = []
        self._text_buffer: list[str] = []
        self._jsonl_initialized = False

    # --- Event logging ---

    def log_event(
        self,
        event_type: str,
        step: int,
        agent_id: str = "",
        data: dict | None = None,
    ) -> None:
        """Log a structured event to all active channels.

        Args:
            event_type: Category of the event (e.g., "daily_plan", "action", "movement").
            step: Current simulation round number.
            agent_id: Name of the agent involved (empty for global events).
            data: Event payload dictionary.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "agent_id": agent_id,
            "event_type": event_type,
            "data": data or {},
        }

        if self.log_config.log_to_jsonl:
            self._write_jsonl(entry)

        if self.log_config.log_to_file:
            text = self._format_text_entry(entry)
            self._text_buffer.append(text)

        if self.log_config.print_to_console:
            self._print_event(entry)

    def log_round_start(self, step: int, global_time: str) -> None:
        """Log the start of a simulation round."""
        separator = f"====================== ROUND {step} TIME {global_time} ========================"
        if self.log_config.log_to_file:
            self._text_buffer.append(separator + "\n")
        if self.log_config.print_to_console:
            print(separator + "\n")

    def log_round_end(self, step: int) -> None:
        """Log the end of a simulation round."""
        separator = f"---------- END OF ROUND {step} ----------"
        text = separator + "\n" + separator + "\n\n"
        if self.log_config.log_to_file:
            self._text_buffer.append(text)
        if self.log_config.print_to_console:
            print(separator + "\n" + separator + "\n")

    def log_separator(self, title: str, step: int = 0) -> None:
        """Log a section separator with a title."""
        text = f"=== {title} ===\n"
        if self.log_config.log_to_file:
            self._text_buffer.append(text)
        if self.log_config.print_to_console:
            print(text)

    def log_debug(self, message: str) -> None:
        """Log a debug message to the text log only."""
        self._text_buffer.append(message + "\n")

    # --- Summary buffer ---

    def add_summary(self, text: str) -> None:
        """Add text to the summary buffer for LLM summarization."""
        self._summary_buffer.append(text)

    def get_summary_text(self) -> str:
        """Get accumulated summary text for LLM summarization."""
        return "\n".join(self._summary_buffer)

    def clear_summary(self) -> None:
        """Clear summary buffer after day-boundary summarization."""
        self._summary_buffer.clear()

    # --- Flush operations ---

    def flush_text_log(self) -> None:
        """Write accumulated text buffer to simulation_log.txt."""
        if self._text_buffer:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.writelines(self._text_buffer)
            self._text_buffer.clear()

    def write_summary(self, summary_text: str, step: int) -> None:
        """Write a day-boundary summary to simulation_summary.txt."""
        header = f"----------------------- SUMMARY FOR ROUND {step} ----------\n"
        if self.log_config.print_to_console:
            print(header)
            print(summary_text)
        with open(self.summary_file, "a", encoding="utf-8") as f:
            f.write(header + summary_text + "\n\n")

    # --- Checkpoint ---

    def save_checkpoint(self, state: object, step: int) -> None:
        """Save a checkpoint of the simulation state.

        Creates a directory with serialized state files:
            checkpoints/step_{N}/
                spatial_graph.json    - NetworkX graph data
                agent_states.json     - Per-agent state snapshots
                memory_summary.json   - Memory statistics
                meta.json             - Metadata snapshot
        """
        checkpoint_dir = os.path.join(self.output_dir, "checkpoints", f"step_{step}")
        os.makedirs(checkpoint_dir, exist_ok=True)

        self._save_spatial_graph(getattr(state, "world_graph", None), checkpoint_dir)
        self._save_agent_states(getattr(state, "agents", []), checkpoint_dir)
        self._save_memory_summary(getattr(state, "memory", None), checkpoint_dir)
        self._save_meta(getattr(state, "meta_data", {}), checkpoint_dir)

    def finalize(self) -> None:
        """Write done.flag and flush all remaining buffers."""
        self.flush_text_log()
        done_path = os.path.join(self.output_dir, "done.flag")
        with open(done_path, "w", encoding="utf-8") as f:
            f.write(f"completed_at: {datetime.now().isoformat()}\n")

    # --- Private: JSONL ---

    def _write_jsonl(self, entry: dict) -> None:
        """Append a JSON line to the events file."""
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # --- Private: text formatting ---

    def _format_text_entry(self, entry: dict) -> str:
        """Format a JSONL entry as human-readable text."""
        event_type = entry["event_type"]
        agent_id = entry["agent_id"]
        step = entry["step"]
        data = entry["data"]

        if event_type == "daily_plan":
            return f"=== DAILY PLAN FOR {agent_id} AT ROUND {step} ===\n{agent_id} plans:\n{data.get('plan', '')}\n\n"
        elif event_type == "hourly_plan":
            return f"=== HOURLY PLAN FOR {agent_id} AT ROUND {step} ===\n{agent_id}'s hourly action:\n{data.get('plan', '')}\n\n"
        elif event_type == "action":
            return f"=== ACTION EXECUTION FOR {agent_id} AT ROUND {step} ===\n{agent_id} executes action: {data.get('action', '')}\n\n"
        elif event_type == "movement":
            return f"{agent_id} moved from {data.get('from', '')} to {data.get('to', '')}\n\n"
        elif event_type == "impression":
            return f"=== RECENT IMPRESSIONS FOR {agent_id} AT ROUND {step} ===\n{agent_id}'s recent impression: {data.get('impression', '')}\n\n"
        elif event_type == "reflection":
            return f"=== REFLECTION FOR {agent_id} AT ROUND {step} ===\n{data.get('reflection', '')}\n\n"
        elif event_type == "location_ratings":
            return f"=== UPDATED LOCATION RATINGS FOR {agent_id} ===\n{agent_id} location ratings: {data.get('ratings', '')}\n"
        else:
            return f"[{event_type}] {agent_id}: {data}\n"

    def _print_event(self, entry: dict) -> None:
        """Print event summary to console."""
        event_type = entry["event_type"]
        agent_id = entry["agent_id"]
        data = entry["data"]

        if event_type == "daily_plan":
            print(f"{agent_id} plans:\n{data.get('plan', '')}\n")
        elif event_type == "hourly_plan":
            print(f"{agent_id}'s hourly action:\n{data.get('plan', '')}\n")
        elif event_type == "action":
            print(f"{agent_id} executes action: {data.get('action', '')}\n")
        elif event_type == "movement":
            print(f"{agent_id} moved from {data.get('from', '')} to {data.get('to', '')}\n")
        elif event_type == "impression":
            print(f"{agent_id}'s recent impression: {data.get('impression', '')}\n")
        elif event_type == "reflection":
            print(f"{data.get('reflection', '')}\n")

    # --- Private: checkpoint serialization ---

    def _save_spatial_graph(self, graph: nx.Graph | None, checkpoint_dir: str) -> None:
        """Serialize NetworkX graph to JSON using node_link_data format."""
        if graph is None:
            return
        graph_data = nx.node_link_data(graph)
        path = os.path.join(checkpoint_dir, "spatial_graph.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

    def _save_agent_states(self, agents: list, checkpoint_dir: str) -> None:
        """Serialize agent states to JSON."""
        agent_states = []
        for agent in agents:
            agent_states.append({
                "name": agent.name,
                "description": agent.description,
                "location": agent.location,
                "daily_plans": agent.daily_plans,
                "hourly_plan": agent.hourly_plan,
                "impression": agent.impression,
                "action": agent.action,
                "reflection": agent.reflection,
                "related_things": agent.related_things,
                "event": agent.event,
                "place_ratings": agent.place_ratings,
            })
        path = os.path.join(checkpoint_dir, "agent_states.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(agent_states, f, indent=2, ensure_ascii=False)

    def _save_memory_summary(self, memory: object | None, checkpoint_dir: str) -> None:
        """Save memory statistics summary (not full memory data)."""
        if memory is None:
            return
        summary: dict = {
            "memory_limit": getattr(memory, "memory_limit", 0),
            "agents": {},
        }
        for agent in getattr(memory, "agents", []):
            try:
                memory_full = memory._load_memory_file(agent.name)
                entries = memory_full.get("memory", [])
                by_type: dict[str, int] = {}
                for entry in entries:
                    t = entry.get("exp_type", "unknown")
                    by_type[t] = by_type.get(t, 0) + 1
                latest = entries[-1].get("global_time", "") if entries else ""
                summary["agents"][agent.name] = {
                    "total_entries": len(entries),
                    "by_type": by_type,
                    "latest_timestamp": latest,
                }
            except (FileNotFoundError, KeyError):
                summary["agents"][agent.name] = {"total_entries": 0, "by_type": {}, "latest_timestamp": ""}
        path = os.path.join(checkpoint_dir, "memory_summary.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def _save_meta(self, meta_data: dict, checkpoint_dir: str) -> None:
        """Save metadata snapshot."""
        path = os.path.join(checkpoint_dir, "meta.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2, ensure_ascii=False)
