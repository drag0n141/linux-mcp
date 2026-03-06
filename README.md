# linux-mcp

Linux MCP Server with SSH remote execution support.

Based on [rhel-lightspeed/linux-mcp-server](https://github.com/rhel-lightspeed/linux-mcp-server) (Apache 2.0).

## Additional features

- `execute_command` tool for arbitrary shell command execution via SSH
- Configurable via environment variables

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `LINUX_MCP_EXECUTE_ENABLED` | `false` | Enable the `execute_command` tool |
| `LINUX_MCP_ALLOWED_COMMANDS` | `` | Comma-separated whitelist of allowed binaries (empty = all allowed) |
| `LINUX_MCP_TRANSPORT` | `stdio` | Transport: `stdio`, `http`, `streamable-http` |
| `LINUX_MCP_SSH_KEY_PATH` | `` | Path to SSH private key |
| `LINUX_MCP_SEARCH_FOR_SSH_KEY` | `true` | Auto-discover SSH key |

## Container image

```
ghcr.io/drag0n141/linux-mcp:main
```
