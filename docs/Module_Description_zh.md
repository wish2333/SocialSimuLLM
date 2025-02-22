## 模块说明

该项目包含以下主要模块：

*   **`simulation/main.py`**: 包含模拟的主程序。
    *   初始化全局变量和模块。
    *   加载项目数据。
    *   创建城镇图。
    *   创建智能体。
    *   运行模拟循环，包括每日规划、每小时规划、执行动作、更新记忆、评估位置和保存数据。
*   **`simulation/agents/`**: 包含 `Agent` 类，用于定义模拟中的智能体。
    *   `Agent` 类具有以下主要方法：
        *   `daily_planning`: 每日规划。
        *   `hourly_planning`: 每小时规划。
        *   `execute_action`: 执行动作。
        *   `rate_experience`: 评估经验。
        *   `format_experience`: 格式化经验。
        *   `rate_locations`: 评估位置。
        *   `move`: 移动。
*   **`simulation/locations/`**: 包含 `Location` 和 `Locations` 类，用于定义模拟中的位置。
    *   `Location` 类表示单个位置。
    *   `Locations` 类管理所有位置。
*   **`simulation/retrieve/`**: 包含 `Memory` 类，用于管理智能体的记忆。
    *   `Memory` 类具有以下主要方法：
        *   `load_memory_file`: 加载记忆文件。
        *   `save_memory_file`: 保存记忆文件。
        *   `add_experience`: 添加经验。
        *   `get_newthings`: 获取新事物。
        *   `format_newthings`: 格式化新事物。
        *   `get_newthings_str`: 获取新事物字符串。
*   **`simulation/utils/`**: 包含实用工具函数和配置。
    *   `config.py`: 包含配置信息，例如 OpenAI API 密钥和默认模型。
    *   `global_methods.py`: 包含全局方法，例如加载和保存元数据、加载城镇数据等。
    *   `text_generation.py`: 包含文本生成相关函数，例如 GPT 请求、获取嵌入等。