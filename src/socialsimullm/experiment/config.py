# socialsimullm/experiment/config.py

# -*- coding: utf-8 -*-

"""
Experiment configuration models for SocialSimuLLM.

Provides Pydantic-based ExperimentConfig for reproducible experiment
setup, YAML serialization, and conversion to SimulationConfig for
the simulation engine.

@author: Huang Miaosen
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from socialsimullm.utils.config import SimulationConfig


class SpatialConfig(BaseModel):
    """Spatial graph generation configuration.

    Controls the topology and edge weights of the simulation world graph.
    When set, the world graph is generated instead of loaded from town_data.json.
    """

    topology: str = Field(
        default="ring",
        description="Graph topology: ring, small_world, grid, random, scale_free",
    )
    num_locations: int = Field(
        default=4, ge=2, le=15, description="Number of location nodes"
    )
    edge_weight_min: float = Field(
        default=1.0, ge=0.1, description="Minimum edge weight (distance)"
    )
    edge_weight_max: float = Field(
        default=1.0, ge=0.1, description="Maximum edge weight (distance)"
    )
    seed: int = Field(
        default=42, ge=0, description="Random seed for graph generation"
    )
    small_world_k: int = Field(default=4, ge=2, description="Watts-Strogatz k parameter")
    small_world_p: float = Field(default=0.3, ge=0.0, le=1.0, description="Watts-Strogatz p parameter")
    grid_rows: int = Field(default=2, ge=1, description="Grid rows")
    grid_cols: int = Field(default=2, ge=1, description="Grid columns")
    random_p: float = Field(default=0.4, ge=0.0, le=1.0, description="Erdos-Renyi edge probability")
    scale_free_m: int = Field(default=2, ge=1, description="Barabasi-Albert m parameter")

    @field_validator("edge_weight_max")
    @classmethod
    def edge_weights_valid(cls, v: float, info) -> float:
        if "edge_weight_min" in info.data and v < info.data["edge_weight_min"]:
            raise ValueError("edge_weight_max must be >= edge_weight_min")
        return v


class MemoryConfig(BaseModel):
    """Memory retrieval weight configuration for experiment runs.

    Controls how memories are scored during recall:
        score = recency_weight * recency + similarity_weight * similarity
              + importance_weight * importance
    """

    recency_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    similarity_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    importance_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    importance_threshold: int = Field(default=6, ge=1, le=9)

    @field_validator("recency_weight", "similarity_weight", "importance_weight")
    @classmethod
    def weights_sum_to_one(cls, v: float, info) -> float:
        return v


class ExperimentConfig(BaseModel):
    """Full experiment configuration with validation.

    Wraps SimulationConfig fields and adds experiment-specific parameters
    (experiment_id, random_seed, budget_limit, events) for reproducible
    batch execution. Converts to SimulationConfig via to_simulation_config().

    API keys are NOT stored here -- they come from environment variables
    (or a .env file) and are applied by _apply_config_to_globals() at runtime.

    Usage::

        config = ExperimentConfig(model="deepseek-chat", simulation_steps=144)
        config.to_yaml("experiments/exp001.yaml")

        loaded = ExperimentConfig.from_yaml("experiments/exp001.yaml")
        sim_config = loaded.to_simulation_config()
    """

    experiment_id: str = Field(
        default_factory=lambda: f"exp_{uuid.uuid4().hex[:8]}",
        description="Unique experiment identifier (auto-generated or manual)",
    )
    project: str = Field(
        default="",
        description="Project name under runs/. Defaults to experiment_id.",
    )
    model: str = Field(default="", description="LLM completion model (empty = env OPENAI_MODEL)")
    embedding_model: str = Field(
        default="", description="Embedding model (empty = env OPENAI_EMBEDDING_MODEL)"
    )
    simulation_steps: int = Field(
        default=144, ge=1, description="Number of 10-minute simulation steps"
    )
    memory_limit: int = Field(
        default=10, ge=1, description="Number of recent experiences to consider"
    )
    random_seed: int = Field(
        default=42, ge=0, description="Random seed for reproducibility (0 = no seed)"
    )
    checkpoint_interval: int = Field(
        default=10, ge=0, description="Steps between checkpoint saves (0 = disabled)"
    )
    spatial_graph_path: str = Field(
        default="",
        description="Path to town_data.json (absolute or relative to project)",
    )
    events: list[str] = Field(
        default_factory=list,
        description="Initial global events (one per simulation day boundary)",
    )
    budget_limit: float = Field(
        default=0.0, ge=0.0, description="USD budget cap (0 = unlimited)"
    )
    memory_config: MemoryConfig = Field(
        default_factory=MemoryConfig, description="Memory retrieval weight config"
    )

    # Spatial configuration
    spatial_config: SpatialConfig | None = Field(
        default=None, description="Spatial graph generation config (None = use town_data.json)"
    )

    # FOV configuration
    fov_enabled: bool = Field(
        default=False, description="Enable proximity-based agent perception"
    )
    fov_distance: float = Field(
        default=0.0, ge=0.0, description="Max graph distance for visibility (0 = same location only)"
    )

    # PathPlanner configuration
    path_planner_enabled: bool = Field(
        default=False, description="Enable LLM intent + A* path planning"
    )
    multi_hop_movement: bool = Field(
        default=True, description="Agents traverse one node per step (False = teleport)"
    )

    # Goal configuration
    goal_enabled: bool = Field(
        default=False, description="Enable goal-driven hierarchical planning"
    )
    max_active_goals: int = Field(
        default=3, ge=1, le=10, description="Max concurrent active goals per agent"
    )

    # Reflection settings (mirrors SimulationConfig)
    reflection_enabled: bool = Field(default=True, description="Enable reflection system")
    reflection_importance_threshold: int = Field(
        default=15, ge=1, description="Cumulative importance to trigger mid-day reflection"
    )
    reflection_min_observations: int = Field(
        default=3, ge=1, description="Min observations before reflection triggers"
    )
    reflection_token_limit: int = Field(
        default=500, ge=10, description="Token limit for reflection generation"
    )
    reflection_include_in_planning: bool = Field(
        default=True, description="Inject past reflections into daily planning"
    )

    # Prompt config
    prompt_meta: str = Field(
        default="### Instruction:\n{}\n### Response:",
        description="Prompt template wrapper for LLM calls",
    )

    @field_validator("project")
    @classmethod
    def project_defaults_to_id(cls, v: str) -> str:
        return v

    def model_post_init(self, __context: Any) -> None:
        pass

    def to_simulation_config(self) -> "SimulationConfig":
        """Convert to SimulationConfig for SimulatorCore consumption.

        Maps ExperimentConfig fields to SimulationConfig fields.
        API keys are resolved from environment variables / .env by
        _apply_config_to_globals() at runtime.

        Returns:
            A SimulationConfig dataclass instance.
        """
        import os

        from socialsimullm.utils.config import SimulationConfig as _SC

        return _SC(
            project_name=self.project,
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            openai_base_url=os.environ.get("OPENAI_BASE_URL", ""),
            key_owner=os.environ.get("SOCIALSIMU_KEY_OWNER", ""),
            embedding_model=self.embedding_model or os.environ.get("OPENAI_EMBEDDING_MODEL", ""),
            embedding_base_url=os.environ.get("EMBEDDING_BASE_URL", ""),
            embedding_api_key=os.environ.get("EMBEDDING_API_KEY", ""),
            completion_model=self.model or os.environ.get("OPENAI_MODEL", ""),
            max_steps=self.simulation_steps,
            memory_limit=self.memory_limit,
            checkpoint_interval=self.checkpoint_interval,
            prompt_meta=self.prompt_meta,
            reflection_enabled=self.reflection_enabled,
            reflection_importance_threshold=self.reflection_importance_threshold,
            reflection_min_observations=self.reflection_min_observations,
            reflection_token_limit=self.reflection_token_limit,
            reflection_include_in_planning=self.reflection_include_in_planning,
            fov_enabled=self.fov_enabled,
            fov_distance=self.fov_distance,
            path_planner_enabled=self.path_planner_enabled,
            multi_hop_movement=self.multi_hop_movement,
            goal_enabled=self.goal_enabled,
            max_active_goals=self.max_active_goals,
        )

    def to_yaml(self, path: str | Path) -> None:
        """Export configuration to a YAML file.

        Args:
            path: Output file path for the YAML config.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(exclude_none=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_yaml(cls, path: str | Path) -> ExperimentConfig:
        """Import configuration from a YAML file.

        Args:
            path: Path to the YAML config file.

        Returns:
            A validated ExperimentConfig instance.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
            ValueError: If the YAML content fails Pydantic validation.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML content in {path}: expected mapping")

        from pydantic import ValidationError
        try:
            return cls.model_validate(data)
        except ValidationError as e:
            errors = "; ".join(
                f"{err['loc'][-1]}: {err['msg']}" for err in e.errors()
            )
            raise ValueError(f"Config validation failed in {path}: {errors}") from e

    def get_event_string(self) -> str:
        """Join events list into a single string for _load_events().

        Returns:
            Semicolon-joined events string, or 'No new event.' if empty.
        """
        if not self.events:
            return "No new event."
        return "; ".join(self.events)
