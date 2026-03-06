"""Settings for linux-mcp-server"""

import sys

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from linux_mcp_server.utils.enum import StrEnum
from linux_mcp_server.utils.types import UpperCase


class Transport(StrEnum):
    stdio = "stdio"
    http = "http"
    streamable_http = "streamable-http"


class Config(BaseSettings):
    # The '_' is required in the env_prefix, otherwise, pydantic would
    # interpret the prefix as LINUX_MCPLOG_DIR, instead of LINUX_MCP_LOG_DIR
    model_config = SettingsConfigDict(
        env_prefix="LINUX_MCP_",
        env_ignore_empty=True,
        cli_hide_none_type=True,
        # Only ignore errors for incorrect/extra parameters when testing
        # https://github.com/pydantic/pydantic-settings/issues/391
        cli_ignore_unknown_args=sys.argv[0].endswith("pytest"),
        cli_implicit_flags=True,
        cli_kebab_case=True,
        cli_parse_args=True,
    )

    # FIXME: When the next version of pydantic-settings is released, change this
    # to CliToggleFlag in order to remove the '--no-' option.
    # https://github.com/pydantic/pydantic-settings/pull/717/changes
    version: bool = False

    user: str = ""
    transport: Transport = Transport.stdio
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"

    # Logging configuration
    log_dir: Path = Path.home() / ".local" / "share" / "linux-mcp-server" / "logs"
    log_level: UpperCase = "INFO"
    log_retention_days: int = 10

    # Log file access control
    allowed_log_paths: str | None = None

    # SSH configuration
    ssh_key_path: Path | None = None
    key_passphrase: SecretStr = SecretStr("")
    search_for_ssh_key: bool = False

    # SSH host key verification (security)
    verify_host_keys: bool = False  # NOTE(major): Switch to true later for production!
    known_hosts_path: Path | None = None  # Custom path to known_hosts file

    # Command execution timeout (applies to remote SSH commands)
    command_timeout: int = 30  # Timeout in seconds; prevents hung SSH operations

    # --- execute_command tool ---
    # LINUX_MCP_EXECUTE_ENABLED=true enables the execute_command tool (disabled by default)
    execute_enabled: bool = False
    # LINUX_MCP_ALLOWED_COMMANDS=curl,python3  comma-separated whitelist of allowed binaries
    # If empty, all commands are allowed (only relevant when execute_enabled=true)
    allowed_commands: str = ""

    # --- write_file tool ---
    # LINUX_MCP_WRITE_ENABLED=true enables the write_file tool (disabled by default)
    write_enabled: bool = False
    # LINUX_MCP_ALLOWED_WRITE_PATHS=/tmp,/etc/app  comma-separated allowlist of writable directories
    # If empty, all paths are allowed (only relevant when write_enabled=true)
    allowed_write_paths: str = ""

    # --- manage_service tool ---
    # LINUX_MCP_MANAGE_SERVICES_ENABLED=true enables the manage_service tool (disabled by default)
    manage_services_enabled: bool = False
    # LINUX_MCP_ALLOWED_SERVICES=nginx,postgresql  comma-separated whitelist of manageable services
    # If empty, all services are allowed (only relevant when manage_services_enabled=true)
    allowed_services: str = ""

    @property
    def allowed_commands_list(self) -> list[str]:
        """Return the allowed commands as a list, stripping whitespace."""
        if not self.allowed_commands:
            return []
        return [cmd.strip() for cmd in self.allowed_commands.split(",") if cmd.strip()]

    @property
    def allowed_write_paths_list(self) -> list[str]:
        """Return the allowed write paths as a list, stripping whitespace."""
        if not self.allowed_write_paths:
            return []
        return [p.strip() for p in self.allowed_write_paths.split(",") if p.strip()]

    @property
    def allowed_services_list(self) -> list[str]:
        """Return the allowed services as a list, stripping whitespace."""
        if not self.allowed_services:
            return []
        return [s.strip() for s in self.allowed_services.split(",") if s.strip()]

    @property
    def effective_known_hosts_path(self) -> Path:
        """Return the known_hosts path, using default ~/.ssh/known_hosts if not configured."""
        return self.known_hosts_path or Path.home() / ".ssh" / "known_hosts"

    @property
    def transport_kwargs(self):
        result: dict[str, str | int] = {"log_level": self.log_level}
        if self.transport in {Transport.http, Transport.streamable_http}:
            result["host"] = self.host
            result["port"] = self.port
            result["path"] = self.path

        return result


CONFIG = Config()
