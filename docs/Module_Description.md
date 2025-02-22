## Module Description

The project contains the following main modules:

*   **`simulation/main.py`**: Contains the main program of the simulation.
    *   Initializes global variables and modules.
    *   Loads project data.
    *   Creates a map of the city.
    *   Creates agents.
    *   Runs the simulation loop, including daily planning, hourly planning, executing actions, updating memory, evaluating positions, and saving data.
*   **`simulation/agents/`**: Contains the `Agent` class, used to define agents in the simulation.
    *   The `Agent` class includes the following main methods:
        *   `daily_planning`: Daily planning.
        *   `hourly_planning`: Hourly planning.
        *   `execute_action`: Executes actions.
        *   `rate_experience`: Evaluates experience.
        *   `format_experience`: Formats experience.
        *   `rate_locations`: Evaluates positions.
        *   `move`: Moves.
*   **`simulation/locations/`**: Contains the `Location` and `Locations` classes, used to define positions in the simulation.
    *   The `Location` class represents a single location.
    *   The `Locations` class manages all locations.
*   **`simulation/retrieve/`**: Contains the `Memory` class, used to manage an agent's memory.
    *   The `Memory` class includes the following main methods:
        *   `load_memory_file`: Loads a memory file.
        *   `save_memory_file`: Saves a memory file.
        *   `add_experience`: Adds experience.
        *   `get_newthings`: Gets new things.
        *   `format_newthings`: Formats new things.
        *   `get_newthings_str`: Gets new things as a string.
*   **`simulation/utils/`**: Contains utility functions and configurations.
    *   `config.py`: Contains configuration information such as the OpenAI API key and default model.
    *   `global_methods.py`: Contains global methods, such as loading and saving metadata, loading city data, etc.
    *   `text_generation.py`: Contains text generation related functions, such as GPT requests, getting embeddings, etc.