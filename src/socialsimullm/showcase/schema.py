"""Immutable data contracts for offline interview showcase snapshots."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _ReadOnlyModel(BaseModel):
    """Base class for validated, immutable showcase records."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class ShowcaseSource(_ReadOnlyModel):
    """Provenance for a migrated showcase snapshot."""

    source_project: str
    source_format: str
    source_files: list[str]
    built_at: datetime
    conversion_rule_version: str
    disclaimer: str


class ShowcaseAgent(_ReadOnlyModel):
    """Agent identity copied from the source town configuration."""

    name: str
    description: str
    starting_location: str


class ShowcaseLocation(_ReadOnlyModel):
    """Location identity copied from the source town configuration."""

    name: str
    description: str


class ShowcaseStep(_ReadOnlyModel):
    """A real source time point for which a checkpoint was built."""

    step: int = Field(ge=1)
    global_time: str
    checkpoint: str


class ShowcaseEventData(_ReadOnlyModel):
    """Normalized payload migrated from one unique legacy memory entry."""

    global_time: str
    location: str
    content: str
    summary: str = ""
    entities: list[str] = Field(default_factory=list)
    importance: int | None = Field(default=None, ge=1, le=9)
    action: str | None = None
    plan: str | None = None
    impression: str | None = None


class ShowcaseEvent(_ReadOnlyModel):
    """Event compatible with the current structured JSONL envelope."""

    timestamp: str
    step: int = Field(ge=1)
    agent_id: str
    event_type: str
    data: ShowcaseEventData


class ShowcaseAgentState(_ReadOnlyModel):
    """List-form checkpoint state built only from known source fields."""

    name: str
    description: str
    location: str
    daily_plans: str = ""
    hourly_plan: str = ""
    impression: str = ""
    action: str = ""
    reflection: str = ""
    related_things: list[str] = Field(default_factory=list)
    event: list[str] = Field(default_factory=list)
    place_ratings: dict[str, Any] = Field(default_factory=dict)


EvidenceLevel = Literal[
    "archive_descriptive",
    "paper_interpretation",
    "mechanism_evidence",
    "unverified_alternative",
]


class ResearchProvenance(_ReadOnlyModel):
    """Stable pointers to the paper and archived repository evidence."""

    paper_title: str
    paper_file: str
    paper_pages: tuple[int, ...] = ()
    repository_branch: str
    repository_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_paths: tuple[str, ...]
    archive_note: str


class ResearchQuestion(_ReadOnlyModel):
    """One social-science question and its theoretical framing."""

    id: str
    title: str
    question: str
    theoretical_lens: tuple[str, ...]
    pdf_pages: tuple[int, ...] = ()


class ResearchScale(_ReadOnlyModel):
    """Declared formal experiment scale, separate from archived coverage."""

    branch_count: int = Field(ge=1)
    archived_branch_count: int = Field(ge=0)
    agents_per_branch: int = Field(ge=1)
    locations: int = Field(ge=1)
    rounds_per_branch: int = Field(ge=1)
    planned_rounds: int = Field(ge=1)
    time_step_minutes: int = Field(ge=1)
    starts_at: str
    ends_at: str
    execution_note: str

    @model_validator(mode="after")
    def validate_planned_rounds(self) -> "ResearchScale":
        expected = self.branch_count * self.rounds_per_branch
        if self.planned_rounds != expected:
            raise ValueError(
                "planned rounds must equal branch count times rounds per branch"
            )
        if self.archived_branch_count > self.branch_count:
            raise ValueError("archived branch count cannot exceed branch count")
        return self


class ResearchConfig(_ReadOnlyModel):
    """Configuration facts available from the paper and repository archive."""

    language: str
    model: str
    embedding_model: str
    memory_limit: int = Field(ge=1)
    global_time_limit: int = Field(ge=1)
    max_attempts: int = Field(ge=1)
    output_artifacts: tuple[str, ...]
    missing_reproducibility_fields: tuple[str, ...]


class ResearchVariable(_ReadOnlyModel):
    """A theoretical construct and its simulation operationalization."""

    id: str
    name: str
    role: Literal[
        "independent",
        "dependent",
        "mechanism",
        "moderator",
        "control",
        "context",
    ]
    theoretical_source: str
    operationalization: str
    measurement: str
    pdf_pages: tuple[int, ...] = ()


class ResearchIntervention(_ReadOnlyModel):
    """A timed intervention inherited by one formal experiment branch."""

    intervention_type: Literal[
        "technology_exposure",
        "policy_encouragement",
        "policy_restriction",
    ]
    global_time: str
    recipients: tuple[str, ...]
    intensity: Literal["none", "partial", "all", "staged"]
    direction: Literal["neutral", "encourage", "restrict", "mixed"]
    content: str
    pdf_pages: tuple[int, ...]


class ResearchBranch(_ReadOnlyModel):
    """One branch in the paper's five-branch counterfactual design."""

    id: str
    name: str
    branch_type: Literal[
        "natural_development",
        "partial_exposure",
        "full_exposure",
        "encouragement_policy",
        "mixed_policy",
    ]
    parent_id: str | None = None
    baseline: str
    interventions: tuple[ResearchIntervention, ...] = ()


class ArchiveTimeSlice(_ReadOnlyModel):
    """A non-overlapping time slice of one coded archive metric."""

    label: str
    starts_at: str
    ends_at: str
    count: int = Field(ge=0)


class ArchiveAgentCount(_ReadOnlyModel):
    """Coded count attributed to one agent's own action records."""

    agent: str
    count: int = Field(ge=0)


class ArchiveMetric(_ReadOnlyModel):
    """A compact, auditable secondary coding result."""

    id: str
    label: str
    numerator: int = Field(ge=0)
    denominator: int = Field(gt=0)
    coding_unit: Literal["primary_action"]
    temporal: tuple[ArchiveTimeSlice, ...]
    by_agent: tuple[ArchiveAgentCount, ...]
    interpretation: str
    source_paths: tuple[str, ...]

    @model_validator(mode="after")
    def validate_counts(self) -> "ArchiveMetric":
        if self.numerator > self.denominator:
            raise ValueError("metric numerator cannot exceed denominator")
        if sum(item.count for item in self.temporal) != self.numerator:
            raise ValueError("temporal counts must sum to metric numerator")
        if sum(item.count for item in self.by_agent) != self.numerator:
            raise ValueError("agent counts must sum to metric numerator")
        return self


class ResearchArchive(_ReadOnlyModel):
    """One archived branch for which primary-action records are available."""

    id: str
    repository_label: Literal["GE", "NA"]
    display_name: str
    total_actions: int = Field(gt=0)
    coverage: str
    interventions_from_archive: tuple[str, ...]
    metrics: tuple[ArchiveMetric, ...]
    source_paths: tuple[str, ...]

    @model_validator(mode="after")
    def validate_metric_denominators(self) -> "ResearchArchive":
        if any(item.denominator != self.total_actions for item in self.metrics):
            raise ValueError("metric denominator must equal archive total actions")
        return self


class ResearchFinding(_ReadOnlyModel):
    """A finding with an explicit evidence grade and rival explanations."""

    id: str
    title: str
    evidence_level: EvidenceLevel
    claim: str
    mechanism: str
    alternative_explanations: tuple[str, ...]
    pdf_pages: tuple[int, ...]
    archive_metric_ids: tuple[str, ...] = ()


class ResearchLimitation(_ReadOnlyModel):
    """A boundary on what the bundled case can support."""

    id: str
    description: str
    consequence: str
    pdf_pages: tuple[int, ...] = ()


class ResearchEvidenceExcerpt(_ReadOnlyModel):
    """A short traceable excerpt retained instead of the full raw archive."""

    id: str
    archive_id: str
    agent: str
    global_time: str
    excerpt: str
    supports: tuple[str, ...]
    evidence_level: EvidenceLevel
    source_path: str


class CodingRule(_ReadOnlyModel):
    """One deterministic rule used to derive an archive metric."""

    metric_id: str
    match_terms: tuple[str, ...]
    case_sensitive: bool = False


class ResearchCodingNotes(_ReadOnlyModel):
    """Method notes needed to reproduce the compact secondary coding."""

    unit: str
    deduplication: str
    rules: tuple[CodingRule, ...]
    exclusions: tuple[str, ...]
    cautions: tuple[str, ...]


class ResearchCase(_ReadOnlyModel):
    """Self-contained social-science case bundled with the offline showcase."""

    schema_version: Literal["1.0"] = "1.0"
    case_id: str
    title: str
    summary: str
    provenance: ResearchProvenance
    research_questions: tuple[ResearchQuestion, ...]
    scale: ResearchScale
    config: ResearchConfig
    variables: tuple[ResearchVariable, ...]
    branches: tuple[ResearchBranch, ...]
    archives: tuple[ResearchArchive, ...]
    findings: tuple[ResearchFinding, ...]
    limitations: tuple[ResearchLimitation, ...]
    evidence_excerpts: tuple[ResearchEvidenceExcerpt, ...]
    coding_notes: ResearchCodingNotes

    @model_validator(mode="after")
    def validate_references(self) -> "ResearchCase":
        branch_ids = {item.id for item in self.branches}
        archive_ids = {item.id for item in self.archives}
        finding_ids = {item.id for item in self.findings}
        metric_ids = {
            metric.id for archive in self.archives for metric in archive.metrics
        }
        if len(branch_ids) != len(self.branches):
            raise ValueError("research branch ids must be unique")
        if len(archive_ids) != len(self.archives):
            raise ValueError("research archive ids must be unique")
        if len(finding_ids) != len(self.findings):
            raise ValueError("research finding ids must be unique")
        if len(self.branches) != self.scale.branch_count:
            raise ValueError("branch records must match declared branch count")
        if len(self.archives) != self.scale.archived_branch_count:
            raise ValueError("archive records must match declared archive count")
        if any(
            item.parent_id is not None and item.parent_id not in branch_ids
            for item in self.branches
        ):
            raise ValueError("research branch parent must reference a known branch")
        if any(
            metric_id not in metric_ids
            for finding in self.findings
            for metric_id in finding.archive_metric_ids
        ):
            raise ValueError("finding references an unknown archive metric")
        if any(item.archive_id not in archive_ids for item in self.evidence_excerpts):
            raise ValueError("evidence excerpt references an unknown archive")
        if any(
            finding_id not in finding_ids
            for item in self.evidence_excerpts
            for finding_id in item.supports
        ):
            raise ValueError("evidence excerpt references an unknown finding")
        return self


class ShowcaseManifest(_ReadOnlyModel):
    """Top-level contract for a self-contained, read-only showcase demo."""

    schema_version: Literal["1.0"] = "1.0"
    project_id: str
    title: str
    summary: str
    source: ShowcaseSource
    agents: list[ShowcaseAgent]
    locations: list[ShowcaseLocation]
    steps: list[ShowcaseStep]
    # Research-only showcases may intentionally omit normalized event logs;
    # their evidence is carried by the validated ResearchCase archives.
    event_log: str | None = None
    research_case: str | None = None
    available_metrics: list[str]
    migration_warnings: list[str]
