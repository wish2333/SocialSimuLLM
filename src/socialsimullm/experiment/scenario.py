# socialsimullm/experiment/scenario.py

# -*- coding: utf-8 -*-

"""
Natural language scenario construction for SocialSimuLLM.

Provides ScenarioGenerator that creates complete town_data.json files
from natural language descriptions using LLM synthesis.

@author: Huang Miaosen
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from socialsimullm.utils.text_generation import GPT_request

SCENARIO_GENERATION_SYSTEM = """You are a world-building assistant for a social simulation.
Given a scenario description, generate a complete town_data.json structure.

The JSON must have exactly this structure:
{
  "general": {
    "global_time_limit": 24,
    "max_attempts": 2,
    "memory_limit": 10,
    "prompt_meta": "### Instruction:\\n{}\\n### Response:"
  },
  "town_areas": {
    "<Area Name>": "<Area description. 1-2 sentences describing the location.>",
    ...
  },
  "town_people": {
    "<Character Name>": {
      "description": "<Detailed character description including personality, background, and motivations. 2-4 sentences.>",
      "starting_location": "<One of the area names above>"
    },
    ...
  }
}

Rules:
- Generate 3-7 town areas that make sense together
- Generate 3-8 characters with distinct personalities
- Each character's starting_location must be one of the town_areas keys
- Characters should have relationships and potential for interaction
- Descriptions should be rich enough to drive interesting simulation behavior
- Output ONLY valid JSON, no markdown, no explanation"""

SCENARIO_GENERATION_PROMPT = """Generate a town_data.json for this scenario:

{scenario_description}

Requirements:
- {min_agents} to {max_agents} characters
- {min_areas} to {max_areas} locations
- Characters should have diverse personalities and motivations

Output the complete JSON:"""

SCENARIO_REFINE_SYSTEM = """You are a world-building assistant reviewing a simulation setup.

Given an existing town_data.json and user feedback, produce an improved version.
Fix any issues mentioned in the feedback while preserving what works.
Output ONLY valid JSON, no markdown, no explanation.

Existing town_data.json:
{existing_data}

Feedback:
{feedback}"""

SCENARIO_VALIDATE_SYSTEM = """You are a simulation data validator.
Review this town_data.json for issues that would cause problems in a
social simulation engine. Check for:
1. Every starting_location matches a town_areas key
2. Character descriptions are substantive (not empty or generic)
3. Area descriptions provide enough context for agent behavior
4. No duplicate names
5. Character motivations allow for meaningful interactions

Output a JSON array of issue objects:
[{"severity": "error|warning|info", "field": "path.to.field", "message": "description"}]

town_data.json:
{town_data}"""


class ScenarioGenerator:
    """Generates simulation town_data.json from natural language descriptions.

    Uses LLM synthesis to create complete world configurations with
    locations, characters, and their starting positions.

    Usage::

        gen = ScenarioGenerator(prompt_meta)
        town_data = gen.generate("A medieval marketplace with 5 merchants")
        gen.save(town_data, "projects/my_scenario/town_data.json")
    """

    def __init__(
        self,
        prompt_meta: str = "### Instruction:\n{}\n### Response:",
        min_agents: int = 3,
        max_agents: int = 8,
        min_areas: int = 3,
        max_areas: int = 7,
    ) -> None:
        self._prompt_meta = prompt_meta
        self._min_agents = min_agents
        self._max_agents = max_agents
        self._min_areas = min_areas
        self._max_areas = max_areas

    def generate(self, scenario_description: str) -> dict[str, Any]:
        """Generate a complete town_data.json dict from a scenario description.

        Args:
            scenario_description: Natural language description of the
                desired simulation scenario.

        Returns:
            A dict matching the town_data.json schema.
        """
        system = SCENARIO_GENERATION_SYSTEM
        prompt = SCENARIO_GENERATION_PROMPT.format(
            scenario_description=scenario_description,
            min_agents=self._min_agents,
            max_agents=self._max_agents,
            min_areas=self._min_areas,
            max_areas=self._max_areas,
        )

        response = GPT_request(
            system,
            self._prompt_meta.format(prompt),
            gpt_parameter={"max_tokens": 1000, "temperature": 0.8},
        )

        return self._parse_json_response(response)

    def refine(
        self,
        scenario_description: str,
        feedback: str,
        existing_town_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Refine an existing town_data.json based on feedback.

        Args:
            scenario_description: Original scenario description.
            feedback: User feedback on what to change.
            existing_town_data: The current town_data.json to improve.

        Returns:
            An improved town_data.json dict.
        """
        prompt = SCENARIO_REFINE_SYSTEM.format(
            existing_data=json.dumps(existing_town_data, indent=2, ensure_ascii=False),
            feedback=feedback,
        )

        response = GPT_request(
            SCENARIO_GENERATION_SYSTEM,
            self._prompt_meta.format(prompt),
            gpt_parameter={"max_tokens": 1000, "temperature": 0.7},
        )

        return self._parse_json_response(response)

    def validate_town_data(self, town_data: dict[str, Any]) -> list[dict[str, str]]:
        """Validate a town_data.json dict for structural correctness.

        Uses both static checks and LLM-based validation.

        Args:
            town_data: The town_data dict to validate.

        Returns:
            List of issue dicts with keys: severity, field, message.
        """
        issues = self._static_validation(town_data)

        llm_issues = self._llm_validation(town_data)
        issues.extend(llm_issues)

        return issues

    def save(self, town_data: dict[str, Any], path: str | Path) -> None:
        """Save town_data to a JSON file.

        Args:
            town_data: The town_data dict to save.
            path: Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(town_data, f, indent=2, ensure_ascii=False)

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response, extracting JSON from potential markdown."""
        text = response.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            brace_start = text.find("{")
            brace_end = text.rfind("}")
            if brace_start >= 0 and brace_end > brace_start:
                data = json.loads(text[brace_start:brace_end + 1])
            else:
                raise ValueError(
                    "Failed to parse JSON from LLM response. "
                    "Raw response (first 200 chars): " + text[:200]
                )

        return self._normalize_structure(data)

    def _normalize_structure(self, data: dict[str, Any]) -> dict[str, Any]:
        """Ensure the data matches expected town_data.json structure."""
        if "general" not in data:
            data["general"] = {
                "global_time_limit": 24,
                "max_attempts": 2,
                "memory_limit": 10,
                "prompt_meta": "### Instruction:\n{}\n### Response:",
            }

        general = data["general"]
        for key, default in [
            ("global_time_limit", 24),
            ("max_attempts", 2),
            ("memory_limit", 10),
        ]:
            if key not in general:
                general[key] = default

        if "town_areas" not in data or not data["town_areas"]:
            data["town_areas"] = {
                "Town Square": "A central gathering place.",
            }
        if "town_people" not in data or not data["town_people"]:
            data["town_people"] = {
                "Villager": {
                    "description": "A simple villager.",
                    "starting_location": list(data["town_areas"].keys())[0],
                },
            }

        valid_locations = set(data["town_areas"].keys())
        for name, person in data["town_people"].items():
            if not isinstance(person, dict):
                data["town_people"][name] = {"description": str(person), "starting_location": list(valid_locations)[0]}
                continue
            if "starting_location" not in person or person["starting_location"] not in valid_locations:
                person["starting_location"] = list(valid_locations)[0]
            if "description" not in person:
                person["description"] = f"{name} is a resident of the town."

        return data

    def _static_validation(self, town_data: dict[str, Any]) -> list[dict[str, str]]:
        """Run static structural checks on town_data."""
        issues: list[dict[str, str]] = []
        valid_locations = set(town_data.get("town_areas", {}).keys())

        if not valid_locations:
            issues.append({
                "severity": "error",
                "field": "town_areas",
                "message": "No town areas defined.",
            })

        people = town_data.get("town_people", {})
        if not people:
            issues.append({
                "severity": "error",
                "field": "town_people",
                "message": "No characters defined.",
            })

        for name, person in people.items():
            if not isinstance(person, dict):
                issues.append({
                    "severity": "error",
                    "field": f"town_people.{name}",
                    "message": f"Character '{name}' is not a dict.",
                })
                continue

            loc = person.get("starting_location", "")
            if loc not in valid_locations:
                issues.append({
                    "severity": "error",
                    "field": f"town_people.{name}.starting_location",
                    "message": f"Location '{loc}' not found in town_areas.",
                })

            desc = person.get("description", "")
            if len(desc) < 10:
                issues.append({
                    "severity": "warning",
                    "field": f"town_people.{name}.description",
                    "message": "Description is too short for meaningful behavior.",
                })

        names = list(people.keys())
        if len(names) != len(set(names)):
            dupes = [n for n in names if names.count(n) > 1]
            issues.append({
                "severity": "error",
                "field": "town_people",
                "message": f"Duplicate character names: {set(dupes)}",
            })

        return issues

    def _llm_validation(self, town_data: dict[str, Any]) -> list[dict[str, str]]:
        """Run LLM-based validation for semantic issues."""
        prompt = SCENARIO_VALIDATE_SYSTEM.format(
            town_data=json.dumps(town_data, indent=2, ensure_ascii=False)
        )

        try:
            response = GPT_request(
                SCENARIO_VALIDATE_SYSTEM,
                self._prompt_meta.format(prompt),
                gpt_parameter={"max_tokens": 200, "temperature": 0.3},
            )
            return self._parse_validation_response(response)
        except Exception:
            return []

    @staticmethod
    def _parse_validation_response(response: str) -> list[dict[str, str]]:
        """Parse LLM validation response into issue dicts."""
        import re

        issues: list[dict[str, str]] = []

        pattern = r'\{\s*"severity"\s*:\s*"(\w+)"\s*,\s*"field"\s*:\s*"([^"]+)"\s*,\s*"message"\s*:\s*"([^"]+)"\s*\}'
        matches = re.findall(pattern, response)

        for severity, field, message in matches:
            issues.append({
                "severity": severity,
                "field": field,
                "message": message,
            })

        return issues
