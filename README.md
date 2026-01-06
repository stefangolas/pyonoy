# Pyonoy

Python utilities for controlling the Byonoy Pyonoy plate reader via SiLA2.

## Prerequisites

### Windows Setup

The Pyonoy must be launched with command-line parameters to enable SiLA2. To create a shortcut:

1. Right-click the app shortcut in the Start Menu and select "Open file location"
2. Right-click the shortcut in the Explorer window and select "Properties"
3. In the Target field, add parameters after the closing quote, e.g.:
   ```
   "C:\Program Files (x86)\Byonoy\Pyonoy\app\pyonoy.exe" --sila --sila-insecure
   ```
4. Optionally, copy the shortcut first to have separate shortcuts for normal and SiLA2 modes

### macOS Setup

1. Open Finder and navigate to Applications
2. Right-click (or Control-click) the app, hold Option, and select "Copy as Pathname"
3. Open Script Editor (Applications/Utilities) and create a new document:
   ```applescript
   do shell script "open \"/Applications/Pyonoy.app\" --args --sila --sila-insecure"
   ```
4. Save as an Application in your Applications folder

### Network Configuration

By default, the SiLA2 server binds to `127.0.0.1` (localhost only). To allow network access:

- Set `--sila-ip 0.0.0.0` to bind to all interfaces
- On Windows, this may trigger a firewall prompt requiring administrator approval
- For service discovery, install [Bonjour Print Services for Windows](https://support.apple.com/kb/dl999) (macOS has this built-in)

### TLS/Security Options

| Mode | Flags | Use Case |
|------|-------|----------|
| Self-signed cert | *(default)* | Development - cert written to log or `--sila-out-cert` |
| Custom certs | `--sila-cert`, `--sila-key`, `--sila-ca-cert` | Production - provide PEM files |
| Insecure | `--sila-insecure` | Testing only - **not for production** |

## Installation


```bash
git clone https://github.com/stefangolas/pyonoy.git
cd byonoy-absorbance96
pip install -e .
```

## Quick Start

### Launch the SiLA2 Server

```bash
# Basic launch (insecure, for testing)
byonoy-launch --insecure

# Network-accessible
byonoy-launch --ip 0.0.0.0 --port 50052 --insecure

# Headless mode
byonoy-launch --headless --insecure
```

### Run an Assay via CLI

```bash
# Run assay and get results to stdout
byonoy-client run /path/to/protocol.byop --insecure

# Run assay and save results
byonoy-client run /path/to/protocol.byop -o results.csv --insecure

# Quit headless application
byonoy-client quit --insecure
```

### Python API

```python
from byonoy_absorbance96 import (
    PyonoyClient,
    ConnectionConfig,
    ExportFormat,
    SiLAConfig,
    launch_sila_server,
)

# Launch the server
config = SiLAConfig(port=50051, insecure=True)
process = launch_sila_server(config)

# Connect and run assay
client = PyonoyClient(ConnectionConfig(insecure=True))
client.connect()

with client.lock():
    client.load_workspace("file:///C:/Protocols/assay.byop")
    client.prepare_for_readout()
    # Insert plate
    client.perform_readout()
    # Remove plate
    results = client.get_results(format=ExportFormat.CSV)

client.disconnect()
```

### High-Level API

```python
from byonoy_absorbance96 import run_assay, ExportFormat

results = run_assay(
    protocol_path="C:/Protocols/assay.byop",
    output_format=ExportFormat.CSV,
    insecure=True,
)
```

## API Reference

### SiLAConfig

Configuration for launching the SiLA2 server:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | int | 50051 | Server port |
| `ip` | str | "127.0.0.1" | Bind IP address |
| `insecure` | bool | False | Disable TLS |
| `headless` | bool | False | Hide GUI window |
| `uuid` | str | None | Server UUID |
| `cert` | Path | None | TLS certificate file |
| `key` | Path | None | TLS private key file |
| `ca_cert` | Path | None | CA certificate file |
| `out_cert` | Path | None | Output path for self-signed cert |

### PyonoyClient Methods

| Method | Description | Prerequisites |
|--------|-------------|---------------|
| `connect()` | Connect to SiLA2 server | - |
| `disconnect()` | Disconnect from server | - |
| `acquire_lock()` | Get exclusive device access | Connected |
| `release_lock()` | Release device access | Lock held |
| `lock()` | Context manager for locking | Connected |
| `load_workspace(uri)` | Load protocol file | Lock held |
| `prepare_for_readout()` | Prepare reader | Protocol loaded |
| `perform_readout()` | Run measurement | Reader prepared |
| `export_results(path, format)` | Save results to server | Measurement done |
| `get_results(format)` | Get results as bytes | Measurement done |
| `quit_application()` | Shut down app | Lock held |

### ExportFormat

- `ExportFormat.CSV`
- `ExportFormat.XLSX`
- `ExportFormat.JSON`
- `ExportFormat.XML`

Note: PDF export is not available via SiLA2.

## URI Formats for Protocols

Local files use `file://` scheme:

```
Windows: file:///C:/Users/user/protocol.byop
macOS:   file:///Users/user/protocol.byop
Linux:   file:///home/user/protocol.byop
```

HTTP/HTTPS URLs are also supported:

```
https://example.com/protocols/assay.byop
```

## Notes

- All ApplicationController commands require holding an exclusive lock
- In headless mode, use `quit_application()` to shut down
- For network access, set `ip="0.0.0.0"` (may require firewall approval on Windows)
- Bonjour service discovery requires Bonjour Print Services on Windows

## CLI Parameters Reference

All parameters supported by the Pyonoy:

| Parameter | Description |
|-----------|-------------|
| `--sila` | **Required.** Enable SiLA2 server |
| `--sila-port <port>` | Server port (default: 50051) |
| `--sila-ip <ip>` | Bind IP (default: 127.0.0.1) |
| `--sila-uuid <uuid>` | Server UUID (auto-generated if omitted) |
| `--sila-insecure` | Disable TLS encryption |
| `--sila-cert <file>` | TLS certificate file (PEM) |
| `--sila-key <file>` | TLS private key file (PEM) |
| `--sila-ca-cert <file>` | CA certificate file (PEM) |
| `--sila-out-cert <file>` | Output path for self-signed certificate |
| `--headless` | Run without GUI (use `quit_application()` to exit) |

## License

MIT