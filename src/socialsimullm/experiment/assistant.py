# socialsimullm/experiment/assistant.py

# -*- coding: utf-8 -*-

"""
Semi-auto research assistant for SocialSimuLLM.

Provides ResearchAssistant that uses LLM analysis to summarize experiments,
identify behavioral patterns, suggest hypotheses, compare runs, and generate
research reports.

@author: Huang Miaosen
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from socialsimullm.experiment.analysis import (
    get_experiment_summary,
    load_results,
)
from socialsimullm.utils.text_generation import GPT_request

SUMMARIZE_SYSTEM = """You are a research assistant analyzing social simulation data.
Given experiment summary data, provide a concise but informative summary
of what happened in this simulation. Focus on:
- Overall simulation duration and scope
- Agent behavior patterns
- Notable events or interactions
- Key findings

Keep the summary under 300 words."""

PATTERNS_SYSTEM = """You are a research assistant analyzing social simulation data.
Given aggregated event data from an experiment, identify notable behavioral
patterns. Look for:
- Recurring agent behaviors
- Temporal activity patterns
- Inter-agent dynamics
- Location preferences
- Anomalies or unexpected behaviors

Return a list of pattern observations, one per line.
Prefix each with a category tag: [MOVEMENT], [INTERACTION], [TEMPORAL], [ANOMALY], [SOCIAL]"""

HYPOTHESIS_SYSTEM = """You are a research assistant helping formulate hypotheses
for social simulation experiments.

Given the observed patterns and experiment context, suggest testable hypotheses
that could be explored in future experiments. Each hypothesis should be:
- Specific and measurable
- Grounded in the observed data
- Actionable (can be tested by modifying experiment config)

Format: one hypothesis per line, prefixed with H1, H2, etc."""

COMPARE_SYSTEM = """You are a research assistant comparing multiple simulation runs.
Given summary statistics from multiple experiments, identify:
- Key differences between runs
- Config factors that most impact behavior
- Unexpected similarities or differences
- Recommendations for further investigation

Provide a structured comparison under 400 words."""

REPORT_SYSTEM = """You are a research assistant writing a simulation experiment report.
Given experiment data, patterns, and hypotheses, write a structured report
with these sections:
1. Overview - experiment setup and duration
2. Key Findings - main discoveries from the data
3. Behavioral Patterns - agent behavior analysis
4. Comparison Insights - how different configs affect outcomes
5. Hypotheses - testable hypotheses for future work
6. Recommendations - suggested next experiments

Keep each section concise. Total report under 800 words."""


class ResearchAssistant:
    """LLM-powered research assistant for experiment analysis.

    Analyzes experiment data to provide summaries, identify patterns,
    suggest hypotheses, compare runs, and generate reports.

    Usage::

        assistant = ResearchAssistant(prompt_meta)
        summary = assistant.summarize_experiment("exp_abc123")
        patterns = assistant.identify_patterns("exp_abc123")
        report = assistant.generate_report("exp_abc123")
    """

    def __init__(
        self,
        prompt_meta: str = "### Instruction:\n{}\n### Response:",
    ) -> None:
        self._prompt_meta = prompt_meta

    def summarize_experiment(
        self,
        experiment_id: str,
        project: str | None = None,
    ) -> str:
        """Generate a natural language summary of an experiment.

        Args:
            experiment_id: The experiment identifier.
            project: Optional project name.

        Returns:
            Summary text from the LLM.
        """
        try:
            summary = get_experiment_summary(experiment_id, project)
        except FileNotFoundError:
            return f"Error: Experiment '{experiment_id}' not found."
        events = load_results(experiment_id, project)

        event_samples = []
        for e in events[:30]:
            data = e.get("data", {})
            if isinstance(data, dict):
                snippet = str(data.get("action", data.get("plan", data.get("reflection", ""))))[:60]
            else:
                snippet = str(data)[:60]
            event_samples.append(f"[{e.get('agent_id')}] {e.get('event_type')}: {snippet}")

        prompt = (
            f"Experiment: {experiment_id}\n"
            f"Total steps: {summary['total_steps']}\n"
            f"Total events: {summary['total_events']}\n"
            f"Agents: {', '.join(summary['agent_names'])}\n"
            f"Event distribution: {summary['event_type_counts']}\n"
            f"\nSample events:\n" + "\n".join(event_samples[:20])
        )

        return GPT_request(
            SUMMARIZE_SYSTEM,
            self._prompt_meta.format(prompt),
            gpt_parameter={"max_tokens": 400},
        )

    def identify_patterns(
        self,
        experiment_id: str,
        project: str | None = None,
    ) -> list[str]:
        """Identify behavioral patterns in an experiment.

        Args:
            experiment_id: The experiment identifier.
            project: Optional project name.

        Returns:
            List of pattern description strings.
        """
        events = load_results(experiment_id, project)

        type_counts = Counter(e.get("event_type", "") for e in events)
        agent_counts = Counter(e.get("agent_id", "") for e in events if e.get("agent_id"))

        movement_data = []
        for e in events:
            if e.get("event_type") == "movement":
                data = e.get("data", {})
                if isinstance(data, dict):
                    movement_data.append(
                        f"{e.get('agent_id')}: {data.get('from')} -> {data.get('to')}"
                    )

        prompt = (
            f"Event types: {dict(type_counts)}\n"
            f"Agent activity: {dict(agent_counts.most_common(10))}\n"
            f"Movement samples: {'; '.join(movement_data[:15])}\n"
            f"Total events: {len(events)}"
        )

        response = GPT_request(
            PATTERNS_SYSTEM,
            self._prompt_meta.format(prompt),
            gpt_parameter={"max_tokens": 300},
        )

        return [line.strip() for line in response.strip().split("\n") if line.strip()]

    def suggest_hypotheses(
        self,
        experiment_id: str,
        project: str | None = None,
    ) -> list[str]:
        """Suggest testable hypotheses based on experiment data.

        Args:
            experiment_id: The experiment identifier.
            project: Optional project name.

        Returns:
            List of hypothesis strings.
        """
        summary = get_experiment_summary(experiment_id, project)
        events = load_results(experiment_id, project)

        action_texts: list[str] = []
        for e in events:
            if e.get("event_type") == "action":
                data = e.get("data", {})
                if isinstance(data, dict):
                    action_texts.append(str(data.get("action", ""))[:50])

        top_actions = Counter(action_texts).most_common(5)

        prompt = (
            f"Experiment: {experiment_id}\n"
            f"Agents: {summary['agent_names']}\n"
            f"Steps: {summary['total_steps']}\n"
            f"Event distribution: {dict(summary['event_type_counts'])}\n"
            f"Most common actions: {top_actions}\n"
            f"\nSuggest testable hypotheses for future experiments."
        )

        response = GPT_request(
            HYPOTHESIS_SYSTEM,
            self._prompt_meta.format(prompt),
            gpt_parameter={"max_tokens": 200},
        )

        return [line.strip() for line in response.strip().split("\n") if line.strip()]

    def compare_runs(
        self,
        experiment_ids: list[str],
        project: str | None = None,
    ) -> str:
        """Compare multiple experiment runs.

        Args:
            experiment_ids: List of experiment IDs to compare.
            project: Optional project name.

        Returns:
            Comparison analysis text.
        """
        summaries: list[str] = []
        for eid in experiment_ids:
            try:
                s = get_experiment_summary(eid, project)
                summaries.append(
                    f"Experiment {eid}: "
                    f"{s['total_steps']} steps, {s['total_events']} events, "
                    f"agents={s['agent_names']}, "
                    f"types={dict(s['event_type_counts'])}"
                )
            except FileNotFoundError:
                summaries.append(f"Experiment {eid}: NOT FOUND")

        prompt = "\n".join(summaries)
        return GPT_request(
            COMPARE_SYSTEM,
            self._prompt_meta.format(prompt),
            gpt_parameter={"max_tokens": 500},
        )

    def generate_report(
        self,
        experiment_id: str,
        project: str | None = None,
    ) -> str:
        """Generate a comprehensive research report for an experiment.

        Args:
            experiment_id: The experiment identifier.
            project: Optional project name.

        Returns:
            Formatted report text.
        """
        summary = self.summarize_experiment(experiment_id, project)
        patterns = self.identify_patterns(experiment_id, project)
        hypotheses = self.suggest_hypotheses(experiment_id, project)

        exp_summary = get_experiment_summary(experiment_id, project)

        prompt = (
            f"Experiment: {experiment_id}\n"
            f"Setup: {exp_summary['total_steps']} steps, "
            f"{len(exp_summary['agent_names'])} agents\n\n"
            f"Summary: {summary}\n\n"
            f"Patterns:\n" + "\n".join(f"  {p}" for p in patterns) + "\n\n"
            f"Hypotheses:\n" + "\n".join(f"  {h}" for h in hypotheses)
        )

        return GPT_request(
            REPORT_SYSTEM,
            self._prompt_meta.format(prompt),
            gpt_parameter={"max_tokens": 800},
        )
