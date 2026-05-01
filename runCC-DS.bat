@echo off
REM 高级配置运行Claude Code

REM 设置自定义API
set ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
set ANTHROPIC_AUTH_TOKEN=sk-82117bb5e45645b68ea233e4457a7c53
set API_TIMEOUT_MS=600000
set ANTHROPIC_MODEL=deepseek-v4-pro[1m]
set ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro[1m]
set ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro[1m]
set ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
set CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
set CLAUDE_CODE_EFFORT_LEVEL=max
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