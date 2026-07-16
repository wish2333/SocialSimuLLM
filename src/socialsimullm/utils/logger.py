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
import hashlib
import logging
import os
import random
import shutil
import sys
import tempfile
import subprocess
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import networkx as nx

_run_logger = logging.getLogger("socialsimullm")


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


def setup_error_logging(output_dir: str) -> None:
    """Configure Python logging to write ERROR+ to error.log in the run directory.

    Also hooks uncaught exceptions so crash tracebacks are captured.

    Args:
        output_dir: Directory to write error.log into.
    """
    log_path = os.path.join(output_dir, "error.log")
    absolute_log_path = os.path.abspath(log_path)
    for existing in list(_run_logger.handlers):
        if (
            isinstance(existing, logging.FileHandler)
            and os.path.abspath(existing.baseFilename) == absolute_log_path
        ):
            _run_logger.removeHandler(existing)
            existing.close()
    handler = logging.FileHandler(log_path, encoding="utf-8", delay=False)
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    _run_logger.addHandler(handler)
    _run_logger.setLevel(logging.DEBUG)

    def _handle_uncaught(exc_type, exc_value, exc_tb):
        _run_logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _handle_uncaught


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
        self.model_calls_file = os.path.join(output_dir, "model_calls.jsonl")
        self.run_metadata_file = os.path.join(output_dir, "run_metadata.json")
        self._summary_buffer: list[str] = []
        self._text_buffer: list[str] = []
        self._jsonl_initialized = False
        self._runtime_sources: dict[str, object | None] = {}

    def bind_runtime(
        self,
        *,
        reflection_engine: object | None = None,
        interaction_coordinator: object | None = None,
    ) -> None:
        """Attach mutable coordinator state that is not owned by SimulationState."""
        self._runtime_sources = {
            "reflection_engine": reflection_engine,
            "interaction_coordinator": interaction_coordinator,
        }

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
        checkpoints_dir = Path(self.output_dir) / "checkpoints"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
        target = checkpoints_dir / f"step_{step}"
        temporary = Path(tempfile.mkdtemp(prefix=f".step_{step}-", dir=checkpoints_dir))
        try:
            checkpoint_dir = str(temporary)
            self._save_spatial_graph(getattr(state, "world_graph", None), checkpoint_dir)
            self._save_agent_states(getattr(state, "agents", []), checkpoint_dir)
            self._save_memory_summary(getattr(state, "memory", None), checkpoint_dir)
            self._save_meta(state, step, checkpoint_dir)
            self._save_full_project_state(state, checkpoint_dir)
            self._save_runtime_state(state, checkpoint_dir)
            self._replace_checkpoint_directory(temporary, target)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)

    def finalize(self) -> None:
        """Write done.flag and flush all remaining buffers."""
        self.flush_text_log()
        done_path = os.path.join(self.output_dir, "done.flag")
        with open(done_path, "w", encoding="utf-8") as f:
            f.write(f"completed_at: {datetime.now().isoformat()}\n")

    def log_model_call(self, record: dict[str, Any]) -> None:
        """Persist prompt-free model call metadata as one JSON line."""
        safe_record = {
            "timestamp": datetime.now().isoformat(),
            "call_type": str(record.get("call_type", "unknown")),
            "model": str(record.get("model", "")),
            "retry_count": int(record.get("retry_count", 0)),
            "fallback_used": bool(record.get("fallback_used", False)),
            "token_usage": {
                key: int(record.get("token_usage", {}).get(key, 0))
                for key in ("prompt_tokens", "completion_tokens", "total_tokens")
            },
        }
        with open(self.model_calls_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(safe_record, ensure_ascii=False) + "\n")

    def start_run_metadata(
        self,
        config_summary: dict[str, Any],
        prompt_template: str,
        *,
        resumed_from_step: int | None = None,
    ) -> None:
        """Create safe run metadata without storing prompts or credentials."""
        path = Path(self.run_metadata_file)
        existing: dict[str, Any] = {}
        if path.is_file():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing = {}
        now = datetime.now().isoformat()
        history = list(existing.get("resume_history", []))
        if resumed_from_step is not None:
            history.append({"from_step": resumed_from_step, "started_at": now})
        metadata = {
            "schema_version": 1,
            "status": "running",
            "git_commit": existing.get("git_commit") or self._git_commit(),
            "config_summary": config_summary,
            "prompt_template_version": hashlib.sha256(
                prompt_template.encode("utf-8")
            ).hexdigest()[:16],
            "started_at": existing.get("started_at", now),
            "last_started_at": now,
            "finished_at": None,
            "resume_history": history,
        }
        self._atomic_write_json(path, metadata)

    def finish_run_metadata(self, status: str) -> None:
        """Mark the current run metadata completed or failed."""
        path = Path(self.run_metadata_file)
        if not path.is_file():
            return
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        metadata["status"] = status
        metadata["finished_at"] = datetime.now().isoformat()
        self._atomic_write_json(path, metadata)

    @staticmethod
    def _git_commit() -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                cwd=Path(__file__).resolve().parents[3],
                text=True,
                timeout=2,
            )
            return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    @staticmethod
    def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        os.replace(temporary, path)

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
                    t = entry.get("event_type", entry.get("exp_type", "unknown"))
                    by_type[t] = by_type.get(t, 0) + 1
                latest = entries[-1].get("timestamp", entries[-1].get("global_time", "")) if entries else ""
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

    def _save_meta(self, state: object, step: int, checkpoint_dir: str) -> None:
        """Save metadata representing the next runnable point after this step."""
        from socialsimullm.utils.global_methods import add_ten_minutes

        meta_data = dict(getattr(state, "meta_data", {}))
        current_time = str(getattr(state, "global_time", meta_data.get("global_time", "")))
        try:
            next_time = add_ten_minutes(current_time)
        except (ValueError, IndexError):
            next_time = current_time
        meta_data["round"] = step
        meta_data["global_time"] = next_time
        meta_data["active_event_ids"] = list(
            getattr(state, "active_event_ids", meta_data.get("active_event_ids", []))
        )
        path = os.path.join(checkpoint_dir, "meta.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2, ensure_ascii=False)

    def _save_full_project_state(self, state: object, checkpoint_dir: str) -> None:
        """Copy all file-backed simulation state and the log prefix."""
        project_folder = Path(
            str(getattr(state, "project_folder", self.output_dir))
        )
        target = Path(checkpoint_dir)
        town_data = project_folder / "town_data.json"
        if town_data.is_file():
            shutil.copy2(town_data, target / "town_data.json")
        agent_data = project_folder / "agent_data"
        if agent_data.is_dir():
            shutil.copytree(agent_data, target / "agent_data")
        for filename in (
            "events.jsonl",
            "simulation_log.txt",
            "simulation_summary.txt",
            "model_calls.jsonl",
        ):
            source = project_folder / filename
            if source.is_file():
                shutil.copy2(source, target / filename)

    def _save_runtime_state(self, state: object, checkpoint_dir: str) -> None:
        """Serialize mutable in-memory state needed for deterministic continuation."""
        agents: dict[str, dict[str, Any]] = {}
        for agent in getattr(state, "agents", []):
            agents[str(agent.name)] = {
                "location": getattr(agent, "location", ""),
                "daily_plans": getattr(agent, "daily_plans", ""),
                "hourly_plan": getattr(agent, "hourly_plan", ""),
                "impression": getattr(agent, "impression", ""),
                "action": getattr(agent, "action", ""),
                "action_detail": self._jsonable(getattr(agent, "action_detail", None)),
                "recent_actions": self._jsonable(getattr(agent, "recent_actions", [])),
                "reflection": getattr(agent, "reflection", ""),
                "related_things": self._jsonable(getattr(agent, "related_things", "")),
                "event": self._jsonable(getattr(agent, "event", "")),
                "place_ratings": self._jsonable(getattr(agent, "place_ratings", [])),
                "goals": self._jsonable(getattr(agent, "goals", [])),
                "planned_path": self._jsonable(getattr(agent, "planned_path", None)),
            }

        reflection = self._runtime_sources.get("reflection_engine")
        coordinator = self._runtime_sources.get("interaction_coordinator")
        payload = {
            "schema_version": 1,
            "active_event_ids": list(getattr(state, "active_event_ids", [])),
            "events": self._jsonable(getattr(state, "events", [])),
            "timed_events": self._jsonable(getattr(state, "timed_events", [])),
            "agents": agents,
            "reflection": {
                "last_reflection_cache": self._jsonable(
                    getattr(reflection, "_last_reflection_cache", {})
                ),
                "last_reflection_step": self._jsonable(
                    getattr(reflection, "_last_reflection_step", {})
                ),
            },
            "interactions": self._serialize_interactions(coordinator),
            "logger": {
                "summary_buffer": list(self._summary_buffer),
            },
            "random_state": self._jsonable(random.getstate()),
        }
        path = Path(checkpoint_dir) / "runtime_state.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def _jsonable(cls, value: Any) -> Any:
        """Convert dataclasses, enums, tuples, and simple objects to JSON values."""
        if isinstance(value, Enum):
            return value.value
        if is_dataclass(value) and not isinstance(value, type):
            return cls._jsonable(asdict(value))
        if isinstance(value, dict):
            return {str(key): cls._jsonable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [cls._jsonable(item) for item in value]
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if hasattr(value, "__dict__"):
            return cls._jsonable(vars(value))
        return str(value)

    @classmethod
    def _serialize_interactions(cls, coordinator: object | None) -> dict[str, Any]:
        if coordinator is None:
            return {"participation": {}, "sessions": []}
        participation = {
            str(name): cls._jsonable(value)
            for name, value in getattr(coordinator, "_participation", {}).items()
        }
        sessions = [
            {"pair": list(pair), **cls._jsonable(session)}
            for pair, session in getattr(coordinator, "_sessions", {}).items()
        ]
        return {"participation": participation, "sessions": sessions}

    @staticmethod
    def _replace_checkpoint_directory(temporary: Path, target: Path) -> None:
        """Publish a complete checkpoint without exposing partial files."""
        backup = target.with_name(f".{target.name}.previous")
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            os.replace(target, backup)
        try:
            os.replace(temporary, target)
        except Exception:
            if backup.exists() and not target.exists():
                os.replace(backup, target)
            raise
        if backup.exists():
            shutil.rmtree(backup)
