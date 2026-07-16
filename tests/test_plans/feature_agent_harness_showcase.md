# Test Plan: Agent / Harness 展示

## Setup

- 启动 Streamlit 展示页。
- 不设置 API key，不启动仿真模型。

## Test Cases

### TC-001: 保留旧展示

- **Steps**:
  1. 选择“研究档案”。
  2. 依次打开“项目总览”和“实验设计”。
- **Expected**: 原有研究档案可正常打开，页面内容和论文分支选择器仍可用。
- **Priority**: P0

### TC-002: Harness 主线

- **Steps**:
  1. 选择“Agent / Harness”。
  2. 打开“Harness 设计”和“协作协议”。
- **Expected**: 首屏出现六阶段 Agent 闭环；可看到 AgentAction、MemoryEntry、ReflectionEngine、FOV、InteractionCoordinator 和 PathPlanner 的代码证据。
- **Priority**: P0

### TC-003: Prompt 实验

- **Steps**:
  1. 打开“Prompt 实验”。
  2. 切换至少两个实验分支。
- **Expected**: 人设、环境、记忆、事件四层输入保持可见；分支只读展示继承关系、时间、对象、强度和方向。
- **Priority**: P0

### TC-004: 结果证据

- **Steps**:
  1. 打开“结果证据”。
- **Expected**: 先显示四人小镇论文基线，再显示校园 GE / NA 归档摘要；不出现模型调用或因果效应声称。
- **Priority**: P1

## Regression Check

- [ ] 研究档案和实验工作台仍可切换。
- [ ] 无 API key 时没有错误堆栈。
- [ ] Streamlit AppTest 无异常。
