## Project Description

The project aims to simulate social interactions and agent behavior, providing a customizable framework for the study and exploration of various social scenarios. Through simulation, you can observe interactions between agents, analyze behavioral patterns, and gain a deeper understanding of social dynamics.

## Environment Setup

Please follow these steps to set up your environment:

1. **Create Conda Environment (Optional):** If you wish to use a Conda environment, execute the following command:

   ```bash
   00_condaCreate.bat
   ```

   This will create a Conda environment named `env`.

2. **Activate Conda Environment (if used):** If you created a Conda environment, activate it.

3. **Install Dependencies:** Use the following command to install the project dependencies:

   ```bash
   env\python.exe -m pip install -r requirements.txt
   ```

4. **Configure OpenAI API Key:**

   *   Add your OpenAI API key to the `simulation/utils/config.py` file under the `openai_api_key` variable.
   *   You can also adjust `openai_base_url`, `key_owner`, and `DefaultModel` according to your needs.

## Running the Simulation

Follow these steps to run the simulation:

1. **Run the Main Program:** Execute the `simulation/main.py` file.
    *   Alternatively, you can run the `test_main.py` file with `01_testMain.bat` for testing.
2. **Enter Project Name:** The program will prompt you to enter the project name.
3. **Enter Simulation Repetitions:** The program will prompt you to input the number of times to repeat the simulation.

## Simulation Storage Location

Simulation data is stored in the following location(s):

*   **Project Directory:** `projects/{project_name}/`, where `{project_name}` is the project name you input when running the simulation.
*   **Simulation Log:** `projects/{project_name}/simulation_log.txt`
*   **Simulation Summary:** `projects/{project_name}/simulation_summary.txt`

## Customization

You can customize the simulation in the following ways:

1. **Modify Town Data:** After generating the project, change the `town_data.json` file in `simulation/project/<your project name>/` to modify town data.
2. **Modify Code:** Change the code in the `simulation/main.py` file to alter simulation behavior.
3. **Modify Configuration Files:** Adjust configurations in `simulation/utils/config.py` such as OpenAI API key and default model.
4. **Modify Agent Behavior:** Change agent behavior by modifying the files in the `simulation/agents/` directory.
5. **Modify Locations:** Modify the files in the `simulation/locations/` directory to alter the management of the simulation world locations.
6. **Modify Memory:** Change the memory management by modifying the files in the `simulation/retrieve/` directory.

Module descriptions can be found in:

## Authors and References

Huang Miaosen 黄淼森

## Acknowledgments

*   [https://github.com/joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents), the License is attached in the License folder.
*   [https://github.com/mkturkcan/generative-agents](https://github.com/mkturkcan/generative-agents), only serves as a reference for the overall idea based on the paper, and the Copy code is used.