"""Service management tool (start/stop/restart/reload/enable/disable)."""

import typing as t

from mcp.types import ToolAnnotations
from pydantic import Field

from linux_mcp_server.audit import log_tool_call
from linux_mcp_server.config import CONFIG
from linux_mcp_server.connection.ssh import execute_with_fallback
from linux_mcp_server.server import mcp
from linux_mcp_server.utils import StrEnum
from linux_mcp_server.utils.types import Host


class ServiceAction(StrEnum):
    """Allowed systemctl actions for manage_service."""
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    RELOAD = "reload"
    ENABLE = "enable"
    DISABLE = "disable"


@mcp.tool(
    title="Manage service",
    description=(
        "Start, stop, restart, reload, enable or disable a systemd service on a remote host via SSH. "
        "Requires LINUX_MCP_MANAGE_SERVICES_ENABLED=true. "
        "If LINUX_MCP_ALLOWED_SERVICES is set, only whitelisted services can be managed."
    ),
    tags={"services", "systemd"},
    annotations=ToolAnnotations(readOnlyHint=False),
)
@log_tool_call
async def manage_service(
    service_name: t.Annotated[
        str,
        Field(
            description="Name of the systemd service (with or without .service suffix)",
            examples=["nginx", "postgresql", "sshd.service"],
        ),
    ],
    action: t.Annotated[
        ServiceAction,
        Field(
            description="Action to perform: start, stop, restart, reload, enable, disable",
        ),
    ],
    host: Host = None,
) -> str:
    """Manage a systemd service on the target host.

    Security controls (via environment variables):
    - LINUX_MCP_MANAGE_SERVICES_ENABLED=true       required to enable this tool
    - LINUX_MCP_ALLOWED_SERVICES=nginx,postgresql  comma-separated whitelist of
      manageable services; if empty, all services are allowed

    Allowed actions: start, stop, restart, reload, enable, disable.
    """
    if not CONFIG.manage_services_enabled:
        return (
            "ERROR: manage_service is disabled. "
            "Set LINUX_MCP_MANAGE_SERVICES_ENABLED=true to enable it."
        )

    # Normalise service name: ensure .service suffix
    if "." not in service_name:
        service_name = f"{service_name}.service"

    # Strip suffix for whitelist comparison (allow both 'nginx' and 'nginx.service' in config)
    base_name = service_name.removesuffix(".service")

    allowed = CONFIG.allowed_services_list
    if allowed:
        normalised_allowed = [s.removesuffix(".service") for s in allowed]
        if base_name not in normalised_allowed:
            return (
                f"ERROR: '{base_name}' is not in the allowed services whitelist. "
                f"Allowed: {', '.join(normalised_allowed)}"
            )

    args = ("systemctl", action.value, service_name)
    returncode, stdout, stderr = await execute_with_fallback(args, host=host)

    stdout = stdout if isinstance(stdout, str) else stdout.decode("utf-8", errors="replace")
    stderr = stderr if isinstance(stderr, str) else stderr.decode("utf-8", errors="replace")

    if returncode != 0:
        return (
            f"ERROR: 'systemctl {action.value} {service_name}' failed (exit {returncode}):\n"
            f"{stderr.strip()}"
        )

    result = f"OK: systemctl {action.value} {service_name} executed successfully."
    if stdout.strip():
        result += f"\n{stdout.strip()}"
    return result
