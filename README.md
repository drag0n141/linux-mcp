# linux-mcp

> Linux MCP Server with SSH-based remote execution — built for AI agents and automation workflows.

Based on [rhel-lightspeed/linux-mcp-server](https://github.com/rhel-lightspeed/linux-mcp-server) (Apache 2.0),
extended with a generic `execute_command` tool for flexible shell command execution over SSH.

---

## What is this?

`linux-mcp` is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI agents
structured access to Linux systems via SSH. It exposes a set of read-only diagnostic tools (system info,
services, logs, network, storage, processes) plus an optional shell execution tool for running arbitrary
commands on remote hosts.

The server runs as a container and connects to remote hosts via SSH using key-based authentication.
It is designed to be deployed in Kubernetes and consumed by AI agents like
[AgentGateway](https://github.com/agentgateway/agentgateway) or similar MCP clients.

---

## Features

| Category        | Tools                                                                 |
|-----------------|-----------------------------------------------------------------------|
| System          | `get_system_information`, `get_cpu_information`, `get_memory_information`, `get_disk_usage`, `get_hardware_information` |
| Services        | `list_services`, `get_service_status`, `get_service_logs`            |
| Network         | `get_network_interfaces`, `get_network_connections`, `get_listening_ports` |
| Processes       | `list_processes`, `get_process_info`                                 |
| Storage / Files | `list_block_devices`, `list_directories`, `list_files`, `read_file`  |
| Logs            | `get_journal_logs`, `read_log_file`                                  |
| **Execution**   | **`execute_command`** *(opt-in, disabled by default)*                |

All tools accept an optional `host` parameter — when set, commands are executed on the remote system via SSH
instead of locally. This allows a single server instance to manage multiple remote hosts.

---

## execute_command

The `execute_command` tool is the main extension over the upstream project. It allows running arbitrary
shell commands on a remote host via SSH.

**It is disabled by default** and must be explicitly enabled via environment variable. Optionally, a
command whitelist can restrict which binaries are allowed.

```
# Enable the tool
LINUX_MCP_EXECUTE_ENABLED=true

# Optional: restrict to specific binaries (comma-separated)
LINUX_MCP_ALLOWED_COMMANDS=curl,python3,pip
```

### Security model

| `EXECUTE_ENABLED` | `ALLOWED_COMMANDS`   | Behavior                                      |
|-------------------|----------------------|-----------------------------------------------|
| `false` (default) | any                  | Tool returns an error, no command is executed |
| `true`            | *(empty)*            | All commands are allowed                      |
| `true`            | `curl,python3`       | Only whitelisted binaries are permitted       |

The whitelist checks the **basename** of the first token of the command, so `ALLOWED_COMMANDS=curl`
permits `curl -s http://...` but blocks `wget`, `bash -c "..."`, etc.

---

## Container Image

```
ghcr.io/drag0n141/linux-mcp:main
ghcr.io/drag0n141/linux-mcp:latest
```

Images are built automatically on every push to `main` via GitHub Actions for `linux/amd64` and `linux/arm64`.

---

## Configuration

All settings are controlled via environment variables with the `LINUX_MCP_` prefix.

| Variable                      | Default   | Description                                                        |
|-------------------------------|-----------|--------------------------------------------------------------------|
| `LINUX_MCP_TRANSPORT`         | `stdio`   | Transport: `stdio`, `http`, `streamable-http`                      |
| `LINUX_MCP_HOST`              | `127.0.0.1` | Bind address (for HTTP transport)                                |
| `LINUX_MCP_PORT`              | `8000`    | Port (for HTTP transport)                                          |
| `LINUX_MCP_SSH_KEY_PATH`      | *(auto)*  | Path to SSH private key (auto-discovered if not set)               |
| `LINUX_MCP_SEARCH_FOR_SSH_KEY`| `true`    | Auto-discover SSH key from `~/.ssh/`                               |
| `LINUX_MCP_USER`              | *(none)*  | SSH username (falls back to the container user if not set)         |
| `LINUX_MCP_VERIFY_HOST_KEYS`  | `false`   | Verify SSH host keys against `known_hosts`                         |
| `LINUX_MCP_COMMAND_TIMEOUT`   | `30`      | SSH command timeout in seconds                                     |
| `LINUX_MCP_ALLOWED_LOG_PATHS` | *(none)*  | Comma-separated allowlist of readable log files                    |
| `LINUX_MCP_EXECUTE_ENABLED`   | `false`   | Enable the `execute_command` tool                                  |
| `LINUX_MCP_ALLOWED_COMMANDS`  | *(empty)* | Comma-separated whitelist of allowed binaries for `execute_command` |

---

## Kubernetes Deployment (Helm / Flux)

Example `HelmRelease` values for deployment with HTTP transport:

```yaml
env:
  - name: LINUX_MCP_TRANSPORT
    value: "streamable-http"
  - name: LINUX_MCP_EXECUTE_ENABLED
    value: "true"
  - name: LINUX_MCP_ALLOWED_COMMANDS
    value: "curl,python3,pip"
  - name: LINUX_MCP_SEARCH_FOR_SSH_KEY
    value: "true"
```

The SSH private key should be mounted as a secret into the container, e.g. at `/var/lib/mcp/.ssh/id_ed25519`.

---

## SSH Authentication

The server uses key-based SSH authentication. Key discovery order:

1. `LINUX_MCP_SSH_KEY_PATH` environment variable (explicit path)
2. Auto-discovery from `~/.ssh/` — checks `id_ed25519`, `id_ecdsa`, `id_rsa` in order (if `LINUX_MCP_SEARCH_FOR_SSH_KEY=true`)

The SSH user on the target host needs read access for diagnostic tools. For `execute_command`,
ensure the user has the appropriate permissions for the commands you intend to run.

---

## License

Apache 2.0 — see [LICENSE](./LICENSE).
Based on work by [Red Hat / RHEL Lightspeed](https://github.com/rhel-lightspeed/linux-mcp-server).
