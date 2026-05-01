@echo off
REM 高级配置运行Claude Code

REM 设置自定义API
set ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
set ANTHROPIC_AUTH_TOKEN=4a2f43455b6091c79f4c1bead1dd947f.dWJMm8ggQDHsXE6y
set API_TIMEOUT_MS=3000000
set ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
set ANTHROPIC_DEFAULT_SONNET_MODEL=glm-5-turbo
set ANTHROPIC_DEFAULT_OPUS_MODEL=glm-5.1
set CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1

REM 可选：设置其他环境变量
@REM set HTTPS_PROXY=http://your-proxy:port

REM 设置权限模式
@REM set CLAUDE_PERMISSION_MODE=plan

REM 添加额外的工作目录
@REM claude --add-dir ../shared-libraries ../common-components

cd %~dp0
claude

pause