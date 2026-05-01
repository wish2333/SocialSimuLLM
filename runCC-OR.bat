@echo off
REM 高级配置运行Claude Code

REM 设置自定义API
set ANTHROPIC_BASE_URL=https://openrouter.ai/api
set ANTHROPIC_AUTH_TOKEN=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
set API_TIMEOUT_MS=600000
set ANTHROPIC_MODEL=tencent/hy3-preview:free
set ANTHROPIC_SMALL_FAST_MODEL=tencent/hy3-preview:free
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