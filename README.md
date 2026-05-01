=======
## Project Description

The project aims to simulate social interactions and agent behavior, providing a customizable framework for the study and exploration of various social scenarios. Through simulation, you can observe interactions between agents, analyze behavioral patterns, and gain a deeper understanding of social dynamics.

## Project Structure

```
SocialSimuLLM/
├── pyproject.toml                # Project config & dependencies
├── src/socialsimullm/            # Source package
│   ├── __main__.py               # Entry point
│   ├── agents/                   # Agent behavior & memory actions
│   ├── locations/                # Location management
│   ├── prompt_templates/         # Prompt templates for LLM
│   ├── retrieve/                 # Memory retrieval & reflection
│   ├── utils/                    # Config, text generation, helpers
│   └── data/                     # Template data files
├── tests/                        # Test files
├── projects/                     # Simulation output data
└── docs/                         # Documentation
```

## Environment Setup

1. **Install Dependencies:** [uv](https://docs.astral.sh/uv/) is used for dependency management. Install dependencies with:

   ```bash
   uv sync
   ```

2. **Configure OpenAI API Key:**

   *   Prepare an API containing models for `completions`.
   *   Add your OpenAI API key to `src/socialsimullm/utils/config.py` under the `openai_api_key` variable.
   *   You can also adjust `openai_base_url`, `key_owner`, and `DefaultModel` according to your needs.

## Running the Simulation

1. **Run the Main Program:** Execute from the project root directory:

   ```bash
   uv run python -m socialsimullm
   ```

   Or use the script entry point:

   ```bash
   uv run socialsimullm
   ```

2. **Enter Project Name:** The program will prompt you to enter the project name.
   *   **Note:** The project can be continued, but it is advisable to implement incremental backups to prevent data loss.
3. **Enter Simulation Repetitions:** The program will prompt you to input the number of times to repeat the simulation.

## Simulation Storage Location

Simulation data is stored in the following location(s):

*   **Project Directory:** `projects/{project_name}/`, where `{project_name}` is the project name you input when running the simulation.
*   **Simulation Log:** `projects/{project_name}/simulation_log.txt`
*   **Simulation Summary:** `projects/{project_name}/simulation_summary.txt`
*   **Agent Memory:** `projects/{project_name}/agent_data/`

## Customization

You can customize the simulation in the following ways:

1. **Modify Town Data:** After generating the project, change the `town_data.json` file in `projects/<your project name>/` to modify town data.
2. **Modify Code:** Change the code in `src/socialsimullm/__main__.py` to alter simulation behavior.
3. **Modify Configuration Files:** Adjust configurations in `src/socialsimullm/utils/config.py` such as OpenAI API key and default model.
4. **Modify Agent Behavior:** Change agent behavior by modifying the files in `src/socialsimullm/agents/` directory.
5. **Modify Locations:** Modify the files in `src/socialsimullm/locations/` directory to alter the management of the simulation world locations.
6. **Modify Memory:** Change the memory management by modifying the files in `src/socialsimullm/retrieve/` directory.
7. **Modify Prompt Templates:** Edit `src/socialsimullm/prompt_templates/template_agents.py` to change how agents interact with LLMs.

Module descriptions can be found in: [Module_Description.md](/docs/Module_Description.md)

## Update Introduction

In the V3.1 version, the project was restructured to a modern Python `src` layout with `pyproject.toml` for dependency management via `uv`. Deprecated files were removed, imports were updated to use proper package paths, and test files were consolidated into a `tests/` directory.

In the V3.0 version, the project underwent significant updates, primarily focusing on enhancing the agent's memory and reflection capabilities, as well as optimizing the simulated prompts. This improvement boosts the agent's learning capacity, adaptability, and decision-making quality.

Updated documentation can be found in: [Update-v3.0-20250223.md](/docs/Update-v3.0-20250223.md)

In the V2.0 version, the project underwent significant updates, including optimizing memory retrieval, improving agent state evaluation, refining memory management, laying the groundwork for database interaction, and optimizing the main program and Prompt.

Updated documentation can be found in: [Update-v2.0-20250222.md](/docs/Update-v2.0-20250222.md)

## Authors and References

Huang Miaosen

## Acknowledgments

- [https://github.com/mkturkcan/generative-agents](https://github.com/mkturkcan/generative-agents), part of the code source, the license is attached in the License folder
- [https://github.com/joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents), only for reference of the idea according to the paper, no copying of the code
