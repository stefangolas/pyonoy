# Pyonoy

Python client for controlling the Byonoy Pyonoy plate reader via SiLA2.

## Installation

```bash
git clone https://github.com/stefangolas/pyonoy.git
cd pyonoy
pip install -e .
```

## Setup

Launch the Pyonoy app with SiLA2 enabled by adding CLI flags to the shortcut target:

```
"C:\Program Files (x86)\Byonoy\Pyonoy\app\pyonoy.exe" --sila --sila-insecure
```

Or use `--headless` to run without GUI.

## Example

```python
import time
from pathlib import Path
from pyonoy import PyonoyClient, ConnectionConfig, ExportFormat, SiLAConfig, launch_sila_server

SCRIPT_DIR = Path(__file__).parent.resolve()
PROTOCOL = (SCRIPT_DIR / "assay.byop").as_uri()
OUTPUT_DIR = SCRIPT_DIR / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

process = launch_sila_server(SiLAConfig(insecure=True, headless=True))
time.sleep(5)

client = PyonoyClient(ConnectionConfig(insecure=True))
client.connect()

with client.lock():
    client.load_workspace(PROTOCOL)
    client.prepare_for_readout()
    # insert plate
    client.perform_readout()
    # remove plate
    results = client.get_results(format=ExportFormat.CSV)
    (OUTPUT_DIR / "results.csv").write_bytes(results)

with client.lock():
    client.quit_application()

client.disconnect()
```

## License

MIT