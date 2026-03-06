"""Write file tool."""

import typing as t

from mcp.types import ToolAnnotations
from pydantic import Field

from linux_mcp_server.audit import log_tool_call
from linux_mcp_server.config import CONFIG
from linux_mcp_server.connection.ssh import execute_with_fallback
from linux_mcp_server.server import mcp
from linux_mcp_server.utils.types import Host


@mcp.tool(
    title="Write file",
    description=(
        "Write content to a file on a remote host via SSH. "
        "Requires LINUX_MCP_WRITE_ENABLED=true. "
        "If LINUX_MCP_ALLOWED_WRITE_PATHS is set, only files within whitelisted directories are permitted. "
        "WARNING: This tool overwrites the file if it already exists."
    ),
    tags={"files", "write"},
    annotations=ToolAnnotations(readOnlyHint=False),
)
@log_tool_call
async def write_file(
    path: t.Annotated[
        str,
        Field(
            description="Absolute path of the file to write",
            examples=["/tmp/test.txt", "/etc/myapp/config.conf"],
        ),
    ],
    content: t.Annotated[
        str,
        Field(
            description="Content to write to the file. Overwrites existing content.",
        ),
    ],
    host: Host = None,
) -> str:
    """Write content to a file on the target host.

    Security controls (via environment variables):
    - LINUX_MCP_WRITE_ENABLED=true                     required to enable this tool
    - LINUX_MCP_ALLOWED_WRITE_PATHS=/tmp,/etc/myapp    comma-separated allowlist of
      permitted base directories; if empty, all paths are allowed

    The file is written atomically: content is written to a temp file first,
    then moved to the target path to avoid partial writes.
    WARNING: Overwrites the file if it already exists.
    """
    if not CONFIG.write_enabled:
        return (
            "ERROR: write_file is disabled. "
            "Set LINUX_MCP_WRITE_ENABLED=true to enable it."
        )

    allowed = CONFIG.allowed_write_paths_list
    if allowed:
        if not any(path.startswith(allowed_path) for allowed_path in allowed):
            return (
                f"ERROR: '{path}' is not within the allowed write paths. "
                f"Allowed: {', '.join(allowed)}"
            )

    # Escape single quotes in content for safe shell embedding
    escaped = content.replace("'", "'\"'\"'")
    # Write atomically via temp file + mv
    tmp_path = path + ".mcp_tmp"
    command = f"printf '%s' '{escaped}' > {tmp_path} && mv {tmp_path} {path}"

    args = ("bash", "-c", command)
    returncode, stdout, stderr = await execute_with_fallback(args, host=host)

    stdout = stdout if isinstance(stdout, str) else stdout.decode("utf-8", errors="replace")
    stderr = stderr if isinstance(stderr, str) else stderr.decode("utf-8", errors="replace")

    if returncode != 0:
        return f"ERROR: write failed (exit {returncode}):\n{stderr.strip()}"

    return f"OK: File written successfully to {path}"
