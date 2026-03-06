"""Shell command execution tool."""

import shlex
import typing as t

from mcp.types import ToolAnnotations
from pydantic import Field

from linux_mcp_server.audit import log_tool_call
from linux_mcp_server.config import CONFIG
from linux_mcp_server.connection.ssh import execute_with_fallback
from linux_mcp_server.server import mcp
from linux_mcp_server.utils.types import Host


@mcp.tool(
    title="Execute command",
    description=(
        "Execute a shell command on a remote host via SSH. "
        "Requires LINUX_MCP_EXECUTE_ENABLED=true. "
        "If LINUX_MCP_ALLOWED_COMMANDS is set, only whitelisted binaries are permitted. "
        "Returns stdout, stderr and exit code."
    ),
    tags={"execute", "shell"},
    annotations=ToolAnnotations(readOnlyHint=False),
)
@log_tool_call
async def execute_command(
    command: t.Annotated[
        str,
        Field(
            description=(
                "Shell command to execute (e.g. 'curl -s http://localhost:32400', "
                "'python3 -c \"import sys; print(sys.version)\"')"
            ),
            examples=["curl -s http://localhost:32400", "python3 --version", "pip install plexapi"],
        ),
    ],
    host: Host = None,
    timeout: t.Annotated[
        int,
        Field(
            description="Command timeout in seconds (default: 30, max: 300)",
            ge=1,
            le=300,
        ),
    ] = 30,
) -> str:
    """Execute a shell command on the target host.

    Security controls (via environment variables):
    - LINUX_MCP_EXECUTE_ENABLED=true   required to enable this tool at all
    - LINUX_MCP_ALLOWED_COMMANDS=curl,python3   comma-separated whitelist of
      allowed binaries; if empty, all commands are permitted

    Returns stdout, stderr and exit code.
    """
    # --- Guard: tool must be explicitly enabled ---
    if not CONFIG.execute_enabled:
        return (
            "ERROR: execute_command is disabled. "
            "Set LINUX_MCP_EXECUTE_ENABLED=true to enable it."
        )

    # --- Guard: whitelist check ---
    allowed = CONFIG.allowed_commands_list
    if allowed:
        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            return f"ERROR: Failed to parse command: {exc}"

        if not tokens:
            return "ERROR: Empty command."

        # The first token is the binary (or a path to it – take the basename)
        import os
        binary = os.path.basename(tokens[0])

        if binary not in allowed:
            return (
                f"ERROR: '{binary}' is not in the allowed commands whitelist. "
                f"Allowed: {', '.join(allowed)}"
            )

    # --- Execute ---
    args = ("bash", "-c", command)
    returncode, stdout, stderr = await execute_with_fallback(args, host=host)

    stdout = stdout if isinstance(stdout, str) else stdout.decode("utf-8", errors="replace")
    stderr = stderr if isinstance(stderr, str) else stderr.decode("utf-8", errors="replace")

    result_parts = []
    if stdout.strip():
        result_parts.append(f"STDOUT:\n{stdout.strip()}")
    if stderr.strip():
        result_parts.append(f"STDERR:\n{stderr.strip()}")
    result_parts.append(f"Exit code: {returncode}")

    return "\n\n".join(result_parts) if result_parts else f"Command completed with exit code {returncode}"
