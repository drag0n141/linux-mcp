"""Tail file tool."""

import typing as t

from mcp.types import ToolAnnotations
from pydantic import Field

from linux_mcp_server.audit import log_tool_call
from linux_mcp_server.connection.ssh import execute_with_fallback
from linux_mcp_server.server import mcp
from linux_mcp_server.utils.types import Host


@mcp.tool(
    title="Tail file",
    description=(
        "Read the last N lines of a file on a remote host via SSH. "
        "Always available, no configuration required. "
        "Returns the last N lines of the file."
    ),
    tags={"files", "logs", "tail"},
    annotations=ToolAnnotations(readOnlyHint=True),
)
@log_tool_call
async def tail_file(
    path: t.Annotated[
        str,
        Field(
            description="Absolute path to the file to tail",
            examples=["/var/log/syslog", "/var/log/nginx/access.log", "/tmp/app.log"],
        ),
    ],
    lines: t.Annotated[
        int,
        Field(
            description="Number of lines to return from the end of the file (default: 100, max: 10000)",
            ge=1,
            le=10000,
        ),
    ] = 100,
    host: Host = None,
) -> str:
    """Read the last N lines of a file on the target host.

    No configuration required - always available.
    Returns the last N lines of the file as plain text.
    """
    args = ("tail", "-n", str(lines), path)
    returncode, stdout, stderr = await execute_with_fallback(args, host=host)

    stdout = stdout if isinstance(stdout, str) else stdout.decode("utf-8", errors="replace")
    stderr = stderr if isinstance(stderr, str) else stderr.decode("utf-8", errors="replace")

    if returncode != 0:
        return f"ERROR: tail failed (exit {returncode}):\n{stderr.strip()}"

    return stdout if stdout.strip() else "(file is empty)"
